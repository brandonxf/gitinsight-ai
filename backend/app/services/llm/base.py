"""Interfaz agnóstica del proveedor LLM y tipos compartidos.

Tanto Ollama (local) como los proveedores free tier (Groq/Gemini/OpenRouter)
exponen una API compatible con la de OpenAI, por lo que un único cliente
(`OpenAICompatLLM`) sirve para ambos; la selección se hace por configuración.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass


class LLMError(RuntimeError):
    """Fallo al invocar el proveedor LLM (red, timeout, respuesta inválida)."""


@dataclass(frozen=True)
class ChatMessage:
    """Un mensaje de la conversación (rol + contenido)."""

    role: str  # "system" | "user" | "assistant"
    content: str

    def as_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


def system(content: str) -> ChatMessage:
    return ChatMessage("system", content)


def user(content: str) -> ChatMessage:
    return ChatMessage("user", content)


class LLMProvider(ABC):
    """Contrato mínimo que usan los analizadores de síntesis."""

    #: Identificador del modelo (para trazas y metadatos del resultado).
    model: str

    @abstractmethod
    def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False,
        on_chunk: Callable[[str], None] | None = None,
    ) -> str:
        """Devuelve el texto de la respuesta del asistente.

        Si se pasa `on_chunk`, la respuesta se consume en streaming y el callback
        recibe cada fragmento generado (para reportar progreso).
        """
        raise NotImplementedError

    @abstractmethod
    def chat_json(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        on_chunk: Callable[[str], None] | None = None,
    ) -> dict:
        """Como `chat`, pero parsea la respuesta como un objeto JSON."""
        raise NotImplementedError

    @abstractmethod
    def ping(self) -> bool:
        """Comprobación rápida de disponibilidad (sin lanzar excepción)."""
        raise NotImplementedError
