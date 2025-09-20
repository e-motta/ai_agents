from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings using Pydantic v2.

    Environment variables are parsed via pydantic-settings. Defaults are provided
    for non-secret values. Secret values can be omitted in local/dev and are
    validated via helper methods when needed.
    """

    model_config = SettingsConfigDict(
        env_prefix="", case_sensitive=True, extra="ignore"
    )

    # Secrets / API keys
    OPENAI_API_KEY: Optional[SecretStr] = None

    # LLM defaults
    LLM_MODEL: str = "gpt-3.5-turbo"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHUNK_SIZE: int = 1024
    CHUNK_OVERLAP: int = 20

    # Knowledge agent configuration
    VECTOR_STORE_PATH: Path = Path(__file__).parent.parent.parent / "vector_store"
    BASE_URL: str = "https://ajuda.infinitepay.io/pt-BR/"
    COLLECTION_NAME: str = "infinitepay_docs"

    # Request headers
    REQUEST_HEADERS_USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )

    @property
    def REQUEST_HEADERS(self) -> Dict[str, str]:
        return {"User-Agent": self.REQUEST_HEADERS_USER_AGENT}

    # Helpers
    def ensure_openai_api_key(self) -> str:
        """Return the OpenAI API key or raise a clear error if missing.

        We intentionally keep the error message compatible with prior code/tests.
        """
        if (
            self.OPENAI_API_KEY is None
            or self.OPENAI_API_KEY.get_secret_value().strip() == ""
        ):
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return self.OPENAI_API_KEY.get_secret_value()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()  # type: ignore[attr-defined]
