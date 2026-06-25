"""Complejidad ciclomática de funciones Python vía radon."""
from __future__ import annotations

from app.analyzers.base import AnalysisContext, Analyzer, AnalyzerResult, FindingData
from app.core.logging import get_logger

logger = get_logger(__name__)

# Umbrales de complejidad ciclomática (escala McCabe / radon).
_MEDIUM_THRESHOLD = 11   # C: moderadamente complejo
_HIGH_THRESHOLD = 21     # D/E: complejo
_CRITICAL_THRESHOLD = 41  # F: muy complejo
_MAX_FINDINGS = 300


def _severity(score: int) -> str:
    if score >= _CRITICAL_THRESHOLD:
        return "high"
    if score >= _HIGH_THRESHOLD:
        return "medium"
    return "low"


class ComplexityAnalyzer(Analyzer):
    name = "complexity"

    def applies(self, context: AnalysisContext) -> bool:
        return bool(context.files_for_language("Python"))

    def run(self, context: AnalysisContext) -> AnalyzerResult:
        try:
            from radon.complexity import cc_visit
        except ImportError:
            logger.warning("radon.unavailable")
            return AnalyzerResult(data={"complexity": {"available": False}})

        findings: list[FindingData] = []
        scores: list[int] = []

        for f in context.files_for_language("Python"):
            if f.size_bytes > 1_000_000:
                continue
            try:
                source = f.abs_path.read_text(encoding="utf-8", errors="ignore")
                blocks = cc_visit(source)
            except (OSError, SyntaxError):
                continue
            for block in blocks:
                scores.append(block.complexity)
                if block.complexity < _MEDIUM_THRESHOLD:
                    continue
                if len(findings) >= _MAX_FINDINGS:
                    continue
                findings.append(
                    FindingData(
                        category="complexity",
                        severity=_severity(block.complexity),
                        rule_id=f"CC{block.complexity}",
                        file_path=f.rel_path,
                        line_start=block.lineno,
                        line_end=getattr(block, "endline", None),
                        message=(
                            f"'{block.name}' tiene complejidad ciclomática "
                            f"{block.complexity} (umbral {_MEDIUM_THRESHOLD})."
                        ),
                        suggestion="Considera dividir la función en unidades más pequeñas.",
                        metadata={"complexity": block.complexity},
                    )
                )

        avg = round(sum(scores) / len(scores), 2) if scores else 0
        return AnalyzerResult(
            findings=findings,
            data={
                "complexity": {
                    "available": True,
                    "functions_analyzed": len(scores),
                    "average": avg,
                    "max": max(scores) if scores else 0,
                }
            },
        )
