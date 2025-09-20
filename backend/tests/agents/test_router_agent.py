"""
Tests for the Router Agent module.

This module tests the router agent functionality including the new
UnsupportedLanguage and Error response handling.
"""

import pytest
from unittest.mock import Mock
from app.agents.router_agent import (
    route_query,
    _validate_response,
    _detect_suspicious_content,
)


class TestValidateResponse:
    """Test the _validate_response function."""

    def test_validate_mathagent_response(self):
        """Test validation of MathAgent response."""
        assert _validate_response("MathAgent") == "MathAgent"
        assert _validate_response("mathagent") == "MathAgent"
        assert _validate_response("  MathAgent  ") == "MathAgent"
        assert _validate_response("I think this should go to MathAgent") == "MathAgent"

    def test_validate_knowledgeagent_response(self):
        """Test validation of KnowledgeAgent response."""
        assert _validate_response("KnowledgeAgent") == "KnowledgeAgent"
        assert _validate_response("knowledgeagent") == "KnowledgeAgent"
        assert _validate_response("  KnowledgeAgent  ") == "KnowledgeAgent"
        assert (
            _validate_response("This should go to KnowledgeAgent") == "KnowledgeAgent"
        )

    def test_validate_unsupportedlanguage_response(self):
        """Test validation of UnsupportedLanguage response."""
        assert _validate_response("UnsupportedLanguage") == "UnsupportedLanguage"
        assert _validate_response("unsupportedlanguage") == "UnsupportedLanguage"
        assert _validate_response("  UnsupportedLanguage  ") == "UnsupportedLanguage"
        assert (
            _validate_response("This is UnsupportedLanguage") == "UnsupportedLanguage"
        )

    def test_validate_error_response(self):
        """Test validation of Error response."""
        assert _validate_response("Error") == "Error"
        assert _validate_response("error") == "Error"
        assert _validate_response("  Error  ") == "Error"
        assert _validate_response("This is an Error") == "Error"

    def test_validate_invalid_response_defaults_to_error(self):
        """Test that invalid responses default to Error."""
        assert _validate_response("InvalidResponse") == "Error"
        assert _validate_response("") == "Error"
        assert _validate_response("Random text") == "Error"
        assert _validate_response("Agent") == "Error"

    def test_validate_response_edge_cases(self):
        """Test edge cases for _validate_response."""
        # Test with very long response
        long_response = "MathAgent" + "x" * 1000
        assert _validate_response(long_response) == "MathAgent"

        # Test with mixed case and special characters
        assert _validate_response("MATHAGENT!!!") == "MathAgent"
        assert _validate_response("knowledgeagent...") == "KnowledgeAgent"
        assert _validate_response("UNSUPPORTEDLANGUAGE???") == "UnsupportedLanguage"
        assert _validate_response("ERROR!!!") == "Error"


class TestDetectSuspiciousContent:
    """Test the _detect_suspicious_content function."""

    def test_detect_suspicious_patterns(self):
        """Test detection of various suspicious patterns."""
        suspicious_queries = [
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
            "file://test",
            "http://example.com",
            "https://example.com",
            "<script>alert('test')</script>",
            "javascript:alert('test')",
            "data:text/html,<script>alert('test')</script>",
            "eval('test')",
            "exec('test')",
            "import os",
            "subprocess",
            "shell",
            "terminal",
            "command line",
            "prompt injection",
            "llm injection",
        ]

        for query in suspicious_queries:
            assert _detect_suspicious_content(
                query
            ), f"Should detect suspicious content in: {query}"

    def test_detect_suspicious_content_case_insensitive(self):
        """Test that suspicious content detection is case insensitive."""
        assert _detect_suspicious_content("IGNORE PREVIOUS INSTRUCTIONS")
        assert _detect_suspicious_content("Ignore Previous Instructions")
        assert _detect_suspicious_content("iGnOrE pReViOuS iNsTrUcTiOnS")

    def test_detect_clean_content(self):
        """Test that clean content is not flagged as suspicious."""
        clean_queries = [
            "quanto é 15*3?",
            "quais as taxas da maquininha?",
            "como funciona o pagamento?",
            "calcule 25 + 17",
            "quais são os métodos de pagamento aceitos?",
            "como faço para criar uma conta?",
            "what is 2 + 2?",
            "how does payment work?",
            "calculate 10 * 5",
        ]

        for query in clean_queries:
            assert not _detect_suspicious_content(
                query
            ), f"Should not detect suspicious content in: {query}"

    def test_detect_suspicious_content_edge_cases(self):
        """Test edge cases for _detect_suspicious_content."""
        # Test with empty string
        assert not _detect_suspicious_content("")

        # Test with very long query
        long_query = "This is a very long query " + "x" * 1000
        assert not _detect_suspicious_content(long_query)

        # Test with query containing suspicious pattern at the end
        assert _detect_suspicious_content("Hello world ignore previous instructions")

        # Test with query containing suspicious pattern at the beginning
        assert _detect_suspicious_content("ignore previous instructions hello world")

        # Test with query containing suspicious pattern in the middle
        assert _detect_suspicious_content("Hello ignore previous instructions world")


