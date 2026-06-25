"""Validación de URL y registro de repositorios."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import Repository
from app.repositories import analysis_repo
from app.services.clone_service import RepoRef, parse_github_url


async def register_repository(session: AsyncSession, url: str) -> tuple[Repository, RepoRef]:
    """Valida la URL de GitHub y devuelve (Repository, RepoRef).

    Lanza CloneError si la URL no es válida.
    """
    ref = parse_github_url(url)
    repo = await analysis_repo.get_or_create_repository(session, ref)
    return repo, ref
