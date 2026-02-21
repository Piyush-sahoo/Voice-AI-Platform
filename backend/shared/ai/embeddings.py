"""Embedding helpers for RAG ingestion and retrieval."""
import logging
from typing import List

from .openai_client import get_openai_client

logger = logging.getLogger("ai.embeddings")


async def embed_texts(texts: List[str], batch_size: int = 50) -> List[List[float]]:
    """Embed a list of texts using OpenAI with internal batching."""
    if not texts:
        return []

    client = get_openai_client()
    embeddings: List[List[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=batch,
        )
        embeddings.extend([item.embedding for item in response.data])

    logger.debug("Generated %s embeddings", len(embeddings))
    return embeddings
