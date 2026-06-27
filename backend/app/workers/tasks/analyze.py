"""Tarea raíz del pipeline de análisis (deterministas + síntesis IA).

Orquesta: clonado seguro -> analizadores deterministas -> síntesis IA ->
persistencia, publicando progreso. Las fases comparten el repo en disco, por eso
se ejecutan en un único worker.
"""
from __future__ import annotations

import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.analyzers import (
    aggregate,
    applicable_analyzers,
    applicable_synthesis,
    build_context,
    prepare_synthesis_context,
)
from app.analyzers.base import LLM_TOKEN_KEY, AnalysisContext, Analyzer, AnalyzerResult
from app.core.config import settings
from app.core.logging import get_logger
from app.models.analysis import AnalysisJob
from app.repositories import analysis_repo, finding_repo
from app.services import progress_service, rag_service
from app.services.clone_service import (
    CloneError,
    CloneResult,
    cleanup,
    clone_repository,
    parse_github_url,
)
from app.workers.celery_app import celery
from app.workers.db import run_async

logger = get_logger(__name__)

# Executor dedicado para las fases de síntesis IA (llamadas LLM bloqueantes).
# Es propio (no el default de asyncio) para poder *abandonar* un hilo cuyo LLM se
# colgó: `asyncio.run` sólo espera al executor por defecto al cerrar, así que un
# hilo huérfano aquí no bloquea el cierre de la tarea Celery ni el slot del worker
# (terminará solo al saltar el timeout HTTP de lectura).
_SYNTH_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="synth")


@celery.task(
    name="app.workers.tasks.analyze.analyze",
    bind=True,
    acks_late=True,
    max_retries=2,
)
def analyze(self, job_id: str) -> dict:  # noqa: ANN001
    """Punto de entrada Celery. Delega en la corrutina async _run."""
    jid = uuid.UUID(job_id)
    return run_async(lambda sm: _run(sm, jid))


async def _set_progress(
    session: AsyncSession,
    job: AnalysisJob,
    *,
    phase: str | None,
    progress_pct: int,
    status: str = "RUNNING",
    **extra,
) -> None:
    await analysis_repo.update_job(
        session, job, phase=phase, progress_pct=progress_pct, status=status, **extra
    )
    await session.commit()
    progress_service.publish(job.id, phase, progress_pct, status)


#: Cadencia del heartbeat de progreso durante las fases de IA (segundos).
_HEARTBEAT_SECONDS = 1.0

#: Banda de progreso [inicio, fin) por fase de síntesis. Las fases que generan
#: más texto (explain, docs_gen) reciben una banda más ancha para que la barra
#: se mueva de forma perceptible mientras el modelo genera.
_SYNTHESIS_BANDS: dict[str, tuple[int, int]] = {
    "explain": (72, 82),
    "diagrams": (82, 86),
    "docs_gen": (86, 93),
}


def _synthesis_band(name: str, idx: int, total: int) -> tuple[int, int]:
    """Devuelve la banda [p0, p1) de progreso para una fase de síntesis."""
    band = _SYNTHESIS_BANDS.get(name)
    if band is not None:
        return band
    total = total or 1
    return 72 + int((idx / total) * 21), 72 + int(((idx + 1) / total) * 21)