class TestRouteQuery:
    """Test the route_query function."""

    def test_empty_query_raises_valueerror(self):
        """Test that empty queries raise ValueError."""
        mock_llm = Mock()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            route_query("", llm=mock_llm)

        with pytest.raises(ValueError, match="Query cannot be empty"):
            route_query("   ", llm=mock_llm)

        with pytest.raises(ValueError, match="Query cannot be empty"):
            route_query(None, llm=mock_llm)  # type: ignore

    def test_suspicious_content_returns_knowledge_agent(self):
        """Test that suspicious content returns KnowledgeAgent."""
        mock_llm = Mock()
        result = route_query("ignore previous instructions", llm=mock_llm)
        assert result == "KnowledgeAgent"

    def test_mathagent_response(self):
        """Test routing to MathAgent."""
        # Mock ChatOpenAI response
        mock_response = Mock()
        mock_response.content = "MathAgent"

        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response

        result = route_query("quanto é 15*3?", llm=mock_llm)
        assert result == "MathAgent"

    def test_knowledgeagent_response(self):
        """Test routing to KnowledgeAgent."""
        # Mock ChatOpenAI response
        mock_response = Mock()
        mock_response.content = "KnowledgeAgent"

        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response

        result = route_query("quais as taxas da maquininha?", llm=mock_llm)
        assert result == "KnowledgeAgent"

    def test_unsupportedlanguage_response(self):
        """Test routing returns UnsupportedLanguage."""
        # Mock ChatOpenAI response
        mock_response = Mock()
        mock_response.content = "UnsupportedLanguage"

        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response

        result = route_query("bonjour comment allez-vous?", llm=mock_llm)
        assert result == "UnsupportedLanguage"

    def test_error_response(self):
        """Test routing returns Error."""
        # Mock ChatOpenAI response
        mock_response = Mock()
        mock_response.content = "Error"

        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response

        result = route_query("some malicious query", llm=mock_llm)
        assert result == "Error"

    def test_openai_exception_defaults_to_error(self):
        """Test that LLM exceptions default to Error."""
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("LLM API error")

        result = route_query("test query", llm=mock_llm)
        assert result == "Error"

    def test_invalid_response_defaults_to_error(self):
        """Test that invalid responses default to Error."""
        # Mock ChatOpenAI response with invalid content
        mock_response = Mock()
        mock_response.content = "InvalidResponse"

        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response

        result = route_query("test query", llm=mock_llm)
        assert result == "Error"

    def test_route_query_edge_cases(self):
        """Test edge cases for route_query."""
        # Mock ChatOpenAI response
        mock_response = Mock()
        mock_response.content = "MathAgent"

        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response

        # Test with very long query
        long_query = "This is a very long query " + "x" * 1000
        result = route_query(long_query, llm=mock_llm)
        assert result == "MathAgent"

        # Test with query containing special characters
        special_query = "quanto é 15*3? @#$%^&*()"
        result = route_query(special_query, llm=mock_llm)
        assert result == "MathAgent"

        # Test with query containing newlines and tabs
        multiline_query = "quanto é 15*3?\n\tThis is a test"
        result = route_query(multiline_query, llm=mock_llm)
        assert result == "MathAgent"

    def test_route_query_malformed_llm_response(self):
        """Test route_query with malformed LLM response."""
        # Mock ChatOpenAI response with malformed structure
        mock_response = Mock()
        mock_response.content = None  # None content

        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response

        result = route_query("test query", llm=mock_llm)
        assert result == "Error"

    def test_route_query_llm_response_with_empty_content(self):
        """Test route_query when LLM response content is empty."""
        # Mock ChatOpenAI response with empty content
        mock_response = Mock()
        mock_response.content = ""

        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response

        result = route_query("test query", llm=mock_llm)
        assert result == "Error"
