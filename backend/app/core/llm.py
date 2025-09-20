"""
Centralized LLM factory functions for all agents.

This module provides factory functions to create LLM instances consistently
across all agents, ensuring uniform configuration and easy maintenance.
"""

import os
from functools import lru_cache
from typing import Optional

from langchain_openai import ChatOpenAI
from llama_index.llms.openai import OpenAI as LlamaIndexOpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core import Settings
from openai import OpenAI


def get_chat_openai_llm(
    model: str = "gpt-3.5-turbo", temperature: float = 0, api_key: Optional[str] = None
) -> ChatOpenAI:
    """
    Create a ChatOpenAI instance for LangChain agents.

    Args:
        model: The OpenAI model to use
        temperature: Temperature for response generation
        api_key: OpenAI API key (if not provided, will use environment variable)

    Returns:
        ChatOpenAI instance configured for the agent
    """
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

    return ChatOpenAI(model=model, temperature=temperature, api_key=api_key)


def setup_llamaindex_settings(
    llm_model: str = "gpt-3.5-turbo",
    embedding_model: str = "text-embedding-3-small",
    chunk_size: int = 1024,
    chunk_overlap: int = 20,
    api_key: Optional[str] = None,
) -> None:
    """
    Setup LlamaIndex global settings for LLM and embeddings.

    Args:
        llm_model: The OpenAI model to use for LLM
        embedding_model: The OpenAI model to use for embeddings
        chunk_size: Size of text chunks for processing
        chunk_overlap: Overlap between chunks
        api_key: OpenAI API key (if not provided, will use environment variable)
    """
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

    # Configure LlamaIndex settings
    Settings.llm = LlamaIndexOpenAI(model=llm_model, temperature=0, api_key=api_key)
    Settings.embed_model = OpenAIEmbedding(model=embedding_model, api_key=api_key)
    Settings.node_parser = SimpleNodeParser.from_defaults(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )


# Convenience functions for common configurations
def get_math_agent_llm() -> ChatOpenAI:
    """Get ChatOpenAI LLM configured for math agent."""
    return get_chat_openai_llm(model="gpt-3.5-turbo", temperature=0)


def get_router_agent_llm() -> ChatOpenAI:
    """Get ChatOpenAI LLM configured for router agent."""
    return get_chat_openai_llm(model="gpt-3.5-turbo", temperature=0)


def setup_knowledge_agent_settings() -> None:
    """Setup LlamaIndex settings for knowledge agent."""
    setup_llamaindex_settings(
        llm_model="gpt-3.5-turbo",
        embedding_model="text-embedding-3-small",
        chunk_size=1024,
        chunk_overlap=20,
    )
