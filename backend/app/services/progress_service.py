"""Publicación de progreso del job en Redis pub/sub (best-effort).

En la Fase 1 el frontend usa polling sobre la DB; este canal queda listo para
el streaming SSE de la Fase 3. Los fallos de publicación nunca rompen el análisis.
"""
from __future__ import annotations

import json
import uuid

import redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: redis.Redis | None = None


def _get_client() -> redis.Redis | None:
    global _client
    if _client is None:
        try:
            _client = redis.Redis.from_url(settings.redis_url)
        except Exception as exc:  # noqa: BLE001
            logger.warning("progress.redis_init_failed", extra={"error": str(exc)})
            return None
    return _client


def channel(job_id: uuid.UUID) -> str:
    return f"analysis:progress:{job_id}"


def publish(job_id: uuid.UUID, phase: str | None, progress_pct: int, status: str) -> None:
    client = _get_client()
    if client is None:
        return
    payload = json.dumps(
        {"phase": phase, "progress_pct": progress_pct, "status": status}
    )
    try:
        client.publish(channel(job_id), payload)
    except Exception as exc:  # noqa: BLE001
        logger.debug("progress.publish_failed", extra={"error": str(exc)})
