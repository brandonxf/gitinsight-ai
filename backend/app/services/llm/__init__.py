"""Capa de IA agnóstica del proveedor (chat LLM gratuito: Ollama / free tier)."""
from app.services.llm.base import ChatMessage, LLMError, LLMProvider, system, user
from app.services.llm.factory import get_llm

__all__ = [
    "ChatMessage",
    "LLMError",
    "LLMProvider",
    "system",
    "user",
    "get_llm",
]
