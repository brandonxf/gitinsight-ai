"""Endpoints REST del análisis de repositorios (Fase 1)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories import analysis_repo, finding_repo
from app.schemas.analysis import (
    AnalysisCreate,
    AnalysisCreateResponse,
    AnalysisJobOut,
    AnalysisLinks,
    AnalysisResultOut,
    RepositoryOut,
)
from app.schemas.finding import FindingOut, FindingPage
from app.services import analysis_service
from app.services.clone_service import CloneError

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=AnalysisCreateResponse)
async def create_analysis(
    payload: AnalysisCreate, session: AsyncSession = Depends(get_session)
) -> AnalysisCreateResponse:
    """Inicia un análisis: registra el repo, crea el job y lo encola (202)."""
    try:
        job = await analysis_service.create_analysis(session, payload)
    except CloneError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return AnalysisCreateResponse(
        job_id=job.id,
        status=job.status,
        links=AnalysisLinks(
            self=f"/api/v1/analyses/{job.id}",
            result=f"/api/v1/analyses/{job.id}/result",
        ),
    )


@router.get("/{job_id}", response_model=AnalysisJobOut)
async def get_analysis(
    job_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> AnalysisJobOut:
    """Estado del job (status, phase, progress) para polling."""
    job = await analysis_service.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Análisis no encontrado.")
    return AnalysisJobOut.model_validate(job)


@router.get("/{job_id}/result", response_model=AnalysisResultOut)
async def get_analysis_result(
    job_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> AnalysisResultOut:
    """Resultado agregado. 409 si el análisis aún no ha terminado."""
    job = await analysis_service.get_job_with_repo(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Análisis no encontrado.")
    if job.status != "SUCCEEDED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El análisis no está listo (estado: {job.status}).",
        )
    result = await analysis_repo.get_result(session, job_id)
    if result is None:
        raise HTTPException(status_code=409, detail="Resultado no disponible todavía.")

    return AnalysisResultOut(
        job=AnalysisJobOut.model_validate(job),
        repository=RepositoryOut.model_validate(job.repository),
        primary_language=result.primary_language,
        languages=result.languages,
        frameworks=result.frameworks,
        structure=result.structure,
        summary=result.summary,
        purpose=result.purpose,
        modules=result.modules,
        flow_description=result.flow_description,
        risk_level=result.risk_level,
        quality_score=result.quality_score,
        metrics=result.metrics,
        diagrams=result.diagrams,
        generated_docs=result.generated_docs,
    )


@router.get("/{job_id}/findings", response_model=FindingPage)
async def get_findings(
    job_id: uuid.UUID,
    category: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    file: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> FindingPage:
    """Hallazgos del job con filtros y paginación."""
    job = await analysis_service.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Análisis no encontrado.")
    items, total = await finding_repo.list_findings(
        session, job_id, category=category, severity=severity, file=file,
        limit=limit, offset=offset,
    )
    return FindingPage(
        items=[FindingOut.model_validate(f) for f in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/{job_id}/retry", status_code=status.HTTP_202_ACCEPTED, response_model=AnalysisJobOut)
async def retry_analysis(
    job_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> AnalysisJobOut:
    """Reencola un job que terminó en FAILED."""
    job = await analysis_service.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Análisis no encontrado.")
    if job.status not in {"FAILED", "SUCCEEDED"}:
        raise HTTPException(status_code=409, detail="El análisis no puede reintentarse ahora.")
    job = await analysis_service.retry_analysis(session, job)
    return AnalysisJobOut.model_validate(job)
