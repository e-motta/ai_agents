from functools import lru_cache
import os
from openai import OpenAI


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """Get or initialize the OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    return OpenAI(api_key=api_key)
