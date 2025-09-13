from __future__ import annotations

"""ChromaDB client wrapper for vector similarity search."""

from typing import List

import chromadb
from chromadb.api.types import Documents, Embeddings

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ChromaDBAgent:  # noqa: D401
    """Wrapper around ChromaDB client for similarity search."""

    def __init__(self, collection_name: str = "default") -> None:
        self._client = chromadb.Client()
        self._collection = self._client.get_or_create_collection(collection_name)
        logger.info("ChromaDB collection '%s' ready", collection_name)

    def add_documents(self, ids: List[str], documents: Documents, embeddings: Embeddings | None = None) -> None:  # noqa: D401
        """Add documents (and optional embeddings) to the collection."""

        self._collection.add(ids=ids, documents=documents, embeddings=embeddings)
        logger.debug("Added %d documents to ChromaDB", len(ids))

    def similarity_search(self, query: str, n_results: int = 5) -> List[str]:  # noqa: D401
        """Return IDs of the most similar documents."""

        results = self._collection.query(query_texts=[query], n_results=n_results)
        return results["ids"][0] if results.get("ids") else []
