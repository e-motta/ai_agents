"""
Comprehensive pytest tests for the math_agent module.
"""

import os
import pytest
from unittest.mock import Mock, patch
from app.agents.math_agent import solve_math


class TestSolveMath:
    """Test the main solve_math function."""

    def test_successful_solve_math(self):
        """Test successful solve_math execution."""
        mock_response = Mock()
        mock_response.content = "5"
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response

        result = solve_math("2 + 3", mock_llm)
        assert result == "5"


    def test_solve_math_llm_error(self):
        """Test solve_math when LLM raises an error."""
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("Network error")

        with pytest.raises(ValueError, match="Network error"):
            solve_math("2 + 3", mock_llm)

    def test_solve_math_various_expressions(self):
        """Test solve_math with various mathematical expressions."""
        test_cases = [
            ("2 + 3", "5"),
            ("10 * 5", "50"),
            ("sqrt(16)", "4"),
            ("2^3", "8"),
            ("15 / 3 + 7", "12"),
            ("2 * (3 + 4)", "14"),
        ]

        for query, expected in test_cases:
            mock_response = Mock()
            mock_response.content = expected
            mock_llm = Mock()
            mock_llm.invoke.return_value = mock_response

            result = solve_math(query, mock_llm)
            assert result == expected

    def test_calculation_with_answer_prefix(self):
        """Test calculation when LLM returns 'Answer: X' format."""
        mock_response = Mock()
        mock_response.content = "Answer: 10"
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response

        with pytest.raises(ValueError, match="LLM returned a non-numerical result"):
            solve_math("5 * 2", mock_llm)

    def test_calculation_with_negative_number(self):
        """Test calculation with negative numbers."""
        mock_response = Mock()
        mock_response.content = "The result is -5"
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response

        # The current implementation expects only numeric results
        with pytest.raises(ValueError, match="LLM returned a non-numerical result"):
            solve_math("2 - 7", mock_llm)

    def test_calculation_with_decimal_number(self):
        """Test calculation with decimal numbers."""
        mock_response = Mock()
        mock_response.content = "3.14159"
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response

        result = solve_math("pi", mock_llm)
        assert result == "3.14159"

    def test_invalid_expression_error(self):
        """Test handling of invalid mathematical expressions."""
        mock_response = Mock()
        mock_response.content = "Error"
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response

        with pytest.raises(ValueError, match="Could not evaluate the expression"):
            solve_math("invalid expression", mock_llm)

    def test_empty_response_handling(self):
        """Test handling of empty LLM response."""
        mock_response = Mock()
        mock_response.content = ""
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response

        with pytest.raises(ValueError, match="Could not evaluate the expression"):
            solve_math("2 + 3", mock_llm)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_expression(self):
        """Test with a very long mathematical expression."""
        long_expression = "1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10"
        mock_response = Mock()
        mock_response.content = "55"
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response

        result = solve_math(long_expression, mock_llm)
        assert result == "55"

    def test_expression_with_special_characters(self):
        """Test expression with special characters that are safe."""
        mock_response = Mock()
        mock_response.content = "3.14159"
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response

        result = solve_math("π", mock_llm)
        assert result == "3.14159"


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_empty_query(self):
        """Test with empty query."""
        mock_llm = Mock()
        with pytest.raises(ValueError):
            solve_math("", mock_llm)

    def test_none_query(self):
        """Test with None query."""
        mock_llm = Mock()
        with pytest.raises((TypeError, ValueError)):
            solve_math(None, mock_llm)

    def test_llm_timeout_error(self):
        """Test handling of LLM timeout errors."""
        mock_llm = Mock()
        mock_llm.invoke.side_effect = TimeoutError("Request timed out")

        with pytest.raises(ValueError, match="Request timed out"):
            solve_math("2 + 3", mock_llm)

    def test_llm_rate_limit_error(self):
        """Test handling of LLM rate limit errors."""
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("Rate limit exceeded")

        with pytest.raises(ValueError, match="Rate limit exceeded"):
            solve_math("2 + 3", mock_llm)
