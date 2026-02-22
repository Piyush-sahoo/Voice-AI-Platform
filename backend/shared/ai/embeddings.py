"""Embedding helpers for RAG ingestion and retrieval."""
import asyncio
import logging
from typing import List

import google.generativeai as genai

from shared.settings import config

logger = logging.getLogger("ai.embeddings")


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts using Gemini embedding model."""
    if not texts:
        return []

    if not config.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is required for Gemini embeddings")

    genai.configure(api_key=config.GOOGLE_API_KEY)

    def _embed_single(text: str) -> List[float]:
        response = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document",
        )
        return response["embedding"]

    embeddings = await asyncio.gather(*[asyncio.to_thread(_embed_single, text) for text in texts])

    logger.debug("Generated %s embeddings", len(embeddings))
    return embeddings
