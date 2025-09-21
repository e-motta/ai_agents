from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from langchain_openai import ChatOpenAI
from llama_index.core.base.base_query_engine import BaseQueryEngine

from app.core.llm import (
    get_math_agent_llm,
    get_router_agent_llm,
)
from app.agents.knowledge_agent import get_query_engine
from app.security.sanitization import sanitize_user_input
from app.models import ChatRequest


@lru_cache(maxsize=1)
def get_math_llm() -> ChatOpenAI:
    """
    Dependency: return a cached instance of the math LLM.

    Uses LRU cache to ensure the expensive client is created once
    per process and reused across requests.
    """
    return get_math_agent_llm()


@lru_cache(maxsize=1)
def get_router_llm() -> ChatOpenAI:
    """
    Dependency: return a cached instance of the router LLM.

    Uses LRU cache to ensure the expensive client is created once
    per process and reused across requests.
    """
    return get_router_agent_llm()


@lru_cache(maxsize=1)
def get_knowledge_engine() -> BaseQueryEngine:
    """
    Dependency: return a cached instance of the query engine.

    Uses LRU cache to ensure the expensive client is created once
    per process and reused across requests.
    """
    return get_query_engine()


def get_sanitized_message_from_request(payload: "ChatRequest") -> str:
    """
    Dependency: extract and sanitize the message from ChatRequest.

    Args:
        payload: The ChatRequest object

    Returns:
        str: The sanitized message
    """
    return sanitize_user_input(payload.message)


# Type alias for dependency injection
SanitizedMessage = Annotated[str, Depends(get_sanitized_message_from_request)]
