import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from requests.exceptions import HTTPError, RequestException

from app.agents.knowledge_agent import (
    _setup_llm_and_embeddings,
    _scrape_page_content,
    _find_collection_links,
    _find_article_links,
    _crawl_help_center,
    _create_vector_store,
    _load_existing_index,
    initialize_knowledge_agent,
    query_knowledge,
    _extract_sources_from_response,
    get_index_stats,
    reset_knowledge_base,
    VECTOR_STORE_PATH,
    BASE_URL,
    COLLECTION_NAME,
    REQUEST_HEADERS,
)


class TestSetupLLMAndEmbeddings:
    """Test the _setup_llm_and_embeddings function."""

    @patch("app.agents.knowledge_agent.os.getenv")
    @patch("app.agents.knowledge_agent.Settings")
    @patch("app.agents.knowledge_agent.OpenAI")
    @patch("app.agents.knowledge_agent.OpenAIEmbedding")
    @patch("app.agents.knowledge_agent.SimpleNodeParser")
    def test_setup_with_valid_api_key(
        self, mock_parser, mock_embedding, mock_llm, mock_settings, mock_getenv
    ):
        """Test that LLM and embeddings are configured correctly with valid API key."""
        # Arrange
        mock_getenv.return_value = "test-api-key"
        mock_llm_instance = Mock()
        mock_llm.return_value = mock_llm_instance
        mock_embedding_instance = Mock()
        mock_embedding.return_value = mock_embedding_instance
        mock_parser_instance = Mock()
        mock_parser.from_defaults.return_value = mock_parser_instance

        # Act
        _setup_llm_and_embeddings()

        # Assert
        mock_getenv.assert_called_once_with("OPENAI_API_KEY")
        mock_llm.assert_called_once_with(
            model="gpt-3.5-turbo", temperature=0, api_key="test-api-key"
        )
        mock_embedding.assert_called_once_with(
            model="text-embedding-3-small", api_key="test-api-key"
        )
        mock_parser.from_defaults.assert_called_once_with(
            chunk_size=1024, chunk_overlap=20
        )

        # Verify Settings assignments
        assert mock_settings.llm == mock_llm_instance
        assert mock_settings.embed_model == mock_embedding_instance
        assert mock_settings.node_parser == mock_parser_instance

    @patch("app.agents.knowledge_agent.os.getenv")
    def test_setup_with_missing_api_key(self, mock_getenv):
        """Test that ValueError is raised when API key is missing."""
        # Arrange
        mock_getenv.return_value = None

        # Act & Assert
        with pytest.raises(
            ValueError, match="OPENAI_API_KEY environment variable is required"
        ):
            _setup_llm_and_embeddings()

        mock_getenv.assert_called_once_with("OPENAI_API_KEY")


