"""Acceso a datos para DocumentChunk (ingestión y búsqueda vectorial)."""
from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzers.ingest_rag import ChunkData
from app.models.chunk import DocumentChunk


async def delete_for_job(session: AsyncSession, job_id: uuid.UUID) -> None:
    await session.execute(delete(DocumentChunk).where(DocumentChunk.job_id == job_id))


async def bulk_insert(
    session: AsyncSession,
    job_id: uuid.UUID,
    chunks: Sequence[ChunkData],
    embeddings: Sequence[Sequence[float]],
) -> int:
    rows = [
        DocumentChunk(
            job_id=job_id,
            file_path=c.file_path,
            language=c.language,
            symbol=c.symbol,
            chunk_index=c.chunk_index,
            line_start=c.line_start,
            line_end=c.line_end,
            content=c.content,
            embedding=list(emb),
        )
        for c, emb in zip(chunks, embeddings, strict=True)
    ]
    session.add_all(rows)
    await session.flush()
    return len(rows)


async def count_for_job(session: AsyncSession, job_id: uuid.UUID) -> int:
    return await session.scalar(
        select(func.count()).select_from(DocumentChunk).where(DocumentChunk.job_id == job_id)
    ) or 0


async def search(
    session: AsyncSession,
    job_id: uuid.UUID,
    query_vector: Sequence[float],
    k: int,
) -> list[DocumentChunk]:
    """Top-k fragmentos del job por menor distancia coseno al vector de consulta."""
    stmt = (
        select(DocumentChunk)
        .where(DocumentChunk.job_id == job_id)
        .order_by(DocumentChunk.embedding.cosine_distance(list(query_vector)))
        .limit(k)
    )
    return list((await session.scalars(stmt)).all())
