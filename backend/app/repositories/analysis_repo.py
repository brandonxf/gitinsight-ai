"""Acceso a datos para Repository, AnalysisJob y AnalysisResult."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.analysis import AnalysisJob, AnalysisResult
from app.models.repository import Repository
from app.services.clone_service import RepoRef


async def get_or_create_repository(session: AsyncSession, ref: RepoRef) -> Repository:
    existing = await session.scalar(select(Repository).where(Repository.url == ref.url))
    if existing:
        return existing
    repo = Repository(url=ref.url, owner=ref.owner, name=ref.name)
    session.add(repo)
    await session.flush()
    return repo


async def create_job(
    session: AsyncSession, repository_id: uuid.UUID, options: dict[str, Any]
) -> AnalysisJob:
    job = AnalysisJob(repository_id=repository_id, status="PENDING", options=options)
    session.add(job)
    await session.flush()
    return job


async def get_job(session: AsyncSession, job_id: uuid.UUID) -> AnalysisJob | None:
    return await session.get(AnalysisJob, job_id)


async def get_job_with_repo(
    session: AsyncSession, job_id: uuid.UUID
) -> AnalysisJob | None:
    return await session.scalar(
        select(AnalysisJob)
        .where(AnalysisJob.id == job_id)
        .options(selectinload(AnalysisJob.repository))
    )


async def update_job(session: AsyncSession, job: AnalysisJob, **fields: Any) -> AnalysisJob:
    for key, value in fields.items():
        setattr(job, key, value)
    await session.flush()
    return job


async def get_result(session: AsyncSession, job_id: uuid.UUID) -> AnalysisResult | None:
    return await session.scalar(
        select(AnalysisResult).where(AnalysisResult.job_id == job_id)
    )


async def upsert_result(
    session: AsyncSession, job_id: uuid.UUID, **data: Any
) -> AnalysisResult:
    result = await get_result(session, job_id)
    if result is None:
        result = AnalysisResult(job_id=job_id, **data)
        session.add(result)
    else:
        for key, value in data.items():
            setattr(result, key, value)
    await session.flush()
    return result
