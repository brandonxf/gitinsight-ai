"""Orquestación del análisis del lado de la API: crear job, encolar, consultar."""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import AnalysisJob
from app.repositories import analysis_repo, finding_repo
from app.schemas.analysis import AnalysisCreate
from app.services import repo_service


async def create_analysis(session: AsyncSession, payload: AnalysisCreate) -> AnalysisJob:
    """Registra repo + job (PENDING) y encola la tarea Celery. Commit incluido."""
    repo, _ref = await repo_service.register_repository(session, payload.url)
    job = await analysis_repo.create_job(
        session, repo.id, options=payload.options.model_dump()
    )
    await session.commit()

    # Import diferido para evitar ciclos (la tarea importa servicios/analizadores).
    from app.workers.tasks.analyze import analyze

    analyze.delay(str(job.id))
    return job


async def get_job(session: AsyncSession, job_id: uuid.UUID) -> AnalysisJob | None:
    return await analysis_repo.get_job(session, job_id)


async def get_job_with_repo(session: AsyncSession, job_id: uuid.UUID) -> AnalysisJob | None:
    return await analysis_repo.get_job_with_repo(session, job_id)


async def retry_analysis(session: AsyncSession, job: AnalysisJob) -> AnalysisJob:
    """Reencola un job fallido, limpiando hallazgos previos."""
    await finding_repo.delete_for_job(session, job.id)
    await analysis_repo.update_job(
        session,
        job,
        status="PENDING",
        phase=None,
        progress_pct=0,
        error_message=None,
        started_at=None,
        finished_at=None,
    )
    await session.commit()

    from app.workers.tasks.analyze import analyze

    analyze.delay(str(job.id))
    return job
