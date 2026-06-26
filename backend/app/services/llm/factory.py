"""Selección del proveedor LLM según la configuración del entorno.

Ollama y los proveedores `openai_compat` (Groq/Gemini/OpenRouter) comparten el
mismo cliente; solo cambian `base_url`, `model` y `api_key`.
"""
from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.services.llm.openai_compat import OpenAICompatLLM


@lru_cache
def get_llm() -> OpenAICompatLLM:
    return OpenAICompatLLM(
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        timeout=float(settings.llm_timeout_seconds),
        max_retries=settings.llm_max_retries,
    )
