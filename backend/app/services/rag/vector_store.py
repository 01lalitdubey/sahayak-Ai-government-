"""
Vector store — Sahayak AI RAG
==============================
Stores scheme chunks + all-MiniLM-L6-v2 embeddings and does cosine
similarity search. Two interchangeable backends, chosen by RAG_CHROMA_MODE:

  * "local"       — pure-Python NumPy store persisted to disk (default).
                    No native build, no server — works everywhere.
  * "persistent"  — chromadb.PersistentClient (needs the FULL `chromadb`
                    package with a compiled hnswlib).
  * "http"        — chromadb.HttpClient against a running Chroma server
                    (see the `chroma` service in docker-compose.yml).

All backends expose: count() · reset() · upsert(...) · query(vec, top_k).
Embeddings are L2-normalised upstream, so cosine == dot product.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.core.exceptions import RagServiceException
from app.core.logging import get_logger

logger = get_logger(__name__)

_lock = threading.Lock()
_backend: "_Backend | None" = None


@dataclass
class RetrievedChunk:
    scheme_id: str
    scheme_code: str
    scheme_name: str
    text: str
    similarity: float
    metadata: dict[str, Any]


# ── Backend protocol ───────────────────────────────────────────────────────
class _Backend:
    def count(self) -> int: ...  # pragma: no cover
    def reset(self) -> None: ...  # pragma: no cover
    def upsert(self, ids, embeddings, documents, metadatas) -> None: ...  # pragma: no cover
    def query(self, vec: list[float], top_k: int) -> list[RetrievedChunk]: ...  # pragma: no cover


# ── NumPy local backend ────────────────────────────────────────────────────
class _LocalBackend(_Backend):
    def __init__(self, path: str) -> None:
        self._dir = path
        os.makedirs(self._dir, exist_ok=True)
        self._file = os.path.join(self._dir, f"{settings.RAG_COLLECTION}.jsonl")
        self._ids: list[str] = []
        self._vecs: list[list[float]] = []
        self._docs: list[str] = []
        self._metas: list[dict[str, Any]] = []
        self._mtime: float = 0.0
        self._load()

    def _reload_if_stale(self) -> None:
        """Pick up writes made by another worker/process."""
        try:
            mt = os.path.getmtime(self._file)
        except OSError:
            return
        if mt != self._mtime:
            self._ids, self._vecs, self._docs, self._metas = [], [], [], []
            self._load()

    def _load(self) -> None:
        if not os.path.isfile(self._file):
            return
        try:
            self._mtime = os.path.getmtime(self._file)
            with open(self._file, "r", encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    self._ids.append(row["id"])
                    self._vecs.append(row["vec"])
                    self._docs.append(row["doc"])
                    self._metas.append(row["meta"])
            logger.info("Local vector store loaded: %d chunks", len(self._ids))
        except Exception as exc:  # noqa: BLE001
            logger.error("Local vector store load failed, starting empty: %s", exc)
            self._ids, self._vecs, self._docs, self._metas = [], [], [], []

    def _persist(self) -> None:
        tmp = self._file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            for i, _id in enumerate(self._ids):
                fh.write(json.dumps({
                    "id": _id, "vec": self._vecs[i],
                    "doc": self._docs[i], "meta": self._metas[i],
                }) + "\n")
        os.replace(tmp, self._file)
        try:
            self._mtime = os.path.getmtime(self._file)
        except OSError:
            pass

    def count(self) -> int:
        self._reload_if_stale()
        return len(self._ids)

    def reset(self) -> None:
        self._ids, self._vecs, self._docs, self._metas = [], [], [], []
        if os.path.isfile(self._file):
            os.remove(self._file)

    def upsert(self, ids, embeddings, documents, metadatas) -> None:
        index = {_id: n for n, _id in enumerate(self._ids)}
        for _id, vec, doc, meta in zip(ids, embeddings, documents, metadatas):
            if _id in index:
                n = index[_id]
                self._vecs[n], self._docs[n], self._metas[n] = list(vec), doc, meta
            else:
                index[_id] = len(self._ids)
                self._ids.append(_id)
                self._vecs.append(list(vec))
                self._docs.append(doc)
                self._metas.append(meta)
        self._persist()

    def query(self, vec: list[float], top_k: int) -> list[RetrievedChunk]:
        self._reload_if_stale()
        if not self._ids:
            return []
        import numpy as np

        mat = np.asarray(self._vecs, dtype=np.float32)
        q = np.asarray(vec, dtype=np.float32)
        qn = np.linalg.norm(q) or 1.0
        mn = np.linalg.norm(mat, axis=1)
        mn[mn == 0] = 1.0
        sims = (mat @ q) / (mn * qn)
        order = np.argsort(-sims)[: max(1, top_k)]
        out: list[RetrievedChunk] = []
        for n in order:
            meta = self._metas[n] or {}
            out.append(RetrievedChunk(
                scheme_id=str(meta.get("scheme_id", "")),
                scheme_code=str(meta.get("scheme_code", "")),
                scheme_name=str(meta.get("scheme_name", "")),
                text=self._docs[n] or "",
                similarity=round(float(sims[n]), 4),
                metadata=meta,
            ))
        return out


# ── Chroma backend ─────────────────────────────────────────────────────────
class _ChromaBackend(_Backend):
    def __init__(self, mode: str) -> None:
        try:
            import chromadb  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RagServiceException("chromadb is not installed.") from exc

        if mode == "http":
            logger.info("ChromaDB HTTP client → %s:%s",
                        settings.RAG_CHROMA_HOST, settings.RAG_CHROMA_PORT)
            self._client = chromadb.HttpClient(
                host=settings.RAG_CHROMA_HOST, port=settings.RAG_CHROMA_PORT
            )
        else:
            os.makedirs(settings.RAG_CHROMA_PATH, exist_ok=True)
            try:
                self._client = chromadb.PersistentClient(path=settings.RAG_CHROMA_PATH)
            except RuntimeError as exc:
                raise RagServiceException(
                    "Installed 'chromadb' is the HTTP-only client — it cannot use "
                    "persistent local storage. Use RAG_CHROMA_MODE=local, or "
                    "`pip install chromadb` (full), or run a Chroma server with "
                    "RAG_CHROMA_MODE=http."
                ) from exc
        self._col = self._client.get_or_create_collection(
            name=settings.RAG_COLLECTION, metadata={"hnsw:space": "cosine"}
        )

    def count(self) -> int:
        return self._col.count()

    def reset(self) -> None:
        try:
            self._client.delete_collection(self._col.name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("delete_collection: %s", exc)
        self._col = self._client.get_or_create_collection(
            name=settings.RAG_COLLECTION, metadata={"hnsw:space": "cosine"}
        )

    def upsert(self, ids, embeddings, documents, metadatas) -> None:
        self._col.upsert(ids=ids, embeddings=embeddings,
                         documents=documents, metadatas=metadatas)

    def query(self, vec: list[float], top_k: int) -> list[RetrievedChunk]:
        if self._col.count() == 0:
            return []
        res = self._col.query(
            query_embeddings=[vec], n_results=max(1, top_k),
            include=["documents", "metadatas", "distances"],
        )
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        out: list[RetrievedChunk] = []
        for doc, meta, dist in zip(docs, metas, dists):
            meta = meta or {}
            out.append(RetrievedChunk(
                scheme_id=str(meta.get("scheme_id", "")),
                scheme_code=str(meta.get("scheme_code", "")),
                scheme_name=str(meta.get("scheme_name", "")),
                text=doc or "",
                similarity=round(1.0 - float(dist), 4) if dist is not None else 0.0,
                metadata=meta,
            ))
        return out


# ── Factory + module-level API ────────────────────────────────────────────
def _get() -> _Backend:
    global _backend
    if _backend is not None:
        return _backend
    with _lock:
        if _backend is not None:
            return _backend
        mode = (settings.RAG_CHROMA_MODE or "local").lower()
        if mode in ("local", "numpy", "memory"):
            _backend = _LocalBackend(settings.RAG_CHROMA_PATH)
        elif mode in ("persistent", "http"):
            _backend = _ChromaBackend(mode)
        else:
            logger.warning("Unknown RAG_CHROMA_MODE=%r, using 'local'", mode)
            _backend = _LocalBackend(settings.RAG_CHROMA_PATH)
        return _backend


def _reset_singleton() -> None:  # for tests
    global _backend
    _backend = None


def count() -> int:
    try:
        return _get().count()
    except RagServiceException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("vector_store.count failed: %s", exc)
        return 0


def reset() -> None:
    _get().reset()


def upsert(ids: list[str], embeddings: list[list[float]],
           documents: list[str], metadatas: list[dict[str, Any]]) -> None:
    if not ids:
        return
    _get().upsert(ids, embeddings, documents, metadatas)


def query(query_embedding: list[float], *, top_k: int) -> list[RetrievedChunk]:
    return _get().query(query_embedding, top_k)
