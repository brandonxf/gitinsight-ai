from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import sqltypes

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.finding import Finding
    from app.models.repository import Repository


# Estados posibles de un job (texto plano, validado en la capa de aplicación).
JobStatus = sqltypes.String


class AnalysisJob(UUIDMixin, TimestampMixin, Base):
    """Una ejecución del pipeline de análisis sobre un repositorio."""

    __tablename__ = "analysis_job"
    __table_args__ = (
        Index("ix_analysis_job_repository_created", "repository_id", "created_at"),
        Index("ix_analysis_job_status", "status"),
    )

    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repository.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    phase: Mapped[str | None] = mapped_column(String(64), nullable=True)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    options: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    repository: Mapped[Repository] = relationship(back_populates="jobs")
    result: Mapped[AnalysisResult | None] = relationship(
        back_populates="job", cascade="all, delete-orphan", uselist=False
    )
    findings: Mapped[list[Finding]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class AnalysisResult(UUIDMixin, TimestampMixin, Base):
    """Agregados y síntesis de un job (1:1). jsonb para estructuras flexibles."""

    __tablename__ = "analysis_result"

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analysis_job.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Tecnología / estructura
    primary_language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    languages: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    frameworks: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    structure: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Síntesis (se rellena en la Fase 2 con IA)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    modules: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    flow_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Métricas / scoring
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Salidas IA (Fase 2)
    diagrams: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    generated_docs: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    job: Mapped[AnalysisJob] = relationship(back_populates="result")
