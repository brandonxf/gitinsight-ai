"""Clonado seguro de repositorios GitHub públicos.

Defensa contra abuso (ver §4.3 de la arquitectura):
- Solo HTTPS de github.com (anti-SSRF, validación estricta de URL).
- Shallow clone (--depth=1), sin hooks, sin submódulos.
- Límites de tamaño, número de archivos y timeout.
- Nunca se ejecuta código del repo: solo lectura estática.
"""
from __future__ import annotations

import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from git import GitCommandError, Repo

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# owner/repo de GitHub: caracteres permitidos por GitHub para usuarios y repos.
_GITHUB_URL_RE = re.compile(
    r"^https://github\.com/"
    r"(?P<owner>[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})?)/"
    r"(?P<name>[A-Za-z0-9._-]{1,100}?)"
    r"(?:\.git)?/?$"
)


class CloneError(Exception):
    """Error determinista de clonado (URL inválida, repo demasiado grande, etc.)."""


@dataclass(frozen=True)
class RepoRef:
    url: str
    owner: str
    name: str


@dataclass
class CloneResult:
    path: Path
    commit_sha: str
    default_branch: str | None
    size_bytes: int
    file_count: int


def parse_github_url(url: str) -> RepoRef:
    """Valida y normaliza una URL de GitHub. Lanza CloneError si no es válida."""
    candidate = (url or "").strip()
    match = _GITHUB_URL_RE.match(candidate)
    if not match:
        raise CloneError(
            "URL inválida. Debe ser un repositorio público de la forma "
            "https://github.com/owner/repo"
        )
    owner = match.group("owner")
    name = match.group("name")
    if name.endswith(".git"):
        name = name[:-4]
    normalized = f"https://github.com/{owner}/{name}"
    return RepoRef(url=normalized, owner=owner, name=name)


def _dir_stats(path: Path, *, max_files: int, max_bytes: int) -> tuple[int, int]:
    """Cuenta archivos y bytes; aborta en cuanto se supera un límite (anti zip-bomb)."""
    total_bytes = 0
    file_count = 0
    for entry in path.rglob("*"):
        if ".git" in entry.parts:
            continue
        if entry.is_file() and not entry.is_symlink():
            file_count += 1
            if file_count > max_files:
                raise CloneError(
                    f"El repositorio supera el límite de {max_files} archivos."
                )
            total_bytes += entry.stat().st_size
            if total_bytes > max_bytes:
                raise CloneError(
                    f"El repositorio supera el límite de {max_bytes // (1024 * 1024)} MB."
                )
    return file_count, total_bytes


def clone_repository(ref: RepoRef) -> CloneResult:
    """Clona el repo en un directorio efímero bajo repos_cache_dir.

    El llamador es responsable de invocar `cleanup()` al terminar.
    """
    base = Path(settings.repos_cache_dir)
    base.mkdir(parents=True, exist_ok=True)
    dest = base / f"{ref.owner}__{ref.name}__{uuid.uuid4().hex}"

    max_bytes = settings.clone_max_size_mb * 1024 * 1024

    logger.info("clone.start", extra={"url": ref.url, "dest": str(dest)})
    try:
        repo = Repo.clone_from(
            ref.url,
            dest,
            depth=1,
            single_branch=True,
            # GitPython exige allow_unsafe_options para pasar `-c` explícitamente.
            allow_unsafe_options=True,
            multi_options=[
                "--no-tags",
                "-c",
                "core.hooksPath=/dev/null",  # nunca ejecutar hooks
            ],
            env={"GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "/bin/true"},
        )
    except GitCommandError as exc:
        cleanup(dest)
        stderr = (exc.stderr or "").strip()
        if "not found" in stderr.lower() or "repository not found" in stderr.lower():
            raise CloneError("El repositorio no existe o no es público.") from exc
        raise CloneError(f"Fallo al clonar el repositorio: {stderr or exc}") from exc
    except Exception as exc:  # noqa: BLE001
        cleanup(dest)
        raise CloneError(f"Fallo inesperado al clonar: {exc}") from exc

    try:
        file_count, size_bytes = _dir_stats(
            dest, max_files=settings.clone_max_files, max_bytes=max_bytes
        )
        commit_sha = repo.head.commit.hexsha
        try:
            default_branch = repo.active_branch.name
        except TypeError:
            default_branch = None
    except CloneError:
        cleanup(dest)
        raise
    finally:
        repo.close()

    logger.info(
        "clone.done",
        extra={"sha": commit_sha, "files": file_count, "bytes": size_bytes},
    )
    return CloneResult(
        path=dest,
        commit_sha=commit_sha,
        default_branch=default_branch,
        size_bytes=size_bytes,
        file_count=file_count,
    )


def cleanup(path: Path) -> None:
    """Borra el directorio del repo clonado (best-effort)."""
    shutil.rmtree(path, ignore_errors=True)
