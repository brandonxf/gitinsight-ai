"""Tarea raíz del pipeline de análisis (deterministas + síntesis IA).

Orquesta: clonado seguro -> analizadores deterministas -> síntesis IA ->
persistencia, publicando progreso. Las fases comparten el repo en disco, por eso
se ejecutan en un único worker.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.analyzers import (
    aggregate,
    applicable_analyzers,
    applicable_synthesis,
    build_context,
    prepare_synthesis_context,
)
from app.core.logging import get_logger
from app.models.analysis import AnalysisJob
from app.repositories import analysis_repo, finding_repo
from app.services import progress_service
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

            # Fase de síntesis IA: depende de los datos agregados (progreso 72..90).
            prepare_synthesis_context(context, data, findings)
            synth = applicable_synthesis(context)
            stotal = len(synth) or 1
            for idx, analyzer in enumerate(synth):
                pct = 72 + int((idx / stotal) * 18)
                await _set_progress(session, job, phase=analyzer.name, progress_pct=pct)
                try:
                    result = await asyncio.to_thread(analyzer.run, context)
                except Exception:  # noqa: BLE001
                    logger.exception("analyze.synthesis_failed", extra={"a": analyzer.name})
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
