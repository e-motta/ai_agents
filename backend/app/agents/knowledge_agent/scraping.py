import logging
from typing import Any
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from llama_index.core import Document

from app.core.settings import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_settings = get_settings()
BASE_URL = _settings.BASE_URL
REQUEST_HEADERS = _settings.REQUEST_HEADERS


def _scrape_page_content(url: str) -> dict[str, Any]:
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


def _find_collection_links(base_url: str) -> set[str]:
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
            href = link["href"]  # type: ignore
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)  # type: ignore

            # Check if this is a collection link
            if "/collections/" in absolute_url:
                collection_links.add(absolute_url)
                logger.info(f"Found collection link: {absolute_url}")

        logger.info(f"Found {len(collection_links)} collection links")
        return collection_links

    except Exception as e:
        logger.error(f"Error finding collection links: {str(e)}")
        return set()


def _find_article_links(collection_url: str) -> set[str]:
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
            href = link["href"]  # type: ignore
            # Convert relative URLs to absolute
            absolute_url = urljoin(collection_url, href)  # type: ignore

            # Check if this is an article link
            if "/articles/" in absolute_url:
                article_links.add(absolute_url)
                logger.info(f"Found article link: {absolute_url}")

        logger.info(f"Found {len(article_links)} article links from {collection_url}")
        return article_links

    except Exception as e:
        logger.error(f"Error finding article links from {collection_url}: {str(e)}")
        return set()


def crawl_help_center() -> list[Document]:
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
