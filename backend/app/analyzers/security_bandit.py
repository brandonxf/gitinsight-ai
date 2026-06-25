"""Análisis de seguridad de código Python vía Bandit (subprocess, salida JSON)."""
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

_BANDIT_TIMEOUT = 180
_MAX_FINDINGS = 500

# Mapeo de severidad Bandit -> severidad unificada.
_SEVERITY_MAP = {"LOW": "low", "MEDIUM": "medium", "HIGH": "high"}


class BanditAnalyzer(Analyzer):
    name = "security_bandit"

    def applies(self, context: AnalysisContext) -> bool:
        return bool(context.files_for_language("Python"))

    def run(self, context: AnalysisContext) -> AnalyzerResult:
        bandit_bin = resolve_tool("bandit")
        if bandit_bin is None:
            logger.warning("bandit.not_found")
            return AnalyzerResult(data={"security": {"bandit_available": False}})
        cmd = [
            bandit_bin, "-r", ".",
            "-f", "json",
            "-q",
            "--exclude", ".git,node_modules,venv,.venv,dist,build,tests",
        ]
        try:
            proc = subprocess.run(
                cmd,
                cwd=context.repo_path,
                capture_output=True,
                text=True,
                timeout=_BANDIT_TIMEOUT,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            logger.warning("bandit.failed", extra={"error": str(exc)})
            return AnalyzerResult(data={"security": {"bandit_available": False}})

        try:
            report = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            logger.warning("bandit.bad_output")
            return AnalyzerResult(data={"security": {"bandit_available": False}})

        findings: list[FindingData] = []
        for issue in report.get("results", [])[:_MAX_FINDINGS]:
            severity = _SEVERITY_MAP.get(issue.get("issue_severity", "LOW"), "low")
            confidence = issue.get("issue_confidence", "")
            findings.append(
                FindingData(
                    category="vuln",
                    severity=severity,
                    rule_id=issue.get("test_id"),
                    file_path=relativize(issue.get("filename"), context.repo_path),
                    line_start=issue.get("line_number"),
                    line_end=(issue.get("line_range") or [None])[-1],
                    message=issue.get("issue_text", ""),
                    suggestion=issue.get("more_info"),
                    metadata={
                        "test_name": issue.get("test_name"),
                        "confidence": confidence,
                        "cwe": (issue.get("issue_cwe") or {}).get("id"),
                    },
                )
            )

        return AnalyzerResult(
            findings=findings,
            data={"security": {"bandit_available": True, "bandit_issues": len(findings)}},
        )
