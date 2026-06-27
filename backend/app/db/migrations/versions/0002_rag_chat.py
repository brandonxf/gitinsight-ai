"""rag + chat: document_chunk (pgvector + HNSW), chat_session, chat_message

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-27
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from app.core.config import settings

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Extensión pgvector (idempotente). Necesaria para el tipo `vector`.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "document_chunk",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("language", sa.String(length=64), nullable=True),
        sa.Column("symbol", sa.String(length=255), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("line_start", sa.Integer(), nullable=True),
        sa.Column("line_end", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(settings.embedding_dim), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["analysis_job.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_document_chunk_job", "document_chunk", ["job_id"])
    # Índice HNSW para búsqueda aproximada por distancia coseno.
    op.execute(
        "CREATE INDEX ix_document_chunk_embedding_hnsw "
        "ON document_chunk USING hnsw (embedding vector_cosine_ops)"
    )

    op.create_table(
        "chat_session",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["analysis_job.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_chat_session_job", "chat_session", ["job_id"])

    op.create_table(
        "chat_message",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["chat_session.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_chat_message_session_created", "chat_message", ["session_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_table("chat_message")
    op.drop_index("ix_chat_session_job", table_name="chat_session")
    op.drop_table("chat_session")
    op.drop_index("ix_document_chunk_embedding_hnsw", table_name="document_chunk")
    op.drop_index("ix_document_chunk_job", table_name="document_chunk")
    op.drop_table("document_chunk")
