"""Acceso a datos para Finding."""
from __future__ import annotations

import uuid

from sqlalchemy import case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzers.base import FindingData
from app.models.finding import Finding

# Rango de severidad para ordenar (críticos primero).
_SEVERITY_RANK = case(
    {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4},
    value=Finding.severity,
    else_=5,
)


async def bulk_insert(
    session: AsyncSession, job_id: uuid.UUID, findings: list[FindingData]
) -> int:
    rows = [
        Finding(
            job_id=job_id,
            category=f.category,
            severity=f.severity,
            rule_id=f.rule_id,
            file_path=f.file_path,
            line_start=f.line_start,
            line_end=f.line_end,
            message=f.message,
            suggestion=f.suggestion,
            finding_metadata=f.metadata or {},
        )
        for f in findings
    ]
    session.add_all(rows)
    await session.flush()
    return len(rows)


async def list_findings(
    session: AsyncSession,
    job_id: uuid.UUID,
    *,
    category: str | None = None,
    severity: str | None = None,
    file: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[Finding], int]:
    conditions = [Finding.job_id == job_id]
    if category:
        conditions.append(Finding.category == category)
    if severity:
        conditions.append(Finding.severity == severity)
    if file:
        conditions.append(Finding.file_path.ilike(f"%{file}%"))

    total = await session.scalar(
        select(func.count()).select_from(Finding).where(*conditions)
    )
    stmt = (
        select(Finding)
        .where(*conditions)
        .order_by(_SEVERITY_RANK, Finding.file_path, Finding.line_start)
        .limit(limit)
        .offset(offset)
    )
    items = list(await session.scalars(stmt))
    return items, int(total or 0)


async def delete_for_job(session: AsyncSession, job_id: uuid.UUID) -> None:
    await session.execute(delete(Finding).where(Finding.job_id == job_id))
