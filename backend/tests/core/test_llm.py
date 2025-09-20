"""
Comprehensive tests for the core LLM factory functions.

This module tests all the LLM factory functions in app.core.llm to ensure
they create properly configured instances and handle errors appropriately.
"""

import os
import pytest
from unittest.mock import Mock, patch
from llama_index.core import Settings

from app.core.llm import (
    get_chat_openai_llm,
    setup_llamaindex_settings,
    get_math_agent_llm,
    get_router_agent_llm,
    setup_knowledge_agent_settings,
)
from app.core.settings import reset_settings_cache


class TestGetChatOpenAILlm:
    """Test the get_chat_openai_llm function."""

    @patch("app.core.llm.ChatOpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"})
    def test_get_chat_openai_llm_with_custom_model_and_temperature(
        self, mock_chat_openai
    ):
        """Test creating ChatOpenAI with custom model and temperature (env provides key)."""
        reset_settings_cache()
        mock_instance = Mock()
        mock_chat_openai.return_value = mock_instance

        result = get_chat_openai_llm(model="gpt-4", temperature=0.5)

        assert result == mock_instance
        mock_chat_openai.assert_called_once_with(model="gpt-4", temperature=0.5)

    @patch("app.core.llm.ChatOpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"})
    def test_get_chat_openai_llm_with_env_key(self, mock_chat_openai):
        """Test creating ChatOpenAI with environment API key."""
        reset_settings_cache()
        mock_instance = Mock()
        mock_chat_openai.return_value = mock_instance

        result = get_chat_openai_llm(model="gpt-3.5-turbo", temperature=0)

        assert result == mock_instance
        mock_chat_openai.assert_called_once_with(model="gpt-3.5-turbo", temperature=0)

    @patch.dict("os.environ", {}, clear=True)
    def test_get_chat_openai_llm_missing_api_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        reset_settings_cache()
        with pytest.raises(
            ValueError, match="OPENAI_API_KEY environment variable is required"
        ):
            get_chat_openai_llm()

    @patch("app.core.llm.ChatOpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"})
    def test_get_chat_openai_llm_default_parameters(self, mock_chat_openai):
        """Test creating ChatOpenAI with default parameters (env provides key)."""
        reset_settings_cache()
        mock_instance = Mock()
        mock_chat_openai.return_value = mock_instance

        result = get_chat_openai_llm()

        assert result == mock_instance
        mock_chat_openai.assert_called_once_with(model="gpt-3.5-turbo", temperature=0)

    @patch("app.core.llm.ChatOpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"})
    def test_get_chat_openai_llm_custom_model_and_temperature(self, mock_chat_openai):
        """Test creating ChatOpenAI with custom model and temperature (env provides key)."""
        reset_settings_cache()
        mock_instance = Mock()
        mock_chat_openai.return_value = mock_instance

        result = get_chat_openai_llm(model="gpt-4-turbo", temperature=0.7)

        assert result == mock_instance
        mock_chat_openai.assert_called_once_with(model="gpt-4-turbo", temperature=0.7)


