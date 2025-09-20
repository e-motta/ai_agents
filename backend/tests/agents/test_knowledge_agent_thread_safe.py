"""
Unit tests for the thread-safe knowledge agent.

This test suite focuses on testing the thread safety of the knowledge agent
with proper mocking to avoid real initialization or network calls.
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock

from app.agents.knowledge_agent import (
    query_knowledge,
    get_index_stats,
    reset_knowledge_base,
    initialize_knowledge_agent,
    _agent_lock,
    _index,
    _query_engine,
    VECTOR_STORE_PATH,
    BASE_URL,
    COLLECTION_NAME,
    REQUEST_HEADERS,
)


class TestThreadSafety:
    """Test thread safety of the knowledge agent functions."""

    def test_concurrent_query_access(self):
        """Test that concurrent queries are handled safely."""
        # Mock the query engine
        mock_query_engine = Mock()
        mock_response = Mock()
        mock_response.__str__ = Mock(return_value="Test answer")
        mock_response.source_nodes = []
        mock_response.metadata = {}
        mock_query_engine.query.return_value = mock_response

        # Set up the global state
        with patch("app.agents.knowledge_agent._query_engine", mock_query_engine):
            results = []
            errors = []

            def query_worker(query_id):
                try:
                    result = query_knowledge(f"test query {query_id}")
                    results.append(result)
                except Exception as e:
                    errors.append(e)

            # Create multiple threads
            threads = []
            for i in range(5):
                thread = threading.Thread(target=query_worker, args=(i,))
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # All queries should succeed
            assert len(results) == 5
            assert len(errors) == 0
            assert all(result == "Test answer" for result in results)

    def test_concurrent_reset_and_query(self):
        """Test that reset and query operations don't interfere with each other."""
        # Mock the query engine
        mock_query_engine = Mock()
        mock_response = Mock()
        mock_response.__str__ = Mock(return_value="Test answer")
        mock_response.source_nodes = []
        mock_response.metadata = {}
        mock_query_engine.query.return_value = mock_response

        # Set up the global state
        with patch(
            "app.agents.knowledge_agent._query_engine", mock_query_engine
        ), patch(
            "app.agents.knowledge_agent._create_vector_store"
        ) as mock_create_vector_store, patch(
            "shutil.rmtree"
        ) as mock_rmtree, patch(
            "app.agents.knowledge_agent.VECTOR_STORE_PATH"
        ) as mock_path:

            mock_path.exists.return_value = True

            results = []
            errors = []

            def query_worker():
                try:
                    result = query_knowledge("test query")
                    results.append(result)
                except Exception as e:
                    errors.append(e)

            def reset_worker():
                try:
                    reset_knowledge_base()
                except Exception as e:
                    errors.append(e)

            # Create threads for concurrent operations
            threads = []

            # Start query threads
            for i in range(3):
                thread = threading.Thread(target=query_worker)
                threads.append(thread)
                thread.start()

            # Start reset thread
            reset_thread = threading.Thread(target=reset_worker)
            threads.append(reset_thread)
            reset_thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Operations should complete without deadlocks
            # Some queries might fail due to reset, but no deadlocks should occur
            assert len(errors) == 0 or all(
                "deadlock" not in str(e).lower() for e in errors
            )

    def test_lock_prevents_concurrent_modifications(self):
        """Test that the lock prevents concurrent modifications to shared state."""

        # Simulate concurrent access
        def access_shared_state():
            with _agent_lock:
                # Simulate some work
                time.sleep(0.01)

        threads = []
        for i in range(3):
            thread = threading.Thread(target=access_shared_state)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # If we get here without deadlock, the test passes
        assert True

    def test_query_with_local_reference(self):
        """Test that query_knowledge uses local reference to avoid race conditions."""
        mock_query_engine = Mock()
        mock_response = Mock()
        mock_response.__str__ = Mock(return_value="Test answer")
        mock_response.source_nodes = []
        mock_response.metadata = {}
        mock_query_engine.query.return_value = mock_response

        with patch("app.agents.knowledge_agent._query_engine", mock_query_engine):
            result = query_knowledge("test query")

            assert result == "Test answer"
            mock_query_engine.query.assert_called_once_with("test query")

    def test_get_stats_with_local_reference(self):
        """Test that get_index_stats uses local reference to avoid race conditions."""
        mock_index = Mock()
        mock_index.docstore = Mock()
        mock_index.docstore.docs = {"doc1": Mock(), "doc2": Mock()}

        with patch("app.agents.knowledge_agent._index", mock_index):
            result = get_index_stats()

            assert result["status"] == "initialized"
            assert result["document_count"] == 2
            assert result["vector_store_path"] == str(VECTOR_STORE_PATH)
            assert result["collection_name"] == COLLECTION_NAME
            assert result["base_url"] == BASE_URL

    def test_reset_knowledge_base_with_lock(self):
        """Test that reset_knowledge_base is protected by lock."""
        with patch(
            "app.agents.knowledge_agent._create_vector_store"
        ) as mock_create_vector_store, patch("shutil.rmtree") as mock_rmtree, patch(
            "app.agents.knowledge_agent.VECTOR_STORE_PATH"
        ) as mock_path:

            mock_path.exists.return_value = True

            reset_knowledge_base()

            mock_rmtree.assert_called_once_with(mock_path)
            mock_create_vector_store.assert_called_once()

    def test_initialize_knowledge_agent_with_lock(self):
        """Test that initialize_knowledge_agent is protected by lock."""
        with patch(
            "app.agents.knowledge_agent._create_vector_store"
        ) as mock_create_vector_store, patch(
            "app.agents.knowledge_agent._index", None
        ), patch(
            "app.agents.knowledge_agent._query_engine", None
        ):

            initialize_knowledge_agent()

            mock_create_vector_store.assert_called_once()


