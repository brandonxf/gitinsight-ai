"""Construcción de la *evidencia* que ancla (grounding) la síntesis IA.

Reúne, a partir del repo clonado y de la salida de los analizadores deterministas,
un texto compacto y acotado: metadatos, estructura, hallazgos y extractos de los
archivos clave. Esto evita alucinaciones y mantiene el prompt dentro del presupuesto.
"""
from __future__ import annotations

from pathlib import Path

from app.analyzers.base import AnalysisContext, FindingData

# Presupuestos para no desbordar la ventana de contexto de modelos pequeños
# (p. ej. n_ctx=4096 por defecto en Ollama). Mantener el prompt compacto también
# acelera notablemente la inferencia en CPU.
_MAX_KEY_FILES = 6
_MAX_FILE_CHARS = 1_200
_MAX_FINDINGS_LISTED = 12
_MAX_SAMPLE_SOURCE = 3

# Archivos cuyo contenido es especialmente informativo sobre el propósito del repo.
_PRIORITY_BASENAMES = (
    "readme.md", "readme.rst", "readme.txt", "readme",
    "pyproject.toml", "package.json", "go.mod", "cargo.toml", "pom.xml",
    "composer.json", "gemfile", "requirements.txt", "docker-compose.yml",
)
# Puntos de entrada típicos (por nombre de archivo, en cualquier carpeta).
_ENTRYPOINT_BASENAMES = (
    "main.py", "app.py", "__main__.py", "manage.py", "cli.py", "server.py",
    "index.ts", "index.tsx", "index.js", "main.ts", "main.tsx", "main.go",
    "main.rs", "app.tsx", "app.ts",
)


def build_evidence(
    context: AnalysisContext, data: dict, findings: list[FindingData]
) -> str:
    """Devuelve un bloque de texto con toda la evidencia para el prompt IA."""
    sections: list[str] = [
        _overview_section(context, data),
        _structure_section(data),
        _findings_section(findings, data),
        _files_section(context),
    ]
    return "\n\n".join(s for s in sections if s)


def _overview_section(context: AnalysisContext, data: dict) -> str:
    languages = data.get("languages", {}) or {}
    lang_line = ", ".join(
        f"{lang} ({n})" for lang, n in sorted(languages.items(), key=lambda kv: -kv[1])
    ) or "—"
    frameworks = ", ".join(data.get("frameworks", []) or []) or "—"
    pms = ", ".join(data.get("package_managers", []) or []) or "—"
    structure = data.get("structure", {}) or {}
    arch = structure.get("architecture", {}) or {}
    signals = ", ".join(arch.get("signals", []) or []) or "—"

    lines = [
        "## Metadatos del repositorio",
        f"Nombre: {context.repo_path.name}",
        f"Lenguaje principal: {data.get('primary_language') or '—'}",
        f"Lenguajes: {lang_line}",
        f"Frameworks/tecnologías: {frameworks}",
        f"Gestores de paquetes: {pms}",
        f"Patrón de arquitectura inferido: {arch.get('pattern', '—')} (señales: {signals})",
        f"Líneas de código: {structure.get('lines_of_code', 0):,} · "
        f"Archivos fuente: {structure.get('total_source_files', 0)}",
    ]
    return "\n".join(lines)


def _structure_section(data: dict) -> str:
    structure = data.get("structure", {}) or {}
    top_dirs = structure.get("top_level_dirs", []) or []
    top_files = structure.get("top_level_files", []) or []
    tree = structure.get("tree", []) or []

    lines = ["## Estructura"]
    if top_dirs:
        lines.append("Directorios raíz: " + ", ".join(top_dirs))
    if top_files:
        lines.append("Archivos raíz: " + ", ".join(top_files[:20]))
    if tree:
        lines.append("Árbol (resumen):")
        for node in tree[:25]:
            lines.append(f"- {node.get('name')}/" if node.get("type") == "dir"
                         else f"- {node.get('name')}")
            for child in (node.get("children", []) or [])[:8]:
                mark = "/" if child.get("type") == "dir" else ""
                lines.append(f"    - {child.get('name')}{mark}")
    return "\n".join(lines)


def _findings_section(findings: list[FindingData], data: dict) -> str:
    agg = data.get("aggregate", {}) or {}
    by_sev = agg.get("by_severity", {}) or {}
    by_cat = agg.get("by_category", {}) or {}
    lines = [
        "## Hallazgos del análisis estático",
        f"Total: {agg.get('findings_total', len(findings))} · "
        f"Nivel de riesgo: {agg.get('risk_level', '—')} · "
        f"Quality score: {agg.get('quality_score', '—')}/100",
    ]
    if by_sev:
        lines.append("Por severidad: " + ", ".join(f"{k}={v}" for k, v in by_sev.items()))
    if by_cat:
        lines.append("Por categoría: " + ", ".join(f"{k}={v}" for k, v in by_cat.items()))

    severe = sorted(
        findings,
        key=lambda f: _SEVERITY_RANK.get(f.severity, 0),
        reverse=True,
    )[:_MAX_FINDINGS_LISTED]
    if severe:
        lines.append("Hallazgos más relevantes:")
        for f in severe:
            loc = f" ({f.file_path}:{f.line_start})" if f.file_path else ""
            rule = f" [{f.rule_id}]" if f.rule_id else ""
            lines.append(f"- [{f.severity}] {f.category}{rule}: {f.message}{loc}")
    return "\n".join(lines)


_SEVERITY_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def _files_section(context: AnalysisContext) -> str:
    selected = _select_key_files(context)
    if not selected:
        return ""
    blocks = ["## Extractos de archivos clave"]
    for sf_path, rel in selected:
        excerpt = _read_excerpt(sf_path)
        if not excerpt:
            continue
        blocks.append(f"### {rel}\n```\n{excerpt}\n```")
    return "\n\n".join(blocks)


def _select_key_files(context: AnalysisContext) -> list[tuple[Path, str]]:
    """Selecciona manifiestos, puntos de entrada y unas muestras de código fuente."""
    chosen: list[tuple[Path, str]] = []
    seen: set[str] = set()

    def add(rel: str, path: Path) -> None:
        if rel not in seen:
            seen.add(rel)
            chosen.append((path, rel))

    # 1) Archivos prioritarios (README, manifiestos), preferentemente en la raíz.
    for f in context.files:
        base = Path(f.rel_path).name.lower()
        if base in _PRIORITY_BASENAMES and f.rel_path.count("/") <= 1:
            add(f.rel_path, f.abs_path)
    # 2) Puntos de entrada.
    for f in context.files:
        if Path(f.rel_path).name.lower() in _ENTRYPOINT_BASENAMES:
            add(f.rel_path, f.abs_path)
    # 3) Muestras de código del lenguaje principal (las de menor profundidad).
    primary = context.shared.get("primary_language")
    samples = [
        f for f in context.files
        if f.language == primary and 0 < f.size_bytes <= 40_000 and f.rel_path not in seen
    ]
    samples.sort(key=lambda f: (f.rel_path.count("/"), -f.size_bytes))
    for f in samples[:_MAX_SAMPLE_SOURCE]:
        add(f.rel_path, f.abs_path)

    # README/manifiestos quedan primero; limita el total para acotar el prompt.
    return chosen[:_MAX_KEY_FILES]


def _read_excerpt(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    if len(text) > _MAX_FILE_CHARS:
        text = text[:_MAX_FILE_CHARS] + "\n[... recortado ...]"
    return text.strip()
