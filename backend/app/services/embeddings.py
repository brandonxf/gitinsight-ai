"""Embeddings locales con FastEmbed (ONNX en proceso, sin servicio externo).

El modelo se descarga una vez (HuggingFace) y se cachea en disco; la instancia
se memoiza por proceso. Para modelos tipo BGE se usan los prefijos de
consulta/pasaje cuando están disponibles (mejora el retrieval).
"""
from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding

    logger.info("embeddings.load_model", extra={"model": settings.embedding_model})
    kwargs: dict = {}
    if settings.embedding_threads > 0:
        # Limita los hilos de onnxruntime para acotar RAM/CPU en despliegue.
        kwargs["threads"] = settings.embedding_threads
    return TextEmbedding(model_name=settings.embedding_model, **kwargs)


def embed_documents(texts: Sequence[str]) -> list[list[float]]:
    """Embeddings de fragmentos (pasajes). Bloqueante: llamar vía to_thread."""
    model = _model()
    embed = getattr(model, "passage_embed", None) or model.embed
    return [vec.tolist() for vec in embed(list(texts))]


def embed_query(text: str) -> list[float]:
    """Embedding de una consulta de búsqueda. Bloqueante: llamar vía to_thread."""
    model = _model()
    embed = getattr(model, "query_embed", None) or model.embed
    vectors = list(embed([text]))
    return vectors[0].tolist()
