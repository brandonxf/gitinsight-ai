"""Endpoints de chat con el repositorio (Fase 3, RAG)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories import analysis_repo, chat_repo
from app.schemas.chat import (
    ChatHistoryOut,
    ChatMessageCreate,
    ChatMessageOut,
    ChatSessionCreateResponse,
)
from app.services import rag_service

router = APIRouter(tags=["chat"])


@router.post(
    "/analyses/{job_id}/chat/sessions",
    status_code=status.HTTP_201_CREATED,
    response_model=ChatSessionCreateResponse,
)
async def create_chat_session(
    job_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> ChatSessionCreateResponse:
    """Crea una sesión de chat anclada a un análisis terminado."""
    job = await analysis_repo.get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Análisis no encontrado.")
    if job.status != "SUCCEEDED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El análisis no está listo (estado: {job.status}).",
        )
    chat = await chat_repo.create_session(session, job_id)
    await session.commit()
    return ChatSessionCreateResponse(session_id=chat.id, job_id=job_id)


@router.post(
    "/chat/sessions/{session_id}/messages",
    response_model=ChatMessageOut,
)
async def post_message(
    session_id: uuid.UUID,
    payload: ChatMessageCreate,
    session: AsyncSession = Depends(get_session),
) -> ChatMessageOut:
    """Envía una pregunta y recibe la respuesta (RAG) con citaciones a archivos."""
    chat = await chat_repo.get_session_row(session, session_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Sesión de chat no encontrada.")

    await chat_repo.add_message(session, session_id, "user", payload.message)

    result = await rag_service.answer(session, chat.job_id, payload.message)
    assistant = await chat_repo.add_message(
        session,
        session_id,
        "assistant",
        result.content,
        citations=[c.as_dict() for c in result.citations],
    )
    await session.commit()
    return ChatMessageOut.model_validate(assistant)


@router.get(
    "/chat/sessions/{session_id}/messages",
    response_model=ChatHistoryOut,
)
async def get_messages(
    session_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> ChatHistoryOut:
    """Historial de la conversación."""
    chat = await chat_repo.get_session_row(session, session_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Sesión de chat no encontrada.")
    messages = await chat_repo.list_messages(session, session_id)
    return ChatHistoryOut(
        session_id=session_id,
        messages=[ChatMessageOut.model_validate(m) for m in messages],
    )
