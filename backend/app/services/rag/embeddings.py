"""
Embeddings — Sahayak AI RAG
============================
all-MiniLM-L6-v2 (384-dim) via sentence-transformers. Loaded once, lazily,
on CPU. Encoding is blocking so callers run it in a thread executor.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Optional

from app.core.config import settings
from app.core.exceptions import RagServiceException
from app.core.logging import get_logger

logger = get_logger(__name__)

_model = None
_lock = threading.Lock()


def _load():
    global _model
    if _model is not None:
        return _model
    with _lock:
        if _model is not None:
            return _model
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RagServiceException(
                "sentence-transformers is not installed. "
                "Add it to requirements and reinstall."
            ) from exc
        logger.info("Loading embedding model %s ...", settings.RAG_EMBEDDING_MODEL)
        _model = SentenceTransformer(settings.RAG_EMBEDDING_MODEL, device="cpu")
        logger.info("Embedding model ready (dim=%s)", _embedding_dim(_model))
        return _model


def _embedding_dim(model) -> Optional[int]:
    for attr in ("get_embedding_dimension", "get_sentence_embedding_dimension"):
        fn = getattr(model, attr, None)
        if callable(fn):
            try:
                return int(fn())
            except Exception:  # noqa: BLE001
                pass
    return None


def embed_sync(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = _load()
    vecs = model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,   # cosine == dot product
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return [v.tolist() for v in vecs]


async def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, embed_sync, texts)


async def embed_one(text: str) -> list[float]:
    out = await embed([text])
    return out[0] if out else []


def dimension() -> Optional[int]:
    try:
        return _embedding_dim(_load())
    except Exception:
        return None
