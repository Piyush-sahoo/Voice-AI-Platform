"""Local embedding utilities for Knowledge Base ingestion and retrieval."""
from typing import List
from threading import Lock
import logging

logger = logging.getLogger("embeddings")

_MODEL = None
_MODEL_LOCK = Lock()

MODEL_NAME = "BAAI/bge-small-en-v1.5"


def _get_model():
    global _MODEL

    if _MODEL is None:
        with _MODEL_LOCK:
            if _MODEL is None:
                from sentence_transformers import SentenceTransformer
                logger.info("Lazy loading embedding model...")
                _MODEL = SentenceTransformer(MODEL_NAME, device="cpu")
                logger.info("Embedding model loaded successfully.")

    return _MODEL


def embed_text(text: str) -> List[float]:
    model = _get_model()
    vector = model.encode(
        text,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return vector.tolist()


def embed_batch(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []

    model = _get_model()
    vectors = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return vectors.tolist()