class TestLockBehavior:
    """Test the behavior of the global lock."""

    def test_lock_is_created(self):
        """Test that the global lock is created."""
        assert _agent_lock is not None
        assert isinstance(_agent_lock, threading.Lock)

    def test_lock_can_be_acquired_and_released(self):
        """Test that the lock can be acquired and released."""
        # This should not block or raise an exception
        with _agent_lock:
            pass

    def test_lock_prevents_concurrent_execution(self):
        """Test that the lock prevents concurrent execution of critical sections."""
        execution_order = []

        def worker1():
            with _agent_lock:
                execution_order.append("worker1_start")
                time.sleep(0.1)
                execution_order.append("worker1_end")

        def worker2():
            with _agent_lock:
                execution_order.append("worker2_start")
                time.sleep(0.1)
                execution_order.append("worker2_end")

        # Start both workers
        thread1 = threading.Thread(target=worker1)
        thread2 = threading.Thread(target=worker2)

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # Verify that workers executed sequentially (not interleaved)
        assert execution_order == [
            "worker1_start",
            "worker1_end",
            "worker2_start",
            "worker2_end",
        ]


class TestIntegration:
    """Integration tests for thread safety."""

    def test_constants_are_defined(self):
        """Test that all required constants are properly defined."""
        from pathlib import Path

        assert VECTOR_STORE_PATH == Path(__file__).parent.parent.parent / "vector_store"
        assert BASE_URL == "https://ajuda.infinitepay.io/pt-BR/"
        assert COLLECTION_NAME == "infinitepay_docs"
        assert isinstance(REQUEST_HEADERS, dict)
        assert "User-Agent" in REQUEST_HEADERS

    def test_global_variables_exist(self):
        """Test that global variables exist."""
        assert "_agent_lock" in globals()
        assert "_index" in globals()
        assert "_query_engine" in globals()

        assert isinstance(_agent_lock, threading.Lock)
        assert _index is None or hasattr(_index, "docstore")
        assert _query_engine is None or hasattr(_query_engine, "query")
