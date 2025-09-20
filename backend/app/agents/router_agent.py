"""
Router Agent module for classifying user queries between MathAgent and KnowledgeAgent.

This module provides a function to route user queries to the appropriate agent
based on the query content using an LLM classifier.
"""

import logging

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from app.security.prompts import ROUTER_SYSTEM_PROMPT
from app.enums import ResponseEnum


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _validate_response(response: str) -> str:
    """
    Validate and clean the LLM response.

    Args:
        response: Raw response from the LLM

    Returns:
        Cleaned response ("MathAgent", "KnowledgeAgent", "UnsupportedLanguage", or "Error")
    """
    # Clean the response
    cleaned_response = response.strip().lower()

    # Mapping of keywords to canonical agent names
    response_map = {
        "mathagent": ResponseEnum.MathAgent,
        "knowledgeagent": ResponseEnum.KnowledgeAgent,
        "unsupportedlanguage": ResponseEnum.UnsupportedLanguage,
        "error": ResponseEnum.Error,
    }

    for key, value in response_map.items():
        if key in cleaned_response:
            return value

    # Default to Error for safety
    logger.warning(f"Invalid response from router: {response}. Defaulting to Error.")
    return ResponseEnum.Error


def _detect_suspicious_content(query: str) -> bool:
    """
    Detect potentially suspicious or malicious content in the query.

    Args:
        query: User query to analyze

    Returns:
        True if suspicious content is detected, False otherwise
    """
    suspicious_patterns = [
        "ignore previous instructions",
        "forget everything",
        "system prompt",
        "you are now",
        "act as",
        "pretend to be",
        "roleplay",
        "jailbreak",
        "developer mode",
        "admin mode",
        "override",
        "bypass",
        "exploit",
        "hack",
        "inject",
        "execute",
        "run command",
        "system call",
        "file://",
        "http://",
        "https://",
        "<script>",
        "javascript:",
        "data:",
        "eval(",
        "exec(",
        "import os",
        "subprocess",
        "shell",
        "terminal",
        "command line",
        "prompt injection",
        "llm injection",
        # Portuguese patterns
        "ignore as instruções anteriores",
        "esqueça tudo",
        "prompt do sistema",
        "você agora é",
        "aja como",
        "finja ser",
        "interprete o papel de",
    ]

    query_lower = query.lower()

    for pattern in suspicious_patterns:
        if pattern in query_lower:
            logger.warning(f"Suspicious content detected in query: {pattern}")
            return True

    return False


def route_query(query: str, llm: ChatOpenAI) -> str:
    """
    Route a user query to the appropriate agent or return error status.

    Args:
        query: The user's query string
        llm: ChatOpenAI LLM instance to use for routing

    Returns:
        str: Either "MathAgent", "KnowledgeAgent", "UnsupportedLanguage", or "Error"

    Raises:
        ValueError: If the query is empty or if there's an error processing the query
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    # Clean the query
    cleaned_query = query.strip()

    # Check for suspicious content
    if _detect_suspicious_content(cleaned_query):
        logger.warning(
            "Suspicious content detected, returning KnowledgeAgent for safety"
        )
        return ResponseEnum.KnowledgeAgent

    try:
        logger.info(f"Routing query: {cleaned_query[:100]}...")

        # Create messages
        messages = [
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(content=f'Query: "{cleaned_query}"'),
        ]

        # Get response from LLM
        response = llm.invoke(messages)

        # Handle different response formats
        if isinstance(response.content, list):
            response_text = " ".join(str(item) for item in response.content).strip()
        else:
            response_text = response.content.strip()

        logger.info(f"Router response: {response_text}")

        # Validate and return the cleaned response
        return _validate_response(response_text)

    except Exception as e:
        logger.error(f"Error routing query: {str(e)}")
        # Default to Error for safety
        return ResponseEnum.Error