class TestScrapePageContent:
    """Test the _scrape_page_content function."""

    @pytest.fixture
    def sample_html(self):
        """Sample HTML content for testing."""
        return """
        <html>
            <head>
                <title>Test Page</title>
                <style>
                    body { color: red; }
                </style>
            </head>
            <body>
                <h1>Main Title</h1>
                <p>This is a paragraph with    multiple   spaces.</p>
                <script>
                    console.log("This should be removed");
                </script>
                <div>
                    <p>Another paragraph</p>
                    <p>   With leading spaces   </p>
                </div>
            </body>
        </html>
        """

    @pytest.fixture
    def expected_cleaned_text(self):
        """Expected cleaned text from sample HTML."""
        return "Test Page Main Title This is a paragraph with multiple spaces. Another paragraph With leading spaces"

    @patch("app.agents.knowledge_agent.requests.get")
    @patch("app.agents.knowledge_agent.BeautifulSoup")
    def test_scrape_page_content_success(
        self, mock_beautifulsoup, mock_requests_get, sample_html, expected_cleaned_text
    ):
        """Test successful page content scraping and cleaning."""
        # Arrange
        url = "https://example.com/test"
        mock_response = Mock()
        mock_response.content = sample_html.encode()
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        mock_soup = Mock()
        mock_soup.get_text.return_value = "Test Page\n\nMain Title\n\nThis is a paragraph with    multiple   spaces.\n\nAnother paragraph\n\n   With leading spaces   \n\n"
        # Mock the soup callable behavior for script/style removal
        mock_soup.return_value = []
        mock_beautifulsoup.return_value = mock_soup

        # Act
        result = _scrape_page_content(url)

        # Assert
        mock_requests_get.assert_called_once_with(
            url, headers=REQUEST_HEADERS, timeout=30
        )
        mock_response.raise_for_status.assert_called_once()
        mock_beautifulsoup.assert_called_once_with(sample_html.encode(), "html.parser")

        # Verify script/style removal was called
        mock_soup.assert_called_with(["script", "style"])

        assert result["content"] == expected_cleaned_text
        assert result["url"] == url

    @patch("app.agents.knowledge_agent.requests.get")
    def test_scrape_page_content_http_error(self, mock_requests_get):
        """Test that HTTPError is propagated correctly."""
        # Arrange
        url = "https://example.com/test"
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
        mock_requests_get.return_value = mock_response

        # Act & Assert
        with pytest.raises(HTTPError, match="404 Not Found"):
            _scrape_page_content(url)

        mock_requests_get.assert_called_once_with(
            url, headers=REQUEST_HEADERS, timeout=30
        )

    @patch("app.agents.knowledge_agent.requests.get")
    def test_scrape_page_content_request_exception(self, mock_requests_get):
        """Test that RequestException is propagated correctly."""
        # Arrange
        url = "https://example.com/test"
        mock_requests_get.side_effect = RequestException("Connection failed")

        # Act & Assert
        with pytest.raises(RequestException, match="Connection failed"):
            _scrape_page_content(url)

        mock_requests_get.assert_called_once_with(
            url, headers=REQUEST_HEADERS, timeout=30
        )


class TestFindCollectionLinks:
    """Test the _find_collection_links function."""

    @pytest.fixture
    def sample_html_with_collections(self):
        """Sample HTML with collection links."""
        return """
        <html>
            <body>
                <a href="/collections/123">Collection 1</a>
                <a href="/collections/456">Collection 2</a>
                <a href="/articles/789">Article Link</a>
                <a href="https://external.com/collections/999">External Collection</a>
                <a href="/other/page">Other Page</a>
            </body>
        </html>
        """

    @patch("app.agents.knowledge_agent.requests.get")
    @patch("app.agents.knowledge_agent.BeautifulSoup")
    def test_find_collection_links_success(
        self, mock_beautifulsoup, mock_requests_get, sample_html_with_collections
    ):
        """Test successful collection link finding."""
        # Arrange
        base_url = "https://example.com"
        mock_response = Mock()
        mock_response.content = sample_html_with_collections.encode()
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        mock_soup = Mock()
        mock_links = [
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
        ]
        # Set href as dictionary access
        mock_links[0].__getitem__ = Mock(return_value="/collections/123")
        mock_links[1].__getitem__ = Mock(return_value="/collections/456")
        mock_links[2].__getitem__ = Mock(return_value="/articles/789")
        mock_links[3].__getitem__ = Mock(
            return_value="https://external.com/collections/999"
        )
        mock_links[4].__getitem__ = Mock(return_value="/other/page")
        mock_soup.find_all.return_value = mock_links
        mock_beautifulsoup.return_value = mock_soup

        # Act
        result = _find_collection_links(base_url)

        # Assert
        mock_requests_get.assert_called_once_with(
            base_url, headers=REQUEST_HEADERS, timeout=30
        )
        expected_links = {
            "https://example.com/collections/123",
            "https://example.com/collections/456",
            "https://external.com/collections/999",
        }
        assert result == expected_links

    @patch("app.agents.knowledge_agent.requests.get")
    def test_find_collection_links_request_failure(self, mock_requests_get):
        """Test that empty set is returned when request fails."""
        # Arrange
        base_url = "https://example.com"
        mock_requests_get.side_effect = RequestException("Connection failed")

        # Act
        result = _find_collection_links(base_url)

        # Assert
        assert result == set()

    @patch("app.agents.knowledge_agent.requests.get")
    @patch("app.agents.knowledge_agent.BeautifulSoup")
    def test_find_collection_links_no_collections(
        self, mock_beautifulsoup, mock_requests_get
    ):
        """Test that empty set is returned when no collection links are found."""
        # Arrange
        base_url = "https://example.com"
        html_without_collections = (
            "<html><body><a href='/articles/123'>Article</a></body></html>"
        )
        mock_response = Mock()
        mock_response.content = html_without_collections.encode()
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        mock_soup = Mock()
        mock_soup.find_all.return_value = [Mock(href="/articles/123")]
        mock_beautifulsoup.return_value = mock_soup

        # Act
        result = _find_collection_links(base_url)

        # Assert
        assert result == set()


