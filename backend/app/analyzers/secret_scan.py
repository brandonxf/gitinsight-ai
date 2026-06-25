"""Detección de secretos: patrones regex + comprobación de entropía."""
from __future__ import annotations

import math
import re

from app.analyzers.base import (
    MAX_TEXT_FILE_BYTES,
    AnalysisContext,
    Analyzer,
    AnalyzerResult,
    FindingData,
)

# (rule_id, descripción, regex). Patrones de alta confianza.
_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    ("AWS_ACCESS_KEY", "AWS Access Key ID", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("PRIVATE_KEY", "Clave privada (PEM)", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),  # noqa: E501
    ("GITHUB_TOKEN", "Token de GitHub", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("SLACK_TOKEN", "Token de Slack", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("GOOGLE_API_KEY", "Google API Key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("STRIPE_KEY", "Stripe Secret Key", re.compile(r"\b(sk|rk)_(live|test)_[0-9A-Za-z]{20,}\b")),
    ("JWT", "JSON Web Token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),  # noqa: E501
    ("PRIVATE_KEY_OPENAI", "OpenAI API Key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
]

# Asignaciones tipo `password = "..."` / `api_key: "..."` con valor sospechoso.
_ASSIGNMENT_RE = re.compile(
    r"""(?i)\b(password|passwd|secret|api[_-]?key|token|access[_-]?key|private[_-]?key)\b"""
    r"""\s*[:=]\s*['"]([^'"\s]{8,})['"]"""
)

# Valores que claramente NO son secretos reales (placeholders).
_PLACEHOLDERS = re.compile(
    r"(?i)(example|placeholder|changeme|your[_-]?|dummy|xxxx|<.*>|\$\{.*\}|test|sample|none|null)"
)

_MAX_FINDINGS = 200
# Extensiones que suelen ser puro binario o no relevantes para secretos.
_SKIP_SUFFIXES = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".pdf", ".zip", ".gz",
    ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mp3", ".wasm", ".lock",
    ".min.js", ".map",
})


def _shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts: dict[str, int] = {}
    for ch in value:
        counts[ch] = counts.get(ch, 0) + 1
    length = len(value)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def _looks_high_entropy(value: str) -> bool:
    return len(value) >= 20 and _shannon_entropy(value) >= 4.0


class SecretScanAnalyzer(Analyzer):
    name = "secret_scan"

    def run(self, context: AnalysisContext) -> AnalyzerResult:
        findings: list[FindingData] = []

        for f in context.files:
            if f.abs_path.suffix.lower() in _SKIP_SUFFIXES:
                continue
            if f.size_bytes > MAX_TEXT_FILE_BYTES:
                continue
            try:
                text = f.abs_path.read_text(encoding="utf-8", errors="strict")
            except (OSError, UnicodeDecodeError):
                continue  # binario o ilegible

            for lineno, line in enumerate(text.splitlines(), start=1):
                if len(findings) >= _MAX_FINDINGS:
                    break
                self._scan_line(line, lineno, f.rel_path, findings)
            if len(findings) >= _MAX_FINDINGS:
                break

        by_sev: dict[str, int] = {}
        for fd in findings:
            by_sev[fd.severity] = by_sev.get(fd.severity, 0) + 1

        return AnalyzerResult(
            findings=findings,
            data={"secrets": {"count": len(findings), "by_severity": by_sev}},
        )

    def _scan_line(
        self, line: str, lineno: int, rel_path: str, findings: list[FindingData]
    ) -> None:
        for rule_id, desc, pattern in _PATTERNS:
            if pattern.search(line):
                findings.append(
                    FindingData(
                        category="secret",
                        severity="high",
                        rule_id=rule_id,
                        file_path=rel_path,
                        line_start=lineno,
                        message=f"Posible secreto detectado: {desc}.",
                        suggestion="Revoca la credencial y muévela a una variable de entorno.",
                        metadata={"confidence": "high"},
                    )
                )
                return  # un hallazgo por línea es suficiente

        match = _ASSIGNMENT_RE.search(line)
        if match:
            key, value = match.group(1), match.group(2)
            if _PLACEHOLDERS.search(value):
                return
            if _looks_high_entropy(value):
                findings.append(
                    FindingData(
                        category="secret",
                        severity="medium",
                        rule_id="HIGH_ENTROPY_ASSIGNMENT",
                        file_path=rel_path,
                        line_start=lineno,
                        message=f"Asignación sospechosa a '{key}' con valor de alta entropía.",
                        suggestion="Confirma que no sea una credencial; usa secretos/entorno.",
                        metadata={"confidence": "medium", "key": key},
                    )
                )
