"""Fase de síntesis IA (Fase 2): orquesta los analizadores que usan el LLM.

A diferencia de los analizadores deterministas, los de síntesis dependen de la
salida agregada de aquellos (estructura, lenguajes, hallazgos). Por eso se ejecutan
en una segunda pasada, recibiendo esos datos a través de `context.shared`.
"""
from __future__ import annotations

from collections.abc import Callable

from app.analyzers.base import AnalysisContext, Analyzer, FindingData
from app.analyzers.diagrams import DiagramsAnalyzer
from app.analyzers.docs_gen import DocsGenAnalyzer
from app.analyzers.explain import ExplainAnalyzer
from app.core.logging import get_logger

logger = get_logger(__name__)

# Orden importa: explain produce módulos/resumen que diagrams y docs_gen reutilizan.
SYNTHESIS_ANALYZERS: list[Analyzer] = [
    ExplainAnalyzer(),
    DiagramsAnalyzer(),
    DocsGenAnalyzer(),
]

ProgressCb = Callable[[str, int], None]


def applicable_synthesis(context: AnalysisContext) -> list[Analyzer]:
    return [a for a in SYNTHESIS_ANALYZERS if a.applies(context)]


def prepare_synthesis_context(
    context: AnalysisContext, det_data: dict, findings: list[FindingData]
) -> None:
    """Inyecta en `context.shared` lo que los analizadores de síntesis consumen."""
    context.shared["det_data"] = det_data
    context.shared["det_findings"] = findings
    context.shared.setdefault("synthesis", {})


def run_synthesis(
    context: AnalysisContext,
    det_data: dict,
    findings: list[FindingData],
    on_progress: ProgressCb | None = None,
) -> dict:
    """Ejecuta la fase de síntesis y devuelve los datos agregados (uso standalone/tests).

    El worker ejecuta los analizadores uno a uno para reportar progreso; esta
    función ofrece la misma orquestación de forma síncrona.
    """
    prepare_synthesis_context(context, det_data, findings)
    out: dict = {}
    for analyzer in applicable_synthesis(context):
        if on_progress:
            on_progress(analyzer.name, 0)
        try:
            result = analyzer.run(context)
        except Exception:  # noqa: BLE001 — un analizador no debe tumbar la síntesis
            logger.exception("synthesis.failed", extra={"analyzer": analyzer.name})
            continue
        out.update(result.data)
        context.shared["synthesis"].update(result.data)
    return out