class TestFindArticleLinks:
    """Test the _find_article_links function."""

    @pytest.fixture
    def sample_html_with_articles(self):
        """Sample HTML with article links."""
        return """
        <html>
            <body>
                <a href="/articles/123">Article 1</a>
                <a href="/articles/456">Article 2</a>
                <a href="/collections/789">Collection Link</a>
                <a href="https://external.com/articles/999">External Article</a>
                <a href="/other/page">Other Page</a>
            </body>
        </html>
        """

    @patch("app.agents.knowledge_agent.requests.get")
    @patch("app.agents.knowledge_agent.BeautifulSoup")
    def test_find_article_links_success(
        self, mock_beautifulsoup, mock_requests_get, sample_html_with_articles
    ):
        """Test successful article link finding."""
        # Arrange
        collection_url = "https://example.com/collections/test"
        mock_response = Mock()
        mock_response.content = sample_html_with_articles.encode()
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        mock_soup = Mock()
        mock_links = [
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
        ]
        # Set href as dictionary access
        mock_links[0].__getitem__ = Mock(return_value="/articles/123")
        mock_links[1].__getitem__ = Mock(return_value="/articles/456")
        mock_links[2].__getitem__ = Mock(return_value="/collections/789")
        mock_links[3].__getitem__ = Mock(
            return_value="https://external.com/articles/999"
        )
        mock_links[4].__getitem__ = Mock(return_value="/other/page")
        mock_soup.find_all.return_value = mock_links
        mock_beautifulsoup.return_value = mock_soup

        # Act
        result = _find_article_links(collection_url)

        # Assert
        mock_requests_get.assert_called_once_with(
            collection_url, headers=REQUEST_HEADERS, timeout=30
        )
        expected_links = {
            "https://example.com/articles/123",
            "https://example.com/articles/456",
            "https://external.com/articles/999",
        }
        assert result == expected_links

    @patch("app.agents.knowledge_agent.requests.get")
    def test_find_article_links_request_failure(self, mock_requests_get):
        """Test that empty set is returned when request fails."""
        # Arrange
        collection_url = "https://example.com/collections/test"
        mock_requests_get.side_effect = RequestException("Connection failed")

        # Act
        result = _find_article_links(collection_url)

        # Assert
        assert result == set()


