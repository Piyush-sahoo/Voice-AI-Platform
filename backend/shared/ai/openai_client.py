"""Shared OpenAI client factory."""
from functools import lru_cache

from openai import AsyncOpenAI

from shared.settings import config


@lru_cache(maxsize=1)
def get_openai_client() -> AsyncOpenAI:
    """Return a singleton AsyncOpenAI client using shared config."""
    return AsyncOpenAI(api_key=config.OPENAI_API_KEY)
