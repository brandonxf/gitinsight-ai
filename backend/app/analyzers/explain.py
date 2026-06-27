"""Síntesis IA: resumen, propósito, módulos y flujo, anclados en la evidencia.

Produce los campos `summary`, `purpose`, `modules` y `flow_description` del
resultado. Si el LLM no está disponible, degrada con elegancia (no rompe el job).
"""
from __future__ import annotations

from app.analyzers.base import (
    AnalysisContext,
    Analyzer,
    AnalyzerResult,
    llm_token_sink,
)
from app.analyzers.evidence import build_evidence
from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm import LLMError, get_llm, system, user

logger = get_logger(__name__)

_SYSTEM = (
    "Eres un ingeniero de software senior que explica repositorios a otros "
    "desarrolladores. Respondes SIEMPRE en español, de forma concisa y técnica. "
    "Te basas EXCLUSIVAMENTE en la evidencia proporcionada; si algo no está en la "
    "evidencia, no lo inventes. Devuelves únicamente un objeto JSON válido."
)

_INSTRUCTIONS = """\
A partir de la evidencia del repositorio, devuelve un objeto JSON con esta forma exacta:

{
  "summary": "2-4 frases que describan qué es el proyecto y qué hace.",
  "purpose": "1-2 frases sobre el problema que resuelve y para quién.",
  "modules": [
    {"name": "módulo/área", "path": "ruta principal", "responsibility": "responsabilidad breve"}
  ],
  "flow": "Un párrafo describiendo el flujo principal de ejecución o de datos."
}

Reglas:
- 3 a 6 módulos, los más importantes; usa rutas reales vistas en la evidencia.
- No incluyas texto fuera del JSON. No uses markdown.
"""


class ExplainAnalyzer(Analyzer):
    name = "explain"

    def applies(self, context: AnalysisContext) -> bool:
        return settings.llm_enabled

    def run(self, context: AnalysisContext) -> AnalyzerResult:
        data = context.shared.get("det_data", {})
        findings = context.shared.get("det_findings", [])
        evidence = build_evidence(context, data, findings)

        llm = get_llm()
        messages = [
            system(_SYSTEM),
            user(f"{_INSTRUCTIONS}\n\n# Evidencia\n{evidence}"),
        ]
        try:
            obj = llm.chat_json(
                messages,
                max_tokens=850,
                temperature=0.2,
                on_chunk=llm_token_sink(context, 320),
            )
        except LLMError as exc:
            logger.warning("explain.llm_unavailable", extra={"error": str(exc)})
            return AnalyzerResult(
                data={"ai": {"available": False, "error": str(exc)}}
            )

        result = {
            "summary": _clean(obj.get("summary")),
            "purpose": _clean(obj.get("purpose")),
            "modules": _normalize_modules(obj.get("modules")),
            "flow_description": _clean(obj.get("flow")),
            "ai": {"available": True, "model": llm.model},
        }
        logger.info("explain.done", extra={"model": llm.model, "modules": len(result["modules"])})
        return AnalyzerResult(data=result)


def _clean(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _normalize_modules(raw: object) -> list[dict]:
    if not isinstance(raw, list):
        return []
    modules: list[dict] = []
    for item in raw[:8]:
        if not isinstance(item, dict):
            continue
        name = _clean(item.get("name"))
        if not name:
            continue
        modules.append(
            {
                "name": name,
                "path": _clean(item.get("path")) or "",
                "responsibility": _clean(item.get("responsibility")) or "",
            }
        )
    return modules
