"""Interfaz común de analizadores (patrón plugin) y contexto compartido.

Cada analizador implementa `Analyzer.run(context) -> AnalyzerResult`. El pipeline
los orquesta y agrega resultados sin conocer su lógica interna.
"""
from __future__ import annotations

import shutil
import sys
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def resolve_tool(name: str) -> str | None:
    """Localiza un ejecutable (ruff, bandit) en el PATH o junto a sys.executable.

    Robusto frente a venvs cuyo bin/ no está en el PATH del proceso worker.
    """
    found = shutil.which(name)
    if found:
        return found
    candidate = Path(sys.executable).parent / name
    return str(candidate) if candidate.exists() else None


def relativize(filename: str | None, repo_path: Path) -> str | None:
    """Normaliza la ruta de un hallazgo a una ruta POSIX relativa al repo.

    Las herramientas (ruff, bandit) corren con cwd=repo_path y pueden devolver
    rutas absolutas o relativas (a veces con prefijo './').
    """
    if not filename:
        return None
    path = Path(filename)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(repo_path.resolve()).as_posix()
        except ValueError:
            return path.as_posix()
    return path.as_posix()  # pathlib normaliza './app.py' -> 'app.py'

# Extensiones por lenguaje (subconjunto pragmático para el MVP).
EXTENSION_LANGUAGE: dict[str, str] = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".hpp": "C++",
    ".swift": "Swift",
    ".scala": "Scala",
    ".sh": "Shell",
    ".sql": "SQL",
    ".vue": "Vue",
    ".svelte": "Svelte",
}

# Directorios que nunca se analizan (ruido, dependencias, artefactos).
IGNORED_DIRS: frozenset[str] = frozenset({
    ".git", "node_modules", "dist", "build", "out", "target", "vendor",
    "__pycache__", ".venv", "venv", "env", ".env", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox", ".idea", ".vscode", "coverage", ".next", ".nuxt",
    ".svelte-kit", "site-packages", ".cache", "bower_components", "Pods",
})

# Archivos que se ignoran para selección de código fuente (lockfiles, binarios comunes).
IGNORED_FILENAMES: frozenset[str] = frozenset({
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
    "Cargo.lock", "composer.lock", "Gemfile.lock", "go.sum",
})

MAX_TEXT_FILE_BYTES = 1_000_000  # 1 MB: por encima se omite para análisis de texto


@dataclass
class FindingData:
    """Hallazgo producido por un analizador (se mapea 1:1 a la tabla `finding`)."""

    category: str
    severity: str
    message: str
    rule_id: str | None = None
    file_path: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    suggestion: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyzerResult:
    """Salida de un analizador: hallazgos + datos agregados para AnalysisResult."""

    findings: list[FindingData] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceFile:
    """Un archivo de código fuente relevante dentro del repo."""

    abs_path: Path
    rel_path: str
    language: str | None
    size_bytes: int


@dataclass
class AnalysisContext:
    """Estado compartido del análisis de un repositorio clonado."""

    repo_path: Path
    files: list[SourceFile] = field(default_factory=list)
    total_files: int = 0
    total_bytes: int = 0
    shared: dict[str, Any] = field(default_factory=dict)

    def files_for_language(self, language: str) -> list[SourceFile]:
        return [f for f in self.files if f.language == language]


#: Clave en `context.shared` donde se publica el progreso de generación del LLM.
#: El worker la lee para avanzar la barra durante las fases de IA (que de otro
#: modo se quedarían congeladas mientras el modelo genera token a token).
LLM_TOKEN_KEY = "_llm_tok"


def llm_token_sink(context: AnalysisContext, expected: int) -> Callable[[str], None]:
    """Crea un callback `on_chunk` para `LLMProvider.chat` que reporta progreso.

    Cada fragmento recibido del stream incrementa el contador de tokens en
    `context.shared[LLM_TOKEN_KEY]`. Si no hay contador (uso standalone/tests),
    el callback es inofensivo. El progreso nunca debe romper la generación.
    """
    tok = context.shared.get(LLM_TOKEN_KEY)
    if tok is not None:
        tok["expected"] = max(int(expected), 1)
        tok["produced"] = 0

    def _on_chunk(piece: str) -> None:
        if tok is not None and piece:
            tok["produced"] = tok.get("produced", 0) + 1

    return _on_chunk


class Analyzer(ABC):
    """Interfaz base de todos los analizadores."""

    #: Nombre legible usado como `phase` en el progreso del job.
    name: str = "analyzer"

    def applies(self, context: AnalysisContext) -> bool:
        """Si devuelve False, el pipeline omite este analizador (ahorra trabajo)."""
        return True

    @abstractmethod
    def run(self, context: AnalysisContext) -> AnalyzerResult:
        """Ejecuta el análisis. Debe ser determinista y no ejecutar código del repo."""
        raise NotImplementedError
