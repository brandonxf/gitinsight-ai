"""Servicio RAG (Fase 3): ingestión, retrieval y respuesta con citaciones.

Desacoplado en dos mitades:
- **Ingestión** (worker): chunking -> embeddings -> persistencia en PgVector.
- **Retrieval + respuesta** (API de chat): embeber la pregunta, recuperar los
  fragmentos más similares y construir un prompt *grounded* para el LLM, que debe
  responder citando los archivos. Si no hay contexto suficiente, lo dice.
"""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzers.base import AnalysisContext
from app.analyzers.ingest_rag import build_chunks
from app.core.config import settings
from app.core.logging import get_logger
from app.models.chunk import DocumentChunk
from app.repositories import chunk_repo
from app.services.embeddings import embed_documents, embed_query
from app.services.llm.base import ChatMessage, LLMError, system, user
from app.services.llm.factory import get_llm

logger = get_logger(__name__)

# Recorte por fragmento al construir el prompt (evita reventar la ventana).
_MAX_SNIPPET_CHARS = 1600

_SYSTEM_PROMPT = (
    "Eres un asistente experto que responde preguntas sobre un repositorio de código. "
    "Respondes SIEMPRE en español, de forma concreta y técnica. "
    "Usa EXCLUSIVAMENTE el contexto de código proporcionado; no inventes archivos, "
    "funciones ni comportamientos que no aparezcan. Cita los archivos relevantes con "
    "su ruta (p. ej. `app/main.py`). Si el contexto no es suficiente para responder, "
    "dilo claramente y sugiere dónde podría estar la respuesta."
)


@dataclass
class Citation:
    file_path: str
    line_start: int | None
    line_end: int | None
    symbol: str | None

    def as_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "symbol": self.symbol,
        }


@dataclass
class RagAnswer:
    content: str
    citations: list[Citation]


async def ingest(session: AsyncSession, job_id: uuid.UUID, context: AnalysisContext) -> int:
    """Indexa el repo: chunk -> embeddings -> persistencia. Devuelve nº de chunks.

    Pensado para llamarse desde el worker. No lanza: si falla, el job degrada con
    elegancia (continúa sin chat). El llamador hace commit.
    """
    if not settings.rag_enabled:
        return 0
    chunks = build_chunks(
        context,
        max_files=settings.rag_max_files,
        max_chunks=settings.rag_max_chunks,
        max_chars=settings.rag_chunk_max_chars,
    )
    if not chunks:
        return 0

    embeddings = await asyncio.to_thread(embed_documents, [c.content for c in chunks])
    await chunk_repo.delete_for_job(session, job_id)
    inserted = await chunk_repo.bulk_insert(session, job_id, chunks, embeddings)
    logger.info("rag.ingested", extra={"job_id": str(job_id), "chunks": inserted})
    return inserted


async def retrieve(
    session: AsyncSession, job_id: uuid.UUID, query: str, k: int | None = None
) -> list[DocumentChunk]:
    """Recupera los fragmentos más similares a la consulta."""
    query_vector = await asyncio.to_thread(embed_query, query)
    return await chunk_repo.search(session, job_id, query_vector, k or settings.rag_top_k)


def _build_context_block(chunks: list[DocumentChunk]) -> str:
    parts: list[str] = []
    for i, c in enumerate(chunks, start=1):
        loc = c.file_path
        if c.line_start:
            loc += f":{c.line_start}-{c.line_end or c.line_start}"
        snippet = c.content[:_MAX_SNIPPET_CHARS]
        parts.append(f"[Fuente {i}] {loc}\n```\n{snippet}\n```")
    return "\n\n".join(parts)


async def answer(session: AsyncSession, job_id: uuid.UUID, question: str) -> RagAnswer:
    """Recupera contexto y genera una respuesta *grounded* con citaciones."""
    chunks = await retrieve(session, job_id, question)
    citations = [
        Citation(c.file_path, c.line_start, c.line_end, c.symbol) for c in chunks
    ]

    if not chunks:
        return RagAnswer(
            content=(
                "No encuentro contexto indexado para este repositorio, así que no "
                "puedo responder con fundamento. Puede que el análisis se ejecutara "
                "sin la fase de indexación (RAG)."
            ),
            citations=[],
        )

    context_block = _build_context_block(chunks)
    messages: list[ChatMessage] = [
        system(_SYSTEM_PROMPT),
        user(
            f"Contexto de código del repositorio:\n\n{context_block}\n\n"
            f"Pregunta: {question}"
        ),
    ]

    llm = get_llm()
    try:
        content = await asyncio.to_thread(
            llm.chat, messages, temperature=0.1, max_tokens=settings.chat_max_tokens
        )
    except LLMError as exc:
        logger.warning("rag.llm_failed", extra={"job_id": str(job_id), "error": str(exc)})
        content = (
            "No pude generar la respuesta porque el modelo de lenguaje no está "
            "disponible ahora mismo. Inténtalo de nuevo en unos segundos."
        )

    return RagAnswer(content=content.strip(), citations=citations)