class TestCrawlHelpCenter:
    """Test the _crawl_help_center function."""

    @patch("app.agents.knowledge_agent._scrape_page_content")
    @patch("app.agents.knowledge_agent._find_article_links")
    @patch("app.agents.knowledge_agent._find_collection_links")
    def test_crawl_help_center_success(
        self, mock_find_collections, mock_find_articles, mock_scrape
    ):
        """Test successful help center crawling."""
        # Arrange
        mock_find_collections.return_value = {
            "https://example.com/collections/1",
            "https://example.com/collections/2",
        }
        mock_find_articles.side_effect = [
            {"https://example.com/articles/1", "https://example.com/articles/2"},
            {"https://example.com/articles/3", "https://example.com/articles/4"},
        ]
        mock_scrape.side_effect = [
            {"content": "Article 1 content", "url": "https://example.com/articles/1"},
            {"content": "Article 2 content", "url": "https://example.com/articles/2"},
            {"content": "Article 3 content", "url": "https://example.com/articles/3"},
            {"content": "Article 4 content", "url": "https://example.com/articles/4"},
        ]

        # Act
        result = _crawl_help_center()

        # Assert
        mock_find_collections.assert_called_once_with(BASE_URL)
        assert mock_find_articles.call_count == 2
        assert mock_scrape.call_count == 4

        # Verify document creation
        assert len(result) == 4
        for doc in result:
            assert hasattr(doc, "text")
            assert hasattr(doc, "metadata")
            assert doc.metadata["source"] == "infinitepay_help_center"

    @patch("app.agents.knowledge_agent._scrape_page_content")
    @patch("app.agents.knowledge_agent._find_article_links")
    @patch("app.agents.knowledge_agent._find_collection_links")
    def test_crawl_help_center_with_failed_articles(
        self, mock_find_collections, mock_find_articles, mock_scrape
    ):
        """Test crawling continues when some articles fail to process."""
        # Arrange
        mock_find_collections.return_value = {"https://example.com/collections/1"}
        mock_find_articles.return_value = {
            "https://example.com/articles/1",
            "https://example.com/articles/2",
        }
        mock_scrape.side_effect = [
            {"content": "Article 1 content", "url": "https://example.com/articles/1"},
            RequestException(
                "Failed to scrape article 2"
            ),  # This should be caught and logged
        ]

        # Act
        result = _crawl_help_center()

        # Assert
        assert len(result) == 1  # Only successful article should be included
        assert result[0].text == "Article 1 content"

    @patch("app.agents.knowledge_agent._scrape_page_content")
    @patch("app.agents.knowledge_agent._find_article_links")
    @patch("app.agents.knowledge_agent._find_collection_links")
    def test_crawl_help_center_empty_content(
        self, mock_find_collections, mock_find_articles, mock_scrape
    ):
        """Test that articles with empty content are skipped."""
        # Arrange
        mock_find_collections.return_value = {"https://example.com/collections/1"}
        mock_find_articles.return_value = {"https://example.com/articles/1"}
        mock_scrape.return_value = {
            "content": "   ",
            "url": "https://example.com/articles/1",
        }  # Empty content

        # Act
        result = _crawl_help_center()

        # Assert
        assert len(result) == 0  # Empty content should be skipped

    @patch("app.agents.knowledge_agent._find_collection_links")
    def test_crawl_help_center_collection_failure(self, mock_find_collections):
        """Test that exception is raised when collection finding fails."""
        # Arrange
        mock_find_collections.side_effect = RequestException(
            "Failed to find collections"
        )

        # Act & Assert
        with pytest.raises(RequestException, match="Failed to find collections"):
            _crawl_help_center()