async def _run_synthesis_step(
    session: AsyncSession,
    job: AnalysisJob,
    analyzer: Analyzer,
    context: AnalysisContext,
    p0: int,
    p1: int,
) -> AnalyzerResult | None:
    """Ejecuta un analizador de síntesis avanzando la barra mientras el LLM genera.

    El analizador corre en un hilo (la llamada al LLM es bloqueante) y, en
    paralelo, un heartbeat lee los tokens generados (`LLM_TOKEN_KEY`) para
    interpolar el progreso dentro de la banda [p0, p1]. Así la fase deja de
    aparentar estar congelada durante la generación token a token.

    Protección anti-cuelgue: si el modelo deja de emitir tokens durante más de
    `llm_stall_seconds` (stream atascado, recarga del modelo, bucle, etc.), la
    fase se cancela y se degrada con elegancia (devuelve None) en lugar de dejar
    el job congelado indefinidamente en, p. ej., "Redactando documentación".
    """
    # Dict propio por fase: si una fase se cancela, el hilo huérfano sigue
    # escribiendo en SU dict y no contamina el progreso de la fase siguiente.
    tok = {"produced": 0, "expected": 1}
    context.shared[LLM_TOKEN_KEY] = tok
    loop = asyncio.get_event_loop()
    task = loop.run_in_executor(_SYNTH_EXECUTOR, analyzer.run, context)

    last_produced = 0
    last_advance = loop.time()
    while not task.done():
        await asyncio.sleep(_HEARTBEAT_SECONDS)
        produced = tok.get("produced", 0)
        now = loop.time()
        if produced > last_produced:
            last_produced = produced
            last_advance = now
        elif now - last_advance > settings.llm_stall_seconds:
            task.cancel()
            logger.warning(
                "analyze.synthesis_stalled",
                extra={"a": analyzer.name, "stall_s": int(now - last_advance)},
            )
            return None
        frac = min(produced / max(tok.get("expected", 1), 1), 0.97)
        pct = p0 + int((p1 - p0) * frac)
        if pct > job.progress_pct:
            await _set_progress(session, job, phase=analyzer.name, progress_pct=pct)

    try:
        return task.result()
    except Exception:  # noqa: BLE001 — un analizador no debe tumbar la síntesis
        logger.exception("analyze.synthesis_failed", extra={"a": analyzer.name})
        return None


async def _run(sessionmaker: async_sessionmaker[AsyncSession], job_id: uuid.UUID) -> dict:
    async with sessionmaker() as session:
        job = await analysis_repo.get_job_with_repo(session, job_id)
        if job is None:
            logger.warning("analyze.job_missing", extra={"job_id": str(job_id)})
            return {"job_id": str(job_id), "status": "MISSING"}

        # Idempotencia: no re-ejecutar un job ya terminado o en curso.
        if job.status in {"RUNNING", "SUCCEEDED"}:
            logger.info("analyze.skip", extra={"job_id": str(job_id), "status": job.status})
            return {"job_id": str(job_id), "status": job.status}

        repo_url = job.repository.url
        clone_result: CloneResult | None = None

        try:
            await _set_progress(
                session, job, phase="clone", progress_pct=5,
                started_at=datetime.now(UTC), error_message=None,
            )

            ref = parse_github_url(repo_url)
            clone_result = await asyncio.to_thread(clone_repository, ref)

            job.repository.commit_sha = clone_result.commit_sha
            job.repository.default_branch = clone_result.default_branch
            await session.commit()

            context = await asyncio.to_thread(build_context, clone_result.path)

            # Fase determinista: analizadores uno a uno (progreso 10..70).
            analyzers = applicable_analyzers(context)
            total = len(analyzers) or 1
            findings = []
            data: dict = {}
            for idx, analyzer in enumerate(analyzers):
                pct = 10 + int((idx / total) * 60)
                await _set_progress(session, job, phase=analyzer.name, progress_pct=pct)
                try:
                    result = await asyncio.to_thread(analyzer.run, context)
                except Exception:  # noqa: BLE001
                    logger.exception("analyze.analyzer_failed", extra={"a": analyzer.name})
                    continue
                findings.extend(result.findings)
                data.update(result.data)

            data["aggregate"] = aggregate(findings, context)

            # Fase de ingestión RAG (Fase 3): indexa el repo para el chat
            # (chunk -> embeddings -> PgVector). Degrada con elegancia: si falla,
            # el job continúa y solo se queda sin chat (progreso ~70).
            if settings.rag_enabled:
                await _set_progress(session, job, phase="ingest_rag", progress_pct=70)
                try:
                    n_chunks = await rag_service.ingest(session, job_id, context)
                    await session.commit()
                    logger.info(
                        "analyze.rag_ingested",
                        extra={"job_id": str(job_id), "chunks": n_chunks},
                    )
                except Exception:  # noqa: BLE001 — la indexación no debe tumbar el job
                    await session.rollback()
                    logger.exception("analyze.rag_failed", extra={"job_id": str(job_id)})

            # Fase de síntesis IA: depende de los datos agregados (progreso 72..93).
            prepare_synthesis_context(context, data, findings)
            context.shared[LLM_TOKEN_KEY] = {"produced": 0, "expected": 1}
            synth = applicable_synthesis(context)
            for idx, analyzer in enumerate(synth):
                p0, p1 = _synthesis_band(analyzer.name, idx, len(synth))
                await _set_progress(session, job, phase=analyzer.name, progress_pct=p0)
                result = await _run_synthesis_step(session, job, analyzer, context, p0, p1)
                if result is None:
                    continue
                data.update(result.data)
                context.shared["synthesis"].update(result.data)

            await _set_progress(session, job, phase="persist", progress_pct=94)
            await _persist(session, job_id, data, findings, clone_result)

            await _set_progress(
                session, job, phase="done", progress_pct=100, status="SUCCEEDED",
                finished_at=datetime.now(UTC),
            )
            logger.info(
                "analyze.success",
                extra={"job_id": str(job_id), "findings": len(findings)},
            )
            return {"job_id": str(job_id), "status": "SUCCEEDED", "findings": len(findings)}

        except CloneError as exc:
            await _fail(session, job, str(exc))
            return {"job_id": str(job_id), "status": "FAILED", "error": str(exc)}
        except Exception as exc:  # noqa: BLE001
            logger.exception("analyze.error", extra={"job_id": str(job_id)})
            await _fail(session, job, f"Error interno: {exc}")
            return {"job_id": str(job_id), "status": "FAILED", "error": str(exc)}
        finally:
            if clone_result is not None:
                await asyncio.to_thread(cleanup, clone_result.path)