class TestSetupLlamaIndexSettings:
    """Test the setup_llamaindex_settings function."""

    @patch("app.core.llm.Settings")
    @patch("app.core.llm.LlamaIndexOpenAI")
    @patch("app.core.llm.OpenAIEmbedding")
    @patch("app.core.llm.SimpleNodeParser")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"})
    def test_setup_llamaindex_settings_with_explicit_values(
        self, mock_parser, mock_embedding, mock_llm, mock_settings
    ):
        """Test setting up LlamaIndex with explicit parameter values (env provides key)."""
        reset_settings_cache()
        mock_llm_instance = Mock()
        mock_embedding_instance = Mock()
        mock_parser_instance = Mock()

        mock_llm.return_value = mock_llm_instance
        mock_embedding.return_value = mock_embedding_instance
        mock_parser.from_defaults.return_value = mock_parser_instance

        setup_llamaindex_settings(
            llm_model="gpt-4",
            embedding_model="text-embedding-ada-002",
            chunk_size=512,
            chunk_overlap=50,
        )

        # Verify LLM configuration
        mock_llm.assert_called_once_with(model="gpt-4", temperature=0)
        mock_settings.llm = mock_llm_instance

        # Verify embedding configuration
        mock_embedding.assert_called_once_with(model="text-embedding-ada-002")
        mock_settings.embed_model = mock_embedding_instance

        # Verify node parser configuration
        mock_parser.from_defaults.assert_called_once_with(
            chunk_size=512, chunk_overlap=50
        )
        mock_settings.node_parser = mock_parser_instance

    @patch("app.core.llm.Settings")
    @patch("app.core.llm.LlamaIndexOpenAI")
    @patch("app.core.llm.OpenAIEmbedding")
    @patch("app.core.llm.SimpleNodeParser")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"})
    def test_setup_llamaindex_settings_with_env_key(
        self, mock_parser, mock_embedding, mock_llm, mock_settings
    ):
        """Test setting up LlamaIndex with environment API key."""
        reset_settings_cache()
        mock_llm_instance = Mock()
        mock_embedding_instance = Mock()
        mock_parser_instance = Mock()

        mock_llm.return_value = mock_llm_instance
        mock_embedding.return_value = mock_embedding_instance
        mock_parser.from_defaults.return_value = mock_parser_instance

        setup_llamaindex_settings()

        # Verify LLM configuration with default parameters
        mock_llm.assert_called_once_with(model="gpt-3.5-turbo", temperature=0)
        mock_settings.llm = mock_llm_instance

        # Verify embedding configuration with default parameters
        mock_embedding.assert_called_once_with(model="text-embedding-3-small")
        mock_settings.embed_model = mock_embedding_instance

        # Verify node parser configuration with default parameters
        mock_parser.from_defaults.assert_called_once_with(
            chunk_size=1024, chunk_overlap=20
        )
        mock_settings.node_parser = mock_parser_instance

    @patch.dict("os.environ", {}, clear=True)
    def test_setup_llamaindex_settings_missing_api_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        reset_settings_cache()
        with pytest.raises(
            ValueError, match="OPENAI_API_KEY environment variable is required"
        ):
            setup_llamaindex_settings()


class TestAgentLLMFunctions:
    """Test the convenience functions for agent LLMs."""

    @patch("app.core.llm.get_chat_openai_llm")
    def test_get_math_agent_llm(self, mock_get_chat_openai):
        """Test get_math_agent_llm function."""
        mock_llm = Mock()
        mock_get_chat_openai.return_value = mock_llm

        result = get_math_agent_llm()

        assert result == mock_llm
        mock_get_chat_openai.assert_called_once_with(
            model="gpt-3.5-turbo", temperature=0
        )

    @patch("app.core.llm.get_chat_openai_llm")
    def test_get_router_agent_llm(self, mock_get_chat_openai):
        """Test get_router_agent_llm function."""
        mock_llm = Mock()
        mock_get_chat_openai.return_value = mock_llm

        result = get_router_agent_llm()

        assert result == mock_llm
        mock_get_chat_openai.assert_called_once_with(
            model="gpt-3.5-turbo", temperature=0
        )

    @patch("app.core.llm.get_chat_openai_llm")
    def test_math_and_router_agent_llms_are_equivalent(self, mock_get_chat_openai):
        """Test that math and router agent LLMs use the same configuration."""
        mock_llm = Mock()
        mock_get_chat_openai.return_value = mock_llm

        math_llm = get_math_agent_llm()
        router_llm = get_router_agent_llm()

        assert math_llm == mock_llm
        assert router_llm == mock_llm
        assert mock_get_chat_openai.call_count == 2

        # Verify both calls use the same parameters
        expected_kwargs = {"model": "gpt-3.5-turbo", "temperature": 0}
        for call in mock_get_chat_openai.call_args_list:
            args, kwargs = call
            assert kwargs == expected_kwargs


