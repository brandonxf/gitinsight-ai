"""Tests de la fase de síntesis IA (Fase 2) con un LLM falso (sin red)."""
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from app.analyzers import build_context, run_pipeline, run_synthesis
from app.analyzers.diagrams import DiagramsAnalyzer, _sanitize_mermaid
from app.analyzers.evidence import build_evidence
from app.services.llm import factory
from app.services.llm.base import ChatMessage, LLMProvider
from app.services.llm.openai_compat import _parse_json

SAMPLE_APP = '''\
"""Demo app."""
import os


def main():
    print(os.getenv("HOME"))
'''


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\ndependencies = ["fastapi"]\n'
    )
    (tmp_path / "README.md").write_text("# Demo\nUn proyecto de ejemplo.\n")
    (tmp_path / "main.py").write_text(SAMPLE_APP)
    return tmp_path


class FakeLLM(LLMProvider):
    """Proveedor LLM determinista para tests."""

    model = "fake-model"

    def __init__(self, json_payload: dict | None = None, text: str = "") -> None:
        self._json = json_payload or {}
        self._text = text

    def chat(self, messages: Sequence[ChatMessage], **kwargs) -> str:
        return self._text

    def chat_json(self, messages: Sequence[ChatMessage], **kwargs) -> dict:
        return self._json

    def ping(self) -> bool:
        return True


def _install_fake(monkeypatch: pytest.MonkeyPatch, llm: LLMProvider) -> None:
    factory.get_llm.cache_clear()
    monkeypatch.setattr("app.analyzers.explain.get_llm", lambda: llm)
    monkeypatch.setattr("app.analyzers.diagrams.get_llm", lambda: llm)
    monkeypatch.setattr("app.analyzers.docs_gen.get_llm", lambda: llm)


# ---------- parsing del cliente LLM ----------


def test_parse_json_plain():
    assert _parse_json('{"a": 1}') == {"a": 1}


def test_parse_json_fenced():
    assert _parse_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_parse_json_with_surrounding_text():
    raw = 'Claro, aquí tienes:\n{"a": 1, "b": 2}\n¡Listo!'
    assert _parse_json(raw) == {"a": 1, "b": 2}


# ---------- sanitización de Mermaid ----------


def test_sanitize_mermaid_strips_fence():
    raw = "```mermaid\nflowchart TD\n  a-->b\n```"
    assert _sanitize_mermaid(raw).startswith("flowchart TD")


def test_sanitize_mermaid_rejects_prose():
    assert _sanitize_mermaid("Aquí tienes un diagrama bonito") == ""


# ---------- evidencia ----------


def test_build_evidence_includes_key_signals(sample_repo: Path):
    out = run_pipeline(build_context(sample_repo))
    ctx = build_context(sample_repo)
    ctx.shared["primary_language"] = out.data["primary_language"]
    evidence = build_evidence(ctx, out.data, out.findings)
    assert "Python" in evidence
    assert "README.md" in evidence
    assert "main.py" in evidence


# ---------- orquestación de síntesis ----------


def test_run_synthesis_with_fake_llm(monkeypatch: pytest.MonkeyPatch, sample_repo: Path):
    payload = {
        "summary": "Una app de demo.",
        "purpose": "Mostrar el pipeline.",
        "modules": [{"name": "core", "path": "main.py", "responsibility": "punto de entrada"}],
        "flow": "main() imprime el HOME.",
    }
    fake = FakeLLM(json_payload=payload, text="flowchart TD\n  a-->b")
    _install_fake(monkeypatch, fake)

    out = run_pipeline(build_context(sample_repo))
    ctx = build_context(sample_repo)
    ctx.shared["primary_language"] = out.data["primary_language"]

    synth = run_synthesis(ctx, out.data, out.findings)

    assert synth["summary"] == "Una app de demo."
    assert synth["purpose"] == "Mostrar el pipeline."
    assert synth["modules"][0]["name"] == "core"
    assert synth["flow_description"] == "main() imprime el HOME."
    assert synth["ai"]["available"] is True
    assert synth["diagrams"]["architecture"].startswith("flowchart TD")
    assert synth["diagrams"]["source"] == "ai"


def test_diagrams_fallback_when_llm_disabled(monkeypatch: pytest.MonkeyPatch, sample_repo: Path):
    monkeypatch.setattr("app.analyzers.diagrams.settings.llm_enabled", False)
    out = run_pipeline(build_context(sample_repo))
    ctx = build_context(sample_repo)
    ctx.shared["det_data"] = out.data
    ctx.shared["synthesis"] = {}

    result = DiagramsAnalyzer().run(ctx)
    mermaid = result.data["diagrams"]["architecture"]
    assert mermaid.startswith("flowchart TD")
    assert result.data["diagrams"]["source"] == "fallback"


def test_synthesis_skipped_when_disabled(monkeypatch: pytest.MonkeyPatch, sample_repo: Path):
    monkeypatch.setattr("app.analyzers.explain.settings.llm_enabled", False)
    monkeypatch.setattr("app.analyzers.docs_gen.settings.llm_enabled", False)
    monkeypatch.setattr("app.analyzers.diagrams.settings.llm_enabled", False)

    out = run_pipeline(build_context(sample_repo))
    ctx = build_context(sample_repo)
    synth = run_synthesis(ctx, out.data, out.findings)

    # Sin LLM: no hay explicación, pero el diagrama determinista sí se genera.
    assert "summary" not in synth or synth.get("summary") is None
    assert synth["diagrams"]["source"] == "fallback"


def test_parse_json_invalid_raises():
    from app.services.llm.base import LLMError

    with pytest.raises(LLMError):
        _parse_json("esto no es json en absoluto")


def test_trim_echoed_context():
    from app.analyzers.docs_gen import _trim_echoed_context

    readme = "# Proyecto\nDescripción.\n\n=== EVIDENCIA ===\nbasura del prompt"
    assert _trim_echoed_context(readme) == "# Proyecto\nDescripción."

    with_rules = "# Proyecto\nTexto.\n\nReglas estrictas:\n- bla"
    assert _trim_echoed_context(with_rules) == "# Proyecto\nTexto."
