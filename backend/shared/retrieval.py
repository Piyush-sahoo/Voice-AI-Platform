"""Qdrant-backed retrieval helpers for Knowledge Base RAG."""
import logging
import time
from typing import Dict, List

from qdrant_client import QdrantClient
from qdrant_client.http import models

from shared.embeddings import embed_text
from shared.settings import config

logger = logging.getLogger("kb.retrieval")

QDRANT_URL = config.QDRANT_URL
COLLECTION_NAME = "knowledge_base"
VECTOR_SIZE = 384

_qdrant_client: QdrantClient | None = None
_collection_ready = False


def _get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(url=QDRANT_URL)
    return _qdrant_client


def _ensure_collection() -> None:
    global _collection_ready
    if _collection_ready:
        return

    client = _get_qdrant_client()
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE,
            ),
        )

    _collection_ready = True


def delete_document_vectors(document_id: str) -> None:
    _ensure_collection()
    client = _get_qdrant_client()
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=document_id),
                    )
                ]
            )
        ),
        wait=True,
    )


def upsert_points(points: List[models.PointStruct]) -> None:
    if not points:
        return

    _ensure_collection()
    client = _get_qdrant_client()
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
        wait=True,
    )


def retrieve_context(
    assistant_id: str,
    user_id: str,
    query: str,
    top_k: int = 5,
    threshold: float = 0.75
) -> str:
    start = time.perf_counter()
    top_score = 0.0

    try:
        if not assistant_id or not user_id or not query.strip():
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info("retrieval_time=%.2fms top_score=%.4f rag_applied=false", elapsed_ms, top_score)
            return ""

        _ensure_collection()
        client = _get_qdrant_client()

        query_vector = embed_text(query)

        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="assistant_id",
                        match=models.MatchValue(value=assistant_id),
                    ),
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id),
                    ),
                ]
            ),
            limit=top_k,
            with_payload=True,
        )

        if not results:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info("retrieval_time=%.2fms top_score=%.4f rag_applied=false", elapsed_ms, top_score)
            return ""

        top_score = float(results[0].score or 0.0)
        if top_score < threshold:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info("retrieval_time=%.2fms top_score=%.4f rag_applied=false", elapsed_ms, top_score)
            return ""

        lines: List[str] = []
        for idx, hit in enumerate(results, start=1):
            payload: Dict = hit.payload or {}
            text = str(payload.get("text") or "").strip()
            if text:
                lines.append(f"{idx}. {text}")

        if not lines:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info("retrieval_time=%.2fms top_score=%.4f rag_applied=false", elapsed_ms, top_score)
            return ""

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info("retrieval_time=%.2fms top_score=%.4f rag_applied=true", elapsed_ms, top_score)
        return "Relevant Knowledge:\n" + "\n".join(lines)

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.warning(
            "retrieval_time=%.2fms top_score=%.4f rag_applied=false error=%s",
            elapsed_ms,
            top_score,
            str(exc),
        )
        return ""