class TestCreateVectorStore:
    """Test the _create_vector_store function."""

    @patch("app.agents.knowledge_agent._load_existing_index")
    @patch("app.agents.knowledge_agent.VECTOR_STORE_PATH")
    def test_create_vector_store_loads_existing(self, mock_path, mock_load_existing):
        """Test that existing vector store is loaded when path exists."""
        # Arrange
        mock_path.exists.return_value = True
        mock_path.iterdir.return_value = ["existing_file"]

        # Act
        _create_vector_store()

        # Assert
        mock_load_existing.assert_called_once()

    @patch("app.agents.knowledge_agent.chromadb.PersistentClient")
    @patch("app.agents.knowledge_agent.VectorStoreIndex.from_documents")
    @patch("app.agents.knowledge_agent._crawl_help_center")
    @patch("app.agents.knowledge_agent._setup_llm_and_embeddings")
    @patch("app.agents.knowledge_agent.VECTOR_STORE_PATH")
    def test_create_vector_store_creates_new(
        self, mock_path, mock_setup, mock_crawl, mock_index, mock_chromadb
    ):
        """Test that new vector store is created when path doesn't exist."""
        # Arrange
        mock_path.exists.return_value = False

        # Mock documents
        mock_doc1 = Mock()
        mock_doc1.text = "Test content 1"
        mock_doc1.metadata = {"url": "test1", "source": "test"}
        mock_doc2 = Mock()
        mock_doc2.text = "Test content 2"
        mock_doc2.metadata = {"url": "test2", "source": "test"}
        mock_crawl.return_value = [mock_doc1, mock_doc2]

        # Mock ChromaDB
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_client

        # Mock VectorStoreIndex
        mock_index_instance = Mock()
        mock_index.return_value = mock_index_instance

        # Act
        _create_vector_store()

        # Assert
        mock_setup.assert_called_once()
        mock_crawl.assert_called_once()
        mock_chromadb.assert_called_once_with(path=str(mock_path / "chroma_db"))
        mock_client.get_or_create_collection.assert_called_once_with(COLLECTION_NAME)
        mock_index.assert_called_once()

    @patch("app.agents.knowledge_agent._crawl_help_center")
    @patch("app.agents.knowledge_agent._setup_llm_and_embeddings")
    @patch("app.agents.knowledge_agent.VECTOR_STORE_PATH")
    def test_create_vector_store_no_documents(self, mock_path, mock_setup, mock_crawl):
        """Test that ValueError is raised when no documents are created."""
        # Arrange
        mock_path.exists.return_value = False
        mock_crawl.return_value = []  # No documents

        # Act & Assert
        with pytest.raises(
            ValueError, match="No documents were created during crawling"
        ):
            _create_vector_store()


class TestLoadExistingIndex:
    """Test the _load_existing_index function."""

    @patch("app.agents.knowledge_agent.chromadb.PersistentClient")
    @patch("app.agents.knowledge_agent.VectorStoreIndex.from_vector_store")
    @patch("app.agents.knowledge_agent._setup_llm_and_embeddings")
    def test_load_existing_index_success(self, mock_setup, mock_index, mock_chromadb):
        """Test successful loading of existing index."""
        # Arrange
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_client

        mock_index_instance = Mock()
        mock_index.return_value = mock_index_instance

        # Act
        _load_existing_index()

        # Assert
        mock_setup.assert_called_once()
        mock_chromadb.assert_called_once_with(path=str(VECTOR_STORE_PATH / "chroma_db"))
        mock_client.get_collection.assert_called_once_with(COLLECTION_NAME)
        mock_index.assert_called_once()

    @patch("app.agents.knowledge_agent._create_vector_store")
    @patch("app.agents.knowledge_agent.chromadb.PersistentClient")
    @patch("app.agents.knowledge_agent._setup_llm_and_embeddings")
    def test_load_existing_index_failure_falls_back(
        self, mock_setup, mock_chromadb, mock_create_vector_store
    ):
        """Test that _create_vector_store is called when loading fails."""
        # Arrange
        mock_setup.side_effect = Exception("Setup failed")

        # Act
        _load_existing_index()

        # Assert
        mock_create_vector_store.assert_called_once()


