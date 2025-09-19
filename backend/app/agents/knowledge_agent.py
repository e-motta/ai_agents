"""
Knowledge Agent module for querying InfinitePay documentation using LlamaIndex.
Enhanced with comprehensive multi-level crawling.
"""

import os
import logging
import time
from pathlib import Path
from typing import Optional, List, Set, Dict, Any
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from llama_index.core import (
    VectorStoreIndex,
    Document,
    StorageContext,
    Settings,
)
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from app.security.prompts import KNOWLEDGE_AGENT_SYSTEM_PROMPT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for the index and query engine
_index: Optional[VectorStoreIndex] = None
_query_engine = None

# Configuration
VECTOR_STORE_PATH = Path("backend", "vector_store")
BASE_URL = "https://ajuda.infinitepay.io/pt-BR/"
COLLECTION_NAME = "infinitepay_docs"

# Headers for web requests
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def _setup_llm_and_embeddings():
    """Setup LLM and embeddings with OpenAI."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    # Configure LlamaIndex settings
    Settings.llm = OpenAI(model="gpt-3.5-turbo", temperature=0, api_key=api_key)
    Settings.embed_model = OpenAIEmbedding(
        model="text-embedding-3-small", api_key=api_key
    )
    Settings.node_parser = SimpleNodeParser.from_defaults(
        chunk_size=1024, chunk_overlap=20
    )


def _scrape_page_content(url: str) -> Dict[str, Any]:
    """
    Scrape content from a single page.

    Args:
        url: The URL to scrape

    Returns:
        Dictionary containing text content and metadata
    """
    try:
        logger.info(f"Scraping content from {url}")

        response = requests.get(url, headers=REQUEST_HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract text content
        text = soup.get_text()

        # Clean up the text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned_text = " ".join(chunk for chunk in chunks if chunk)

        logger.info(f"Successfully scraped {len(cleaned_text)} characters from {url}")

        return {"content": cleaned_text, "url": url}

    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        raise


def _find_collection_links(base_url: str) -> Set[str]:
    """
    Find all collection links from the main help center page.

    Args:
        base_url: The main help center URL

    Returns:
        Set of collection URLs
    """
    collection_links = set()

    try:
        logger.info(f"Finding collection links from {base_url}")

        response = requests.get(base_url, headers=REQUEST_HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Find all links
        links = soup.find_all("a", href=True)

        for link in links:
            href = link["href"]
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)

            # Check if this is a collection link
            if "/collections/" in absolute_url:
                collection_links.add(absolute_url)
                logger.info(f"Found collection link: {absolute_url}")

        logger.info(f"Found {len(collection_links)} collection links")
        return collection_links

    except Exception as e:
        logger.error(f"Error finding collection links: {str(e)}")
        return set()


def _find_article_links(collection_url: str) -> Set[str]:
    """
    Find all article links from a collection page.

    Args:
        collection_url: The collection URL to crawl

    Returns:
        Set of article URLs
    """
    article_links = set()

    try:
        logger.info(f"Finding article links from {collection_url}")

        response = requests.get(collection_url, headers=REQUEST_HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Find all links
        links = soup.find_all("a", href=True)

        for link in links:
            href = link["href"]
            # Convert relative URLs to absolute
            absolute_url = urljoin(collection_url, href)

            # Check if this is an article link
            if "/articles/" in absolute_url:
                article_links.add(absolute_url)
                logger.info(f"Found article link: {absolute_url}")

        logger.info(f"Found {len(article_links)} article links from {collection_url}")
        return article_links

    except Exception as e:
        logger.error(f"Error finding article links from {collection_url}: {str(e)}")
        return set()


def _crawl_help_center() -> List[Document]:
    """
    Perform comprehensive crawling of the InfinitePay help center.

    Returns:
        List of LlamaIndex Document objects
    """
    documents = []
    visited_urls = set()

    try:
        logger.info("Starting comprehensive crawl of InfinitePay help center")

        # Step 1: Find all collection links
        collection_links = _find_collection_links(BASE_URL)

        # Step 2: Find all article links from collections
        all_article_links = set()
        for collection_url in collection_links:
            article_links = _find_article_links(collection_url)
            all_article_links.update(article_links)

        logger.info(f"Total unique article links found: {len(all_article_links)}")

        # Step 3: Process each article
        for i, article_url in enumerate(all_article_links, 1):
            if article_url in visited_urls:
                continue

            visited_urls.add(article_url)

            try:
                logger.info(
                    f"Processing article {i}/{len(all_article_links)}: {article_url}"
                )

                # Scrape the article content
                page_data = _scrape_page_content(article_url)

                if page_data["content"].strip():
                    # Create LlamaIndex Document
                    doc = Document(
                        text=page_data["content"],
                        metadata={
                            "url": article_url,
                            "source": "infinitepay_help_center",
                        },
                    )
                    documents.append(doc)
                    logger.info(f"Created document for {article_url}")
                else:
                    logger.warning(f"No content found for {article_url}")

            except Exception as e:
                logger.error(f"Error processing article {article_url}: {str(e)}")
                continue

        logger.info(f"Crawling completed. Created {len(documents)} documents")
        return documents

    except Exception as e:
        logger.error(f"Error during crawling: {str(e)}")
        raise


def _create_vector_store():
    """Create and populate the vector store with documentation content."""
    global _index, _query_engine

    try:
        # Check if index already exists
        if VECTOR_STORE_PATH.exists() and any(VECTOR_STORE_PATH.iterdir()):
            logger.info("Loading existing vector store...")
            _load_existing_index()
            return

        logger.info("Creating new vector store...")

        # Setup LLM and embeddings
        _setup_llm_and_embeddings()

        # Crawl the help center and create documents
        documents = _crawl_help_center()

        if not documents:
            raise ValueError("No documents were created during crawling")

        logger.info(f"Created {len(documents)} documents from crawling")

        # Initialize ChromaDB
        chroma_client = chromadb.PersistentClient(
            path=str(VECTOR_STORE_PATH / "chroma_db")
        )
        chroma_collection = chroma_client.get_or_create_collection(COLLECTION_NAME)

        # Create vector store
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Create index directly from documents
        _index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context, show_progress=True
        )

        # Persist the index
        _index.storage_context.persist(persist_dir=str(VECTOR_STORE_PATH))

        # Create query engine with custom system prompt
        _query_engine = _index.as_query_engine(
            system_prompt=KNOWLEDGE_AGENT_SYSTEM_PROMPT,
            similarity_top_k=5,
            response_mode="compact",
        )

        logger.info("Vector store created successfully!")

    except Exception as e:
        logger.error(f"Error creating vector store: {str(e)}")
        raise


def _load_existing_index():
    """Load an existing vector store index."""
    global _index, _query_engine

    try:
        # Setup LLM and embeddings
        _setup_llm_and_embeddings()

        # Initialize ChromaDB
        chroma_client = chromadb.PersistentClient(
            path=str(VECTOR_STORE_PATH / "chroma_db")
        )
        chroma_collection = chroma_client.get_collection(COLLECTION_NAME)

        # Create vector store
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Load index
        _index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store, storage_context=storage_context
        )

        # Create query engine with custom system prompt
        _query_engine = _index.as_query_engine(
            system_prompt=KNOWLEDGE_AGENT_SYSTEM_PROMPT,
            similarity_top_k=5,
            response_mode="compact",
        )

        logger.info("Existing vector store loaded successfully!")

    except Exception as e:
        logger.error(f"Error loading existing index: {str(e)}")
        # If loading fails, create a new one
        logger.info("Creating new vector store due to loading error...")
        _create_vector_store()


def initialize_knowledge_agent():
    """Initialize the knowledge agent by creating or loading the vector store."""
    global _index, _query_engine

    if _index is None or _query_engine is None:
        logger.info("Initializing knowledge agent...")
        _create_vector_store()

    logger.info("Knowledge agent initialized successfully!")


def _extract_sources_from_response(response) -> List[str]:
    """
    Extract source URLs from LlamaIndex response metadata.

    Args:
        response: LlamaIndex response object

    Returns:
        List of source URLs used to generate the response
    """
    sources = []

    try:
        # Check if response has source_nodes attribute
        if hasattr(response, "source_nodes") and response.source_nodes:
            for node in response.source_nodes:
                if hasattr(node, "metadata") and node.metadata:
                    url = node.metadata.get("url")
                    if url and url not in sources:
                        sources.append(url)

        # Fallback: check if response has metadata directly
        elif hasattr(response, "metadata") and response.metadata:
            url = response.metadata.get("url")
            if url:
                sources.append(url)

    except Exception as e:
        logger.warning(f"Error extracting sources from response: {str(e)}")

    return sources


def query_knowledge(query: str) -> str:
    """
    Query the knowledge base for information about InfinitePay.

    Args:
        query: The question to ask about InfinitePay

    Returns:
        str: The answer based on the documentation

    Raises:
        ValueError: If the knowledge agent is not initialized or if there's an error
    """
    global _query_engine

    if _query_engine is None:
        raise ValueError(
            "Knowledge agent not initialized. Call initialize_knowledge_agent() first."
        )

    start_time = time.time()

    try:
        # Query the knowledge base
        response = _query_engine.query(query)

        # Extract the response text
        answer = str(response).strip()

        # Extract sources from response metadata (for future logging use)
        sources = _extract_sources_from_response(response)

        # Calculate execution time (for future logging use)
        execution_time_ms = (time.time() - start_time) * 1000

        # Validate the response
        if not answer or answer.lower() in ["", "none", "null"]:
            answer = "I don't have information about that in the available documentation. Please try rephrasing your question or ask about a different topic."

        return answer

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        raise ValueError(f"Error querying knowledge base: {str(e)}")


def get_index_stats() -> dict:
    """
    Get statistics about the knowledge base index.

    Returns:
        dict: Statistics about the index
    """
    global _index

    if _index is None:
        return {"status": "not_initialized"}

    try:
        stats = {
            "status": "initialized",
            "vector_store_path": str(VECTOR_STORE_PATH),
            "collection_name": COLLECTION_NAME,
            "base_url": BASE_URL,
        }

        # Try to get more detailed stats if possible
        try:
            if hasattr(_index, "docstore") and _index.docstore:
                stats["document_count"] = len(_index.docstore.docs)
        except:
            pass

        return stats

    except Exception as e:
        logger.error(f"Error getting index stats: {str(e)}")
        return {"status": "error", "error": str(e)}


def reset_knowledge_base():
    """Reset the knowledge base by deleting the vector store and recreating it."""
    global _index, _query_engine

    try:
        logger.info("Resetting knowledge base...")

        # Clear global variables
        _index = None
        _query_engine = None

        # Remove the vector store directory
        if VECTOR_STORE_PATH.exists():
            import shutil

            shutil.rmtree(VECTOR_STORE_PATH)
            logger.info("Vector store directory removed")

        # Recreate the knowledge base
        _create_vector_store()

        logger.info("Knowledge base reset successfully!")

    except Exception as e:
        logger.error(f"Error resetting knowledge base: {str(e)}")
        raise


def crawl_and_update():
    """
    Perform a fresh crawl of the help center and update the knowledge base.
    This function can be called to refresh the knowledge base with latest content.
    """
    global _index, _query_engine

    try:
        logger.info("Starting fresh crawl and knowledge base update...")

        # Clear global variables
        _index = None
        _query_engine = None

        # Remove the vector store directory
        if VECTOR_STORE_PATH.exists():
            import shutil

            shutil.rmtree(VECTOR_STORE_PATH)
            logger.info("Vector store directory removed")

        # Create new knowledge base
        _create_vector_store()

        logger.info("Knowledge base updated successfully!")

    except Exception as e:
        logger.error(f"Error updating knowledge base: {str(e)}")
        raise
