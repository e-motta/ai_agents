import shutil
import logging

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

from app.security.prompts import KNOWLEDGE_AGENT_SYSTEM_PROMPT
from app.core.settings import get_settings
from app.core.llm import setup_knowledge_agent_settings
from app.agents.knowledge_agent.scraping import crawl_help_center

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
_settings = get_settings()
VECTOR_STORE_PATH = _settings.VECTOR_STORE_PATH
COLLECTION_NAME = _settings.COLLECTION_NAME


def build_index_from_scratch():
    """
    Crawls, scrapes, and builds the vector store from scratch.
    This is a slow, offline process that should NOT be called during a request.
    """
    if VECTOR_STORE_PATH.exists():
        logger.warning("Vector store already exists. Deleting it to rebuild.")
        shutil.rmtree(VECTOR_STORE_PATH)

    logger.info("Creating new vector store...")
    setup_knowledge_agent_settings()

    documents = crawl_help_center()
    if not documents:
        raise ValueError("No documents were created during crawling.")

    chroma_client = chromadb.PersistentClient(path=str(VECTOR_STORE_PATH / "chroma_db"))
    chroma_collection = chroma_client.create_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex.from_documents(
        documents, storage_context=storage_context, show_progress=True
    )
    index.storage_context.persist(persist_dir=str(VECTOR_STORE_PATH))
    logger.info("Vector store built and persisted successfully!")


def get_query_engine():
    """
    FastAPI Dependency: Loads the pre-built index from disk and returns a
    configured query engine. This function is cached to run only once.
    """
    logger.info("Initializing query engine from persisted store...")

    if not VECTOR_STORE_PATH.exists():
        logger.error("Vector store not found! Please run `build_index.py` first.")
        raise FileNotFoundError("Vector store does not exist.")

    # Setup LLM settings for LlamaIndex (this is safe to call multiple times)
    setup_knowledge_agent_settings()

    # Load the persisted ChromaDB store
    chroma_client = chromadb.PersistentClient(path=str(VECTOR_STORE_PATH / "chroma_db"))
    chroma_collection = chroma_client.get_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    # Load the index from the vector store
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    # Return the configured query engine
    return index.as_query_engine(
        system_prompt=KNOWLEDGE_AGENT_SYSTEM_PROMPT,
        similarity_top_k=5,
        response_mode="compact",
    )


async def query_knowledge(query: str, query_engine: BaseQueryEngine) -> str:
    """
    Asynchronously queries the knowledge base.

    Args:
        query: The question to ask.
        query_engine: The query engine instance provided by the dependency.

    Returns:
        The answer from the knowledge base.
    """
    if not query:
        raise ValueError("Query cannot be empty.")

    try:
        # Use the native async method for non-blocking I/O
        response = await query_engine.aquery(query)
        answer = str(response).strip()

        if not answer or answer.lower() in ["", "none", "null"]:
            return "I don't have information about that in the available documentation."

        return answer

    except Exception as e:
        logger.error(f"Error querying knowledge base: {e}", exc_info=True)
        raise ValueError(f"Error querying knowledge base: {str(e)}")
