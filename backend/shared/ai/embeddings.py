"""Embedding helpers for RAG ingestion and retrieval."""
import logging
from typing import List
from google import genai
from shared.settings import config

logger = logging.getLogger("ai.embeddings")

if not config.GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is required for Gemini embeddings")

client = genai.Client(
    api_key=config.GOOGLE_API_KEY,
    http_options={"api_version": "v1"},  # text-embedding-004 is only on stable v1, not v1beta
)

async def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []

    response = client.models.embed_content(
        model="text-embedding-004",
        contents=texts,
    )

    if not response or not hasattr(response, "embeddings"):
        raise ValueError("Invalid embedding response from Gemini")

    embeddings = []
    for item in response.embeddings:
        if hasattr(item, "values") and item.values:
            embeddings.append(item.values)
        else:
            raise ValueError("Empty embedding vector returned from Gemini")

    return embeddings