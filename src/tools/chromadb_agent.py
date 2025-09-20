from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import List

import chromadb
from llama_index.embeddings.ollama import OllamaEmbedding

from src.config import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class ChromaDBAgent:
    """Wrapper around ChromaDB client for similarity search with LRU
    caching."""

    _client: chromadb.Client | None = None
    _embedding_function: OllamaEmbedding | None = None

    def __init__(self, collection_name: str = "default") -> None:
        # Use singleton client for connection pooling
        if ChromaDBAgent._client is None:
            # Use persistent database instead of in-memory
            ChromaDBAgent._client = chromadb.PersistentClient(path="./chroma_db")
            ChromaDBAgent._embedding_function = OllamaEmbedding(
                model_name=settings.ollama_embedding_model,
                base_url=settings.ollama_host,
            )
            logger.info(
                "ChromaDB persistent client initialized with connection pooling"
            )

        self._client = ChromaDBAgent._client
        self._embedding_function = ChromaDBAgent._embedding_function

        # Check if collection exists and has correct dimensions
        try:
            existing_collection = self._client.get_collection(collection_name)
            # Test embedding dimensions by creating a test embedding
            if self._embedding_function is None:
                raise RuntimeError("Embedding function not initialized")
            test_embedding = self._embedding_function.get_text_embedding("test")

            # Try to query with test embedding to check dimensions
            try:
                existing_collection.query(
                    query_embeddings=[test_embedding], n_results=1
                )
                # If successful, use existing collection
                self._collection = existing_collection
                logger.info(
                    "Using existing ChromaDB collection '%s' with correct "
                    "dimensions",
                    collection_name,
                )
            except Exception as e:
                if "dimension" in str(e).lower():
                    logger.warning(
                        "Collection '%s' has wrong dimensions, deleting and "
                        "recreating",
                        collection_name,
                    )
                    self._client.delete_collection(collection_name)
                    self._collection = self._client.create_collection(collection_name)
                    logger.info(
                        "Created new ChromaDB collection '%s' with correct "
                        "dimensions",
                        collection_name,
                    )
                else:
                    raise e
        except Exception:
            # Collection doesn't exist, create it
            self._collection = self._client.create_collection(collection_name)
            logger.info("Created new ChromaDB collection '%s'", collection_name)

    def similarity_search(self, query: str, n_results: int = 5) -> List[str]:
        """Return the content of the most similar documents with LRU
        caching."""
        return self._cached_search(query, n_results)

    @lru_cache(maxsize=128)
    def _cached_search(self, query: str, n_results: int) -> List[str]:
        """Cached search function using LRU cache."""
        logger.debug("Cache miss for query: %s", query[:50])
        # 1. Manually create embeddings for the query using our model
        if self._embedding_function is None:
            raise RuntimeError("Embedding function not initialized")
        query_embeddings = self._embedding_function.get_text_embedding(query)

        # 2. Query the collection using the generated embeddings
        results = self._collection.query(
            query_embeddings=[query_embeddings], n_results=n_results
        )

        # 3. Return the actual document text
        documents = results["documents"][0] if results.get("documents") else []
        logger.debug("Cached results for query: %s", query[:50])

        return documents

    async def similarity_search_async(
        self, query: str, n_results: int = 5
    ) -> List[str]:
        """Async version of similarity search for better performance."""
        # Run the cached search in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._cached_search, query, n_results)

    def get_collections(self) -> List[str]:
        """Get list of available collections."""
        try:
            if self._client is None:
                return []
            collections = self._client.list_collections()
            return [collection.name for collection in collections]
        except Exception as e:
            logger.error("Failed to get collections: %s", e)
            return []

    def clear_cache(self) -> None:
        """Clear the LRU cache."""
        self._cached_search.cache_clear()
        logger.info("ChromaDB LRU cache cleared")

    def close(self) -> None:
        """Close the shared client connection."""
        if ChromaDBAgent._client is not None:
            # Note: ChromaDB client doesn't have explicit close method
            # but we can clear the reference for cleanup
            ChromaDBAgent._client = None
            ChromaDBAgent._embedding_function = None
            logger.info("ChromaDB client closed")