async def _persist(
    session: AsyncSession,
    job_id: uuid.UUID,
    data: dict,
    findings: list,
    clone_result: CloneResult,
) -> None:
    agg = data.get("aggregate", {})
    await finding_repo.delete_for_job(session, job_id)
    await finding_repo.bulk_insert(session, job_id, findings)
    await analysis_repo.upsert_result(
        session,
        job_id,
        primary_language=data.get("primary_language"),
        languages=data.get("languages", {}),
        frameworks=data.get("frameworks", []),
        structure=data.get("structure", {}),
        summary=data.get("summary"),
        purpose=data.get("purpose"),
        modules=data.get("modules", []),
        flow_description=data.get("flow_description"),
        diagrams=data.get("diagrams", {}),
        generated_docs=data.get("generated_docs", {}),
        risk_level=agg.get("risk_level"),
        quality_score=agg.get("quality_score"),
        metrics={
            "aggregate": agg,
            "quality": data.get("quality", {}),
            "complexity": data.get("complexity", {}),
            "security": data.get("security", {}),
            "secrets": data.get("secrets", {}),
            "package_managers": data.get("package_managers", []),
            "ai": data.get("ai", {}),
            "clone": {
                "commit_sha": clone_result.commit_sha,
                "size_bytes": clone_result.size_bytes,
                "file_count": clone_result.file_count,
            },
        },
    )
    await session.commit()


async def _fail(session: AsyncSession, job: AnalysisJob, message: str) -> None:
    await analysis_repo.update_job(
        session,
        job,
        status="FAILED",
        error_message=message[:2000],
        finished_at=datetime.now(UTC),
    )
    await session.commit()
    progress_service.publish(job.id, "error", job.progress_pct, "FAILED")