class TestSetupKnowledgeAgentSettings:
    """Test the setup_knowledge_agent_settings function."""

    @patch("app.core.llm.setup_llamaindex_settings")
    def test_setup_knowledge_agent_settings(self, mock_setup_llamaindex):
        """Test setup_knowledge_agent_settings function."""
        setup_knowledge_agent_settings()

        mock_setup_llamaindex.assert_called_once_with(
            llm_model="gpt-3.5-turbo",
            embedding_model="text-embedding-3-small",
            chunk_size=1024,
            chunk_overlap=20,
        )

    @patch("app.core.llm.setup_llamaindex_settings")
    def test_setup_knowledge_agent_settings_propagates_error(
        self, mock_setup_llamaindex
    ):
        """Test that errors from setup_llamaindex_settings are propagated."""
        mock_setup_llamaindex.side_effect = ValueError("API key missing")

        with pytest.raises(ValueError, match="API key missing"):
            setup_knowledge_agent_settings()


class TestIntegration:
    """Integration tests for LLM factory functions."""

    @patch("app.core.llm.ChatOpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_end_to_end_llm_creation(self, mock_chat_openai):
        """Test end-to-end LLM creation workflow."""
        reset_settings_cache()
        mock_instance = Mock()
        mock_chat_openai.return_value = mock_instance

        # Test creating LLMs for different agents
        math_llm = get_math_agent_llm()
        router_llm = get_router_agent_llm()

        assert math_llm == mock_instance
        assert router_llm == mock_instance
        assert mock_chat_openai.call_count == 2

    @patch("app.core.llm.Settings")
    @patch("app.core.llm.LlamaIndexOpenAI")
    @patch("app.core.llm.OpenAIEmbedding")
    @patch("app.core.llm.SimpleNodeParser")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_end_to_end_llamaindex_setup(
        self, mock_parser, mock_embedding, mock_llm, mock_settings
    ):
        """Test end-to-end LlamaIndex setup workflow."""
        reset_settings_cache()
        mock_llm_instance = Mock()
        mock_embedding_instance = Mock()
        mock_parser_instance = Mock()

        mock_llm.return_value = mock_llm_instance
        mock_embedding.return_value = mock_embedding_instance
        mock_parser.from_defaults.return_value = mock_parser_instance

        # Test knowledge agent setup
        setup_knowledge_agent_settings()

        # Verify all components were configured
        mock_llm.assert_called_once()
        mock_embedding.assert_called_once()
        mock_parser.from_defaults.assert_called_once()


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch.dict("os.environ", {}, clear=True)
    def test_all_functions_require_api_key(self):
        """Test that all functions require API key when not provided."""
        reset_settings_cache()
        with pytest.raises(
            ValueError, match="OPENAI_API_KEY environment variable is required"
        ):
            get_chat_openai_llm()

        with pytest.raises(
            ValueError, match="OPENAI_API_KEY environment variable is required"
        ):
            setup_llamaindex_settings()

        with pytest.raises(
            ValueError, match="OPENAI_API_KEY environment variable is required"
        ):
            get_math_agent_llm()

        with pytest.raises(
            ValueError, match="OPENAI_API_KEY environment variable is required"
        ):
            get_router_agent_llm()

        with pytest.raises(
            ValueError, match="OPENAI_API_KEY environment variable is required"
        ):
            setup_knowledge_agent_settings()

    @patch("app.core.llm.ChatOpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_chat_openai_creation_error_handling(self, mock_chat_openai):
        """Test error handling when ChatOpenAI creation fails."""
        reset_settings_cache()
        mock_chat_openai.side_effect = Exception("OpenAI API error")

        with pytest.raises(Exception, match="OpenAI API error"):
            get_chat_openai_llm()

    @patch("app.core.llm.LlamaIndexOpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_llamaindex_llm_creation_error_handling(self, mock_llm):
        """Test error handling when LlamaIndex LLM creation fails."""
        reset_settings_cache()
        mock_llm.side_effect = Exception("LlamaIndex LLM error")

        with pytest.raises(Exception, match="LlamaIndex LLM error"):
            setup_llamaindex_settings()
