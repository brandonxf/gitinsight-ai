"""Cliente LLM compatible con la API de OpenAI (Ollama local o free tier).

Llama a `POST {base_url}/chat/completions`. Es síncrono a propósito: los
analizadores se ejecutan en un hilo (`asyncio.to_thread`) dentro del worker.
"""
from __future__ import annotations

import json
import re
import time
from collections.abc import Sequence

import httpx

from app.core.logging import get_logger
from app.services.llm.base import ChatMessage, LLMError, LLMProvider

logger = get_logger(__name__)

# Recorte de seguridad por mensaje: evita prompts gigantes que agotan la ventana
# de contexto del modelo o disparan timeouts. La evidencia ya viene acotada.
MAX_MESSAGE_CHARS = 24_000

_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class OpenAICompatLLM(LLMProvider):
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str = "",
        timeout: float = 150.0,
        max_retries: int = 2,
    ) -> None:
        self._url = base_url.rstrip("/") + "/chat/completions"
        self.model = model
        self._headers = {"Content-Type": "application/json"}
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"
        self._timeout = timeout
        self._max_retries = max(1, max_retries)

    def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> str:
        payload: dict = {
            "model": self.model,
            "messages": [_trim(m).as_dict() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    resp = client.post(self._url, headers=self._headers, json=payload)
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                return content or ""
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                # Algunos modelos no soportan response_format: reintenta sin él.
                if json_mode and exc.response.status_code == 400:
                    payload.pop("response_format", None)
                    json_mode = False
                    continue
                logger.warning(
                    "llm.http_error",
                    extra={"attempt": attempt, "status": exc.response.status_code},
                )
            except (httpx.HTTPError, KeyError, ValueError, IndexError) as exc:
                last_exc = exc
                logger.warning("llm.error", extra={"attempt": attempt, "error": str(exc)})

            if attempt < self._max_retries:
                time.sleep(min(2**attempt, 8))

        raise LLMError(f"El LLM falló tras {self._max_retries} intentos: {last_exc}")

    def chat_json(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> dict:
        raw = self.chat(
            messages, temperature=temperature, max_tokens=max_tokens, json_mode=True
        )
        return _parse_json(raw)

    def ping(self) -> bool:
        try:
            self.chat([ChatMessage("user", "ping")], max_tokens=1)
            return True
        except LLMError:
            return False


def _trim(message: ChatMessage) -> ChatMessage:
    if len(message.content) <= MAX_MESSAGE_CHARS:
        return message
    head = MAX_MESSAGE_CHARS - 200
    truncated = message.content[:head] + "\n\n[... contenido recortado ...]"
    return ChatMessage(message.role, truncated)


def _parse_json(raw: str) -> dict:
    """Extrae un objeto JSON de la respuesta, tolerando ```fences``` o texto extra."""
    text = raw.strip()
    fenced = _JSON_FENCE.search(text)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Último recurso: recorta al primer '{' y al último '}'.
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMError(f"Respuesta JSON inválida del LLM: {exc}") from exc
    raise LLMError("El LLM no devolvió un objeto JSON parseable.")
