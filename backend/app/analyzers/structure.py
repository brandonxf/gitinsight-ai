"""Análisis de estructura de carpetas y arquitectura inferida (heurística)."""
from __future__ import annotations

from pathlib import Path

from app.analyzers.base import (
    IGNORED_DIRS,
    AnalysisContext,
    Analyzer,
    AnalyzerResult,
)

_MAX_TREE_ENTRIES = 300


class StructureAnalyzer(Analyzer):
    name = "structure"

    def run(self, context: AnalysisContext) -> AnalyzerResult:
        root = context.repo_path
        top_dirs: list[str] = []
        top_files: list[str] = []
        for entry in sorted(root.iterdir()):
            if entry.name in IGNORED_DIRS or entry.name.startswith("."):
                continue
            if entry.is_dir():
                top_dirs.append(entry.name)
            elif entry.is_file():
                top_files.append(entry.name)

        loc = self._count_lines(context)
        tree = self._build_tree(root, max_entries=_MAX_TREE_ENTRIES)
        architecture = self._infer_architecture(root, top_dirs, context)

        structure = {
            "top_level_dirs": top_dirs,
            "top_level_files": top_files,
            "total_files": context.total_files,
            "total_source_files": len(context.files),
            "total_size_bytes": context.total_bytes,
            "lines_of_code": loc,
            "tree": tree,
            "architecture": architecture,
        }
        context.shared["lines_of_code"] = loc
        return AnalyzerResult(data={"structure": structure})

    def _count_lines(self, context: AnalysisContext) -> int:
        total = 0
        for f in context.files:
            if f.language is None or f.size_bytes > 1_000_000:
                continue
            try:
                with f.abs_path.open("r", encoding="utf-8", errors="ignore") as fh:
                    total += sum(1 for _ in fh)
            except OSError:
                continue
        return total

    def _build_tree(self, root: Path, *, max_entries: int) -> list[dict]:
        """Árbol limitado (2 niveles) para mostrar en la UI sin saturar."""
        nodes: list[dict] = []
        count = 0
        for entry in sorted(root.iterdir()):
            if entry.name in IGNORED_DIRS or entry.name.startswith("."):
                continue
            count += 1
            if count > max_entries:
                break
            node: dict = {"name": entry.name, "type": "dir" if entry.is_dir() else "file"}
            if entry.is_dir():
                children: list[dict] = []
                try:
                    for sub in sorted(entry.iterdir()):
                        if sub.name in IGNORED_DIRS or sub.name.startswith("."):
                            continue
                        children.append(
                            {"name": sub.name, "type": "dir" if sub.is_dir() else "file"}
                        )
                        if len(children) >= 50:
                            break
                except OSError:
                    pass
                node["children"] = children
            nodes.append(node)
        return nodes

    def _infer_architecture(
        self, root: Path, top_dirs: list[str], context: AnalysisContext
    ) -> dict:
        dir_set = {d.lower() for d in top_dirs}
        signals: list[str] = []

        has_backend = bool(dir_set & {"backend", "server", "api"})
        has_frontend = bool(dir_set & {"frontend", "client", "web", "ui"})
        if has_backend and has_frontend:
            signals.append("monorepo (frontend + backend)")
        if "src" in dir_set:
            signals.append("src layout")
        if dir_set & {"tests", "test", "spec", "__tests__"}:
            signals.append("con tests")
        if dir_set & {"packages", "apps"}:
            signals.append("workspace/monorepo")
        if (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists():
            signals.append("contenerizado (Docker)")
        if dir_set & {"controllers", "models", "views"}:
            signals.append("MVC")

        pattern = signals[0] if signals else "estructura plana / por defecto"
        return {"pattern": pattern, "signals": signals}
