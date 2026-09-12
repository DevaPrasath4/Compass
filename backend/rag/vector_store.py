from __future__ import annotations

import os
from typing import Any

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency may be unavailable in minimal envs
    SentenceTransformer = None

try:
    import chromadb
except Exception:
    chromadb = None

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "rag", "chroma_db")
os.makedirs(DB_PATH, exist_ok=True)

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        if SentenceTransformer is None:
            return None
        try:
            _MODEL = SentenceTransformer(_MODEL_NAME)
        except Exception:
            _MODEL = None
    return _MODEL


def _get_client():
    if chromadb is None:
        return None
    try:
        return chromadb.PersistentClient(path=DB_PATH)
    except Exception:
        return None


def _collection(collection_name: str):
    client = _get_client()
    if client is None:
        return None
    try:
        return client.get_or_create_collection(name=collection_name)
    except Exception:
        return None


def upsert_documents(collection_name: str, docs: list[dict]) -> None:
    model = _get_model()
    collection = _collection(collection_name)
    if model is None or collection is None or not docs:
        return
    texts = [str(item.get("text") or "") for item in docs]
    ids = [str(item.get("id") or idx) for idx, item in enumerate(docs)]
    metadata = [{k: v for k, v in item.items() if k not in {"text", "id"}} for item in docs]
    embeddings = model.encode(texts, convert_to_numpy=True).tolist()
    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadata,
    )


def semantic_retrieve(query: str, k: int = 3, collection_name: str = "campus_kb") -> list[dict]:
    model = _get_model()
    collection = _collection(collection_name)
    if model is None or collection is None or not (query or "").strip():
        return []
    try:
        embeddings = model.encode([query], convert_to_numpy=True).tolist()
        results = collection.query(query_embeddings=embeddings, n_results=k, include=["documents", "metadatas", "distances"])
        items = []
        for i in range(len(results.get("documents", [[]])[0])):
            document = results["documents"][0][i]
            meta = (results.get("metadatas", [[{}]])[0][i] or {})
            dist = (results.get("distances", [[0.0]])[0][i] if results.get("distances") else 0.0)
            items.append({
                "text": document,
                "score": float(1.0 - min(max(dist, 0.0), 1.0)),
                **meta,
            })
        return items
    except Exception:
        return []


def search_collection(query: str, collection_name: str = "complaints", k: int = 5) -> list[dict]:
    return semantic_retrieve(query, k=k, collection_name=collection_name)
