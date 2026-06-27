"""Acceso a datos para ChatSession y ChatMessage."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage, ChatSession


async def create_session(
    session: AsyncSession, job_id: uuid.UUID, title: str | None = None
) -> ChatSession:
    chat = ChatSession(job_id=job_id, title=title)
    session.add(chat)
    await session.flush()
    return chat


async def get_session_row(
    session: AsyncSession, session_id: uuid.UUID
) -> ChatSession | None:
    return await session.get(ChatSession, session_id)


async def list_messages(
    session: AsyncSession, session_id: uuid.UUID
) -> list[ChatMessage]:
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    return list((await session.scalars(stmt)).all())


async def add_message(
    session: AsyncSession,
    session_id: uuid.UUID,
    role: str,
    content: str,
    citations: list[dict[str, Any]] | None = None,
) -> ChatMessage:
    msg = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        citations=citations or [],
    )
    session.add(msg)
    await session.flush()
    return msg