class TestInitializeKnowledgeAgent:
    """Test the initialize_knowledge_agent function."""

    @patch("app.agents.knowledge_agent._create_vector_store")
    def test_initialize_knowledge_agent_calls_create(self, mock_create_vector_store):
        """Test that _create_vector_store is called when agent is not initialized."""
        # Arrange
        # Reset global variables
        import app.agents.knowledge_agent as ka

        ka._index = None
        ka._query_engine = None

        # Act
        initialize_knowledge_agent()

        # Assert
        mock_create_vector_store.assert_called_once()

    @patch("app.agents.knowledge_agent._create_vector_store")
    def test_initialize_knowledge_agent_skips_when_initialized(
        self, mock_create_vector_store
    ):
        """Test that _create_vector_store is not called when agent is already initialized."""
        # Arrange
        # Set global variables to simulate initialized state
        import app.agents.knowledge_agent as ka

        ka._index = Mock()
        ka._query_engine = Mock()

        # Act
        initialize_knowledge_agent()

        # Assert
        mock_create_vector_store.assert_not_called()


class TestExtractSourcesFromResponse:
    """Test the _extract_sources_from_response function."""

    def test_extract_sources_with_source_nodes(self):
        """Test source extraction when response has source_nodes."""
        # Arrange
        mock_response = Mock()
        mock_node1 = Mock()
        mock_node1.metadata = {"url": "https://example.com/doc1"}
        mock_node2 = Mock()
        mock_node2.metadata = {"url": "https://example.com/doc2"}
        mock_node3 = Mock()
        mock_node3.metadata = {"url": "https://example.com/doc1"}  # Duplicate
        mock_response.source_nodes = [mock_node1, mock_node2, mock_node3]

        # Act
        result = _extract_sources_from_response(mock_response)

        # Assert
        assert result == ["https://example.com/doc1", "https://example.com/doc2"]

    def test_extract_sources_with_direct_metadata(self):
        """Test source extraction when response has direct metadata."""
        # Arrange
        mock_response = Mock()
        mock_response.source_nodes = None
        mock_response.metadata = {"url": "https://example.com/doc1"}

        # Act
        result = _extract_sources_from_response(mock_response)

        # Assert
        assert result == ["https://example.com/doc1"]

    def test_extract_sources_no_sources(self):
        """Test source extraction when no sources are available."""
        # Arrange
        mock_response = Mock()
        mock_response.source_nodes = []
        mock_response.metadata = {}

        # Act
        result = _extract_sources_from_response(mock_response)

        # Assert
        assert result == []

    def test_extract_sources_exception_handling(self):
        """Test that exceptions are handled gracefully."""
        # Arrange
        mock_response = Mock()
        mock_response.source_nodes = Mock()
        mock_response.source_nodes.__iter__ = Mock(side_effect=Exception("Test error"))

        # Act
        result = _extract_sources_from_response(mock_response)

        # Assert
        assert result == []


class TestQueryKnowledge:
    """Test the query_knowledge function."""

    def test_query_knowledge_not_initialized(self):
        """Test that ValueError is raised when agent is not initialized."""
        # Arrange
        import app.agents.knowledge_agent as ka

        ka._query_engine = None

        # Act & Assert
        with pytest.raises(ValueError, match="Knowledge agent not initialized"):
            query_knowledge("test query")

    @patch("app.agents.knowledge_agent._query_engine")
    def test_query_knowledge_success(self, mock_query_engine):
        """Test successful query execution."""
        # Arrange
        mock_response = Mock()
        mock_response.__str__ = Mock(return_value="Test answer")
        mock_response.source_nodes = [
            Mock(metadata={"url": "https://example.com/doc1"}),
            Mock(metadata={"url": "https://example.com/doc2"}),
        ]
        mock_query_engine.query.return_value = mock_response

        # Act
        result = query_knowledge("test query")

        # Assert
        mock_query_engine.query.assert_called_once_with("test query")
        assert result == "Test answer"

    @patch("app.agents.knowledge_agent._query_engine")
    def test_query_knowledge_empty_response(self, mock_query_engine):
        """Test handling of empty response."""
        # Arrange
        mock_response = Mock()
        mock_response.__str__ = Mock(return_value="")
        mock_response.source_nodes = []
        mock_response.metadata = {}
        mock_query_engine.query.return_value = mock_response

        # Act
        result = query_knowledge("test query")

        # Assert
        expected_message = "I don't have information about that in the available documentation. Please try rephrasing your question or ask about a different topic."
        assert result == expected_message

    @patch("app.agents.knowledge_agent._query_engine")
    def test_query_knowledge_exception(self, mock_query_engine):
        """Test that exceptions are properly handled."""
        # Arrange
        mock_query_engine.query.side_effect = Exception("Query failed")

        # Act & Assert
        with pytest.raises(
            ValueError, match="Error querying knowledge base: Query failed"
        ):
            query_knowledge("test query")


