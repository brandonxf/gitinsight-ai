"""Recorrido del repo clonado y construcción del AnalysisContext."""
from __future__ import annotations

from pathlib import Path

from app.analyzers.base import (
    EXTENSION_LANGUAGE,
    IGNORED_DIRS,
    IGNORED_FILENAMES,
    AnalysisContext,
    SourceFile,
)


def _is_ignored(rel_parts: tuple[str, ...]) -> bool:
    return any(part in IGNORED_DIRS for part in rel_parts)


def build_context(repo_path: Path) -> AnalysisContext:
    """Recorre el repo y construye el contexto con la lista de archivos fuente."""
    files: list[SourceFile] = []
    total_files = 0
    total_bytes = 0

    for path in repo_path.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(repo_path)
        if _is_ignored(rel.parts):
            continue

        total_files += 1
        try:
            size = path.stat().st_size
        except OSError:
            continue
        total_bytes += size

        if path.name in IGNORED_FILENAMES:
            continue

        language = EXTENSION_LANGUAGE.get(path.suffix.lower())
        files.append(
            SourceFile(
                abs_path=path,
                rel_path=rel.as_posix(),
                language=language,
                size_bytes=size,
            )
        )

    return AnalysisContext(
        repo_path=repo_path,
        files=files,
        total_files=total_files,
        total_bytes=total_bytes,
    )
