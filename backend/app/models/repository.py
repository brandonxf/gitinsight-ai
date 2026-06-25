from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.analysis import AnalysisJob


class Repository(UUIDMixin, TimestampMixin, Base):
    """Repositorio GitHub registrado. Se separa del job para permitir re-análisis."""

    __tablename__ = "repository"

    url: Mapped[str] = mapped_column(String(2048), unique=True, index=True, nullable=False)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)

    jobs: Mapped[list[AnalysisJob]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