class TestGetIndexStats:
    """Test the get_index_stats function."""

    def test_get_index_stats_not_initialized(self):
        """Test stats when agent is not initialized."""
        # Arrange
        import app.agents.knowledge_agent as ka

        ka._index = None

        # Act
        result = get_index_stats()

        # Assert
        assert result == {"status": "not_initialized"}

    @patch("app.agents.knowledge_agent._index")
    def test_get_index_stats_initialized(self, mock_index):
        """Test stats when agent is initialized."""
        # Arrange
        mock_index.docstore = Mock()
        mock_index.docstore.docs = {"doc1": Mock(), "doc2": Mock()}

        # Act
        result = get_index_stats()

        # Assert
        assert result["status"] == "initialized"
        assert result["vector_store_path"] == str(VECTOR_STORE_PATH)
        assert result["collection_name"] == COLLECTION_NAME
        assert result["base_url"] == BASE_URL
        assert result["document_count"] == 2

    @patch("app.agents.knowledge_agent._index")
    def test_get_index_stats_with_error(self, mock_index):
        """Test stats when error occurs."""
        # Arrange
        mock_index.docstore = None  # This will cause an error when accessing docs

        # Act
        result = get_index_stats()

        # Assert
        assert result["status"] == "initialized"
        assert "document_count" not in result


class TestResetKnowledgeBase:
    """Test the reset_knowledge_base function."""

    @patch("shutil.rmtree")
    @patch("app.agents.knowledge_agent._create_vector_store")
    @patch("app.agents.knowledge_agent.VECTOR_STORE_PATH")
    def test_reset_knowledge_base_success(
        self, mock_path, mock_create_vector_store, mock_rmtree
    ):
        """Test successful knowledge base reset."""
        # Arrange
        mock_path.exists.return_value = True

        # Act
        reset_knowledge_base()

        # Assert
        mock_rmtree.assert_called_once_with(mock_path)
        mock_create_vector_store.assert_called_once()

    @patch("shutil.rmtree")
    @patch("app.agents.knowledge_agent._create_vector_store")
    @patch("app.agents.knowledge_agent.VECTOR_STORE_PATH")
    def test_reset_knowledge_base_path_not_exists(
        self, mock_path, mock_create_vector_store, mock_rmtree
    ):
        """Test reset when vector store path doesn't exist."""
        # Arrange
        mock_path.exists.return_value = False

        # Act
        reset_knowledge_base()

        # Assert
        mock_rmtree.assert_not_called()
        mock_create_vector_store.assert_called_once()


class TestIntegration:
    """Integration tests for the knowledge agent."""

    @patch("app.agents.knowledge_agent._create_vector_store")
    def test_full_workflow_mock(self, mock_create_vector_store):
        """Test the full workflow with mocked dependencies."""
        # Arrange
        import app.agents.knowledge_agent as ka

        ka._index = None
        ka._query_engine = None

        # Act
        initialize_knowledge_agent()

        # Assert
        mock_create_vector_store.assert_called_once()

    def test_constants_are_defined(self):
        """Test that all required constants are properly defined."""
        assert VECTOR_STORE_PATH == Path("backend", "vector_store")
        assert BASE_URL == "https://ajuda.infinitepay.io/pt-BR/"
        assert COLLECTION_NAME == "infinitepay_docs"
        assert isinstance(REQUEST_HEADERS, dict)
        assert "User-Agent" in REQUEST_HEADERS
