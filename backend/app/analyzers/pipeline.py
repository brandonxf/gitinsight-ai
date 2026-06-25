"""Orquestador del pipeline de analizadores deterministas (Fase 1)."""
from __future__ import annotations

from collections.abc import Callable

from app.analyzers.base import AnalysisContext, Analyzer, AnalyzerResult, FindingData
from app.analyzers.complexity import ComplexityAnalyzer
from app.analyzers.quality_ruff import RuffAnalyzer
from app.analyzers.secret_scan import SecretScanAnalyzer
from app.analyzers.security_bandit import BanditAnalyzer
from app.analyzers.structure import StructureAnalyzer
from app.analyzers.tech_detect import TechDetectAnalyzer
from app.core.logging import get_logger

logger = get_logger(__name__)

# Orden importa: tech_detect rellena context.shared['primary_language'] que otros usan.
ANALYZERS: list[Analyzer] = [
    TechDetectAnalyzer(),
    StructureAnalyzer(),
    RuffAnalyzer(),
    ComplexityAnalyzer(),
    BanditAnalyzer(),
    SecretScanAnalyzer(),
]

# Severidades ordenadas para derivar el nivel de riesgo.
_SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


class PipelineOutput:
    """Resultado agregado del pipeline: findings + datos para AnalysisResult."""

    def __init__(self) -> None:
        self.findings: list[FindingData] = []
        self.data: dict = {}


ProgressCb = Callable[[str, int], None]


def run_pipeline(
    context: AnalysisContext, on_progress: ProgressCb | None = None
) -> PipelineOutput:
    """Ejecuta cada analizador aplicable, agregando hallazgos y datos.

    `on_progress(phase, pct)` se invoca antes de cada analizador (pct 10..90,
    reservando 0-10 para clonado y 90-100 para persistencia).
    """
    output = PipelineOutput()
    applicable = applicable_analyzers(context)
    total = len(applicable) or 1

    for idx, analyzer in enumerate(applicable):
        pct = 10 + int((idx / total) * 80)
        if on_progress:
            on_progress(analyzer.name, pct)
        try:
            result: AnalyzerResult = analyzer.run(context)
        except Exception:  # noqa: BLE001 — un analizador no debe tumbar el pipeline
            logger.exception("analyzer.failed", extra={"analyzer": analyzer.name})
            continue
        output.findings.extend(result.findings)
        output.data.update(result.data)

    output.data["aggregate"] = aggregate(output.findings, context)
    return output


def applicable_analyzers(context: AnalysisContext) -> list[Analyzer]:
    """Analizadores que se ejecutarán para este contexto (en orden)."""
    return [a for a in ANALYZERS if a.applies(context)]


def aggregate(findings: list[FindingData], context: AnalysisContext) -> dict:
    """Calcula risk_level, quality_score y conteos a partir de los hallazgos."""
    by_category: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    max_security_sev = "info"

    for f in findings:
        by_category[f.category] = by_category.get(f.category, 0) + 1
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
        if f.category in {"secret", "vuln", "insecure_config"}:
            if _SEVERITY_ORDER[f.severity] > _SEVERITY_ORDER[max_security_sev]:
                max_security_sev = f.severity

    risk_level = _risk_level(max_security_sev, by_category)
    quality_score = _quality_score(by_severity, context)

    return {
        "findings_total": len(findings),
        "by_category": by_category,
        "by_severity": by_severity,
        "risk_level": risk_level,
        "quality_score": quality_score,
    }


def _risk_level(max_security_sev: str, by_category: dict[str, int]) -> str:
    secrets = by_category.get("secret", 0)
    if max_security_sev in {"high", "critical"} or secrets > 0:
        return "high"
    if max_security_sev == "medium":
        return "medium"
    if by_category.get("vuln", 0) > 0:
        return "low"
    return "low"


def _quality_score(by_severity: dict[str, int], context: AnalysisContext) -> int:
    """Score 0-100: penaliza por densidad de hallazgos ponderada por severidad."""
    weights = {"info": 0.0, "low": 1.0, "medium": 3.0, "high": 6.0, "critical": 10.0}
    penalty = sum(weights[s] * n for s, n in by_severity.items())
    loc = max(context.shared.get("lines_of_code", 0), 1)
    # Penalización normalizada por cada 100 líneas de código.
    density = penalty / (loc / 100)
    score = max(0, min(100, round(100 - density)))
    return int(score)
