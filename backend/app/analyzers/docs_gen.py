"""Generación de documentación: un README mejorado en Markdown, anclado en la evidencia.

Produce el campo `generated_docs` del resultado. Reutiliza la síntesis ya
calculada por `explain` (resumen, propósito, módulos) cuando está disponible.
"""
from __future__ import annotations

from app.analyzers.base import AnalysisContext, Analyzer, AnalyzerResult
from app.analyzers.evidence import build_evidence
from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm import LLMError, get_llm, system, user

logger = get_logger(__name__)

_SYSTEM = (
    "Eres un technical writer. Redactas documentación clara y profesional en español, "
    "en formato Markdown, basándote SOLO en la evidencia del repositorio. No inventes "
    "comandos, dependencias ni rutas que no aparezcan en la evidencia."
)

_PROMPT = """\
A continuación tienes el contexto del repositorio (NO lo copies en tu respuesta).

=== SÍNTESIS PREVIA ===
{synthesis}

=== EVIDENCIA ===
{evidence}
=== FIN DEL CONTEXTO ===

Tarea: redacta un README.md mejorado para este proyecto usando SOLO el contexto
anterior. Estructura (en este orden):

# <Nombre del proyecto>
Descripción breve (1-2 frases).

## Características
- viñetas con lo que hace, derivadas de la evidencia.

## Arquitectura
Breve descripción de los módulos principales detectados.

## Tecnologías
Lenguajes y frameworks detectados.

## Estructura del proyecto
Breve explicación de los directorios principales.

Reglas estrictas:
- Empieza directamente con `# ` (el título). No incluyas las secciones de contexto
  anteriores (SÍNTESIS/EVIDENCIA) ni ningún texto antes del título.
- No inventes instrucciones de instalación si no hay evidencia de ellas.
- Máximo ~350 palabras. Devuelve SOLO el Markdown, sin envolverlo en ```.
"""


class DocsGenAnalyzer(Analyzer):
    name = "docs_gen"

    def applies(self, context: AnalysisContext) -> bool:
        return settings.llm_enabled

    def run(self, context: AnalysisContext) -> AnalyzerResult:
        data = context.shared.get("det_data", {})
        findings = context.shared.get("det_findings", [])
        synthesis = context.shared.get("synthesis", {})

        synthesis_txt = _synthesis_summary(synthesis)
        evidence = build_evidence(context, data, findings)
        prompt = _PROMPT.format(synthesis=synthesis_txt, evidence=evidence)

        try:
            readme = get_llm().chat(
                [system(_SYSTEM), user(prompt)], max_tokens=1100, temperature=0.3
            )
        except LLMError as exc:
            logger.warning("docs_gen.llm_unavailable", extra={"error": str(exc)})
            return AnalyzerResult(data={})

        readme = _trim_echoed_context(_strip_fences(readme)).strip()
        if not readme:
            return AnalyzerResult(data={})
        logger.info("docs_gen.done", extra={"chars": len(readme)})
        return AnalyzerResult(data={"generated_docs": {"readme": readme}})


def _synthesis_summary(synthesis: dict) -> str:
    parts: list[str] = []
    if synthesis.get("summary"):
        parts.append(f"Resumen: {synthesis['summary']}")
    if synthesis.get("purpose"):
        parts.append(f"Propósito: {synthesis['purpose']}")
    modules = synthesis.get("modules", []) or []
    if modules:
        parts.append(
            "Módulos: "
            + "; ".join(f"{m['name']} — {m.get('responsibility', '')}" for m in modules)
        )
    return "\n".join(parts) or "—"


# Marcadores que delatan que el modelo copió el contexto del prompt en su salida.
_ECHO_MARKERS = (
    "=== SÍNTESIS",
    "=== EVIDENCIA",
    "=== FIN DEL CONTEXTO",
    "## Síntesis previa",
    "# Síntesis previa",
    "## Evidencia",
    "### Metadatos del repositorio",
    "Reglas estrictas:",
    "Tarea: redacta",
)


def _trim_echoed_context(text: str) -> str:
    """Corta el README si el modelo pegó las secciones de contexto del prompt."""
    cut = len(text)
    for marker in _ECHO_MARKERS:
        idx = text.find(marker)
        if idx != -1:
            cut = min(cut, idx)
    return text[:cut].rstrip()


def _strip_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines)
    return stripped
