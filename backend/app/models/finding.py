from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.analysis import AnalysisJob


class Finding(UUIDMixin, TimestampMixin, Base):
    """Hallazgo unificado: calidad, seguridad, secretos, complejidad, etc."""

    __tablename__ = "finding"
    __table_args__ = (
        Index("ix_finding_job_category_severity", "job_id", "category", "severity"),
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analysis_job.id", ondelete="CASCADE"), nullable=False
    )
    # category ∈ {bug, code_smell, duplication, complexity, secret, vuln, insecure_config}
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    # severity ∈ {info, low, medium, high, critical}
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    rule_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    line_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    finding_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )

    job: Mapped[AnalysisJob] = relationship(back_populates="findings")
