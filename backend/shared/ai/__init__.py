"""Shared AI clients and helpers."""

from .openai_client import get_openai_client
from .embeddings import embed_texts

__all__ = ["get_openai_client", "embed_texts"]
