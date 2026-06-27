"""Chat con el repositorio (Fase 3): sesiones y mensajes.

Cada sesión se ancla a un `analysis_job` (cuyos `document_chunk` alimentan el RAG).
Los mensajes guardan, además del texto, las citas a archivos usadas como contexto.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    pass


class ChatSession(UUIDMixin, TimestampMixin, Base):
    """Una conversación sobre un análisis concreto."""

    __tablename__ = "chat_session"
    __table_args__ = (Index("ix_chat_session_job", "job_id"),)

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_job.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(UUIDMixin, TimestampMixin, Base):
    """Un mensaje de la conversación (user o assistant) con sus citas."""

    __tablename__ = "chat_message"
    __table_args__ = (Index("ix_chat_message_session_created", "session_id", "created_at"),)

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_session.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    #: Lista de citas usadas para responder: [{file_path, line_start, line_end, symbol}].
    citations: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    session: Mapped[ChatSession] = relationship(back_populates="messages")
