from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.agents.knowledge_agent import initialize_knowledge_agent
from app.core.llm import (
    get_math_agent_llm,
    get_router_agent_llm,
)


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
def initialize_knowledge() -> bool:
    """
    Dependency: ensure the knowledge agent is initialized once and cached.

    Returns True if initialized. The boolean return is a lightweight sentinel
    that can be injected to guarantee initialization side-effect.
    """
    initialize_knowledge_agent()
    return True
