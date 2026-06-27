"""Generación de diagramas Mermaid de arquitectura.

Intenta un diagrama generado por IA (anclado en módulos/estructura) y, si el LLM
no está disponible o devuelve algo inválido, recurre a un diagrama determinista
construido a partir de los directorios de nivel superior.
"""
from __future__ import annotations

import re

from app.analyzers.base import (
    AnalysisContext,
    Analyzer,
    AnalyzerResult,
    llm_token_sink,
)
from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm import LLMError, get_llm, system, user

logger = get_logger(__name__)

# Tipos de diagrama Mermaid que aceptamos como salida válida del LLM.
_VALID_HEADERS = ("flowchart", "graph", "sequencediagram", "classdiagram", "erdiagram")
_FENCE = re.compile(r"```(?:mermaid)?\s*(.*?)\s*```", re.DOTALL)

_SYSTEM = (
    "Eres un arquitecto de software. Generas diagramas Mermaid válidos y legibles "
    "que representan la arquitectura real del repositorio según la evidencia. "
    "Respondes SOLO con el código Mermaid, sin explicaciones ni markdown."
)

_PROMPT = """\
Genera UN diagrama Mermaid de tipo `flowchart TD` que represente la arquitectura de
alto nivel del proyecto: componentes/módulos principales y cómo se relacionan
(flujo de datos o dependencias). Usa los módulos y la estructura de la evidencia.

Requisitos:
- Empieza con `flowchart TD`.
- Entre 4 y 9 nodos. Etiquetas cortas en español.
- Solo identificadores alfanuméricos para los nodos (sin espacios ni acentos).
- Devuelve ÚNICAMENTE el código Mermaid, nada más.

# Módulos detectados
{modules}

# Estructura
{structure}
"""


class DiagramsAnalyzer(Analyzer):
    name = "diagrams"

    # Siempre aplica: si el LLM falla, hay un fallback determinista.
    def run(self, context: AnalysisContext) -> AnalyzerResult:
        data = context.shared.get("det_data", {})
        synthesis = context.shared.get("synthesis", {})
        structure = data.get("structure", {}) or {}

        mermaid = ""
        source = "fallback"
        if settings.llm_enabled:
            mermaid = self._generate_with_llm(context, synthesis, structure)
            if mermaid:
                source = "ai"

        if not mermaid:
            mermaid = _fallback_diagram(structure)

        return AnalyzerResult(
            data={"diagrams": {"architecture": mermaid, "source": source}}
        )

    def _generate_with_llm(
        self, context: AnalysisContext, synthesis: dict, structure: dict
    ) -> str:
        modules = synthesis.get("modules", []) or []
        modules_txt = "\n".join(
            f"- {m['name']} ({m.get('path', '')}): {m.get('responsibility', '')}"
            for m in modules
        ) or "—"
        struct_txt = ", ".join(structure.get("top_level_dirs", []) or []) or "—"
        prompt = _PROMPT.format(modules=modules_txt, structure=struct_txt)
        try:
            raw = get_llm().chat(
                [system(_SYSTEM), user(prompt)],
                max_tokens=500,
                temperature=0.1,
                on_chunk=llm_token_sink(context, 200),
            )
        except LLMError as exc:
            logger.warning("diagrams.llm_unavailable", extra={"error": str(exc)})
            return ""
        return _sanitize_mermaid(raw)


def _sanitize_mermaid(raw: str) -> str:
    text = raw.strip()
    fenced = _FENCE.search(text)
    if fenced:
        text = fenced.group(1).strip()
    if not text:
        return ""
    first = text.lstrip().splitlines()[0].strip().lower()
    if not first.startswith(_VALID_HEADERS):
        logger.warning("diagrams.invalid_header", extra={"header": first[:40]})
        return ""
    return text


def _fallback_diagram(structure: dict) -> str:
    """Flowchart determinista a partir de los directorios de nivel superior."""
    top_dirs = (structure.get("top_level_dirs", []) or [])[:8]
    arch = structure.get("architecture", {}) or {}
    root_label = arch.get("pattern", "Proyecto") or "Proyecto"

    lines = ["flowchart TD", f'    root["{_safe(root_label)}"]']
    if not top_dirs:
        lines.append('    root --> src["código fuente"]')
        return "\n".join(lines)
    for i, name in enumerate(top_dirs):
        node = f"n{i}"
        lines.append(f'    {node}["{_safe(name)}"]')
        lines.append(f"    root --> {node}")
    return "\n".join(lines)


def _safe(label: str) -> str:
    """Etiqueta segura para Mermaid (sin comillas dobles ni corchetes)."""
    return re.sub(r'["\[\]{}|]', " ", label).strip()[:40] or "nodo"
