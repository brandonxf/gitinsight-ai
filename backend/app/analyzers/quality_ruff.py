"""Calidad de código Python vía Ruff (subprocess, salida JSON)."""
from __future__ import annotations

import json
import subprocess

from app.analyzers.base import (
    AnalysisContext,
    Analyzer,
    AnalyzerResult,
    FindingData,
    relativize,
    resolve_tool,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

# Prefijos de regla Ruff que tratamos como bugs probables (resto: code_smell).
_BUG_PREFIXES = ("F", "B", "E9", "S")
_RUFF_TIMEOUT = 120
_MAX_FINDINGS = 500


class RuffAnalyzer(Analyzer):
    name = "quality_ruff"

    def applies(self, context: AnalysisContext) -> bool:
        return bool(context.files_for_language("Python"))

    def run(self, context: AnalysisContext) -> AnalyzerResult:
        ruff_bin = resolve_tool("ruff")
        if ruff_bin is None:
            logger.warning("ruff.not_found")
            return AnalyzerResult(data={"quality": {"ruff_available": False}})
        cmd = [
            ruff_bin, "check", ".",
            "--output-format", "json",
            "--no-cache",
            "--exit-zero",
            "--quiet",
        ]
        try:
            proc = subprocess.run(
                cmd,
                cwd=context.repo_path,
                capture_output=True,
                text=True,
                timeout=_RUFF_TIMEOUT,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            logger.warning("ruff.failed", extra={"error": str(exc)})
            return AnalyzerResult(data={"quality": {"ruff_available": False}})

        try:
            issues = json.loads(proc.stdout or "[]")
        except json.JSONDecodeError:
            logger.warning("ruff.bad_output")
            return AnalyzerResult(data={"quality": {"ruff_available": False}})

        findings: list[FindingData] = []
        for issue in issues[:_MAX_FINDINGS]:
            code = issue.get("code") or "RUFF"
            category = "bug" if code.startswith(_BUG_PREFIXES) else "code_smell"
            location = issue.get("location") or {}
            end = issue.get("end_location") or {}
            fix = issue.get("fix") or {}
            findings.append(
                FindingData(
                    category=category,
                    severity="low",
                    rule_id=code,
                    file_path=relativize(issue.get("filename"), context.repo_path),
                    line_start=location.get("row"),
                    line_end=end.get("row"),
                    message=issue.get("message", ""),
                    suggestion=fix.get("message"),
                    metadata={"url": issue.get("url")},
                )
            )

        return AnalyzerResult(
            findings=findings,
            data={"quality": {"ruff_available": True, "ruff_issues": len(issues)}},
        )
