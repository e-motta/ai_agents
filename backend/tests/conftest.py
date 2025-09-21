"""
Test configuration and fixtures for the FastAPI application.

This module provides test fixtures and configuration to ensure tests run
without making external calls or warming up expensive resources.
"""

import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from langchain_openai import ChatOpenAI
from llama_index.core.base.base_query_engine import BaseQueryEngine

from app.main import app
from app.dependencies import get_math_llm, get_router_llm, get_knowledge_engine


@pytest.fixture
def mock_llm():
    """Create a mock ChatOpenAI instance for testing."""
    mock = AsyncMock(spec=ChatOpenAI)
    return mock


@pytest.fixture
def mock_knowledge_engine():
    """Create a mock BaseQueryEngine instance for testing."""
    mock = AsyncMock(spec=BaseQueryEngine)
    return mock


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_dependencies(mock_llm, mock_knowledge_engine):
    """
    Automatically mock all dependencies to prevent external calls.

    This fixture runs automatically for all tests and ensures that:
    - LLM instances are mocked
    - Knowledge engine is mocked
    - No external API calls are made
    """
    # Mock the dependency functions
    app.dependency_overrides[get_math_llm] = lambda: mock_llm
    app.dependency_overrides[get_router_llm] = lambda: mock_llm
    app.dependency_overrides[get_knowledge_engine] = lambda: mock_knowledge_engine

    yield

    # Clean up after test
    app.dependency_overrides.clear()


@pytest.fixture
def sample_chat_request():
    """Create a sample ChatRequest for testing."""
    return {
        "message": "What is 2 + 2?",
        "user_id": "test_user_123",
        "conversation_id": "test_conv_456",
    }


@pytest.fixture
def sample_math_query():
    """Create a sample math query for testing."""
    return "2 + 2"


@pytest.fixture
def sample_knowledge_query():
    """Create a sample knowledge query for testing."""
    return "What are the fees for the payment terminal?"
