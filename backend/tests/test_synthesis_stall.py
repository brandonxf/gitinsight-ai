"""Test del detector de atasco de las fases de síntesis IA.

Garantiza que una fase cuyo LLM deja de emitir tokens se cancela y degrada con
elegancia (devuelve None) en lugar de dejar el job colgado indefinidamente
(p. ej. clavado en "Redactando documentación").
"""
from __future__ import annotations

import time
import types

import pytest

from app.analyzers.base import AnalysisContext, Analyzer, AnalyzerResult
from app.core.config import settings
from app.workers.tasks import analyze


class _StalledAnalyzer(Analyzer):
    """Simula un LLM colgado: bloquea sin producir tokens nunca."""

    name = "docs_gen"

    def run(self, context: AnalysisContext) -> AnalyzerResult:
        time.sleep(6)  # nunca toca LLM_TOKEN_KEY -> sin progreso
        return AnalyzerResult(data={"generated_docs": {"readme": "no debería llegar"}})


@pytest.mark.asyncio
async def test_synthesis_step_cancels_on_stall(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "llm_stall_seconds", 2)

    context = AnalysisContext(repo_path=tmp_path)
    # progress_pct alto: el heartbeat no intentará escribir en BD (pct <= actual).
    job = types.SimpleNamespace(id="test", progress_pct=100)

    started = time.monotonic()
    result = await analyze._run_synthesis_step(
        session=None,  # no se usa: nunca se llama a _set_progress en este caso
        job=job,
        analyzer=_StalledAnalyzer(),
        context=context,
        p0=86,
        p1=93,
    )
    elapsed = time.monotonic() - started

    assert result is None  # degradó en vez de colgarse
    assert elapsed < 10  # se canceló pronto (~llm_stall_seconds), no a los 30s
