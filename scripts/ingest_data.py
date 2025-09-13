#!/usr/bin/env python
"""Offline data ingestion pipeline.

Usage:
    python scripts/ingest_data.py --source_dir data/

The pipeline:
1. Parses files in source_dir using unstructured.io
2. Extracts named entities with spaCy
3. Generates embeddings via LlamaIndex + Nomic (Ollama backend)
4. Stores embeddings in ChromaDB and entities/relations in Neo4j.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

import spacy
from unstructured.partition.auto import partition
from llama_index.core import Document, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding

from src.utils.logger import get_logger
from src.tools.chromadb_agent import ChromaDBAgent
from src.tools.neo4j_agent import Neo4jAgent
from src.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


def _load_spacy() -> spacy.language.Language:  # noqa: D401
    """Load (or download) the English spaCy model."""

    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        import subprocess, sys

        logger.info("Downloading spaCy model en_core_web_sm…")
        subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)
        return spacy.load("en_core_web_sm")


def parse_documents(source_dir: Path) -> List[Document]:  # noqa: D401
    """Parse files in the directory into LlamaIndex Document objects."""

    docs: List[Document] = []
    for file_path in source_dir.rglob("*.*"):
        if file_path.is_dir():
            continue
        logger.info("Parsing %s", file_path.name)
        elements = partition(file_path)
        text = "\n".join([el.text for el in elements if hasattr(el, "text")])
        docs.append(Document(text=text, metadata={"filename": file_path.name}))
    logger.info("Parsed %d documents", len(docs))
    return docs


def extract_entities(text: str, nlp: spacy.language.Language) -> List[tuple[str, str]]:  # noqa: D401
    """Return list of (entity_text, label) pairs."""

    doc = nlp(text)
    return [(ent.text, ent.label_) for ent in doc.ents]


def ingest(source_dir: Path) -> None:  # noqa: D401
    nlp = _load_spacy()
    docs = parse_documents(source_dir)

    # ------------------------------------
    # Embedding + ChromaDB via LlamaIndex
    # ------------------------------------
    embed_model = OllamaEmbedding(model_name=settings.ollama_model, base_url=settings.ollama_host)
    index = VectorStoreIndex.from_documents(
        docs,
        embed_model=embed_model,
        vector_store=ChromaDBAgent()._collection,  # use underlying collection
    )
    logger.info("Embedded %d documents into ChromaDB", len(docs))

    # ------------------------------------
    # Entity extraction + Neo4j
    # ------------------------------------
    neo = Neo4jAgent()
    for doc in docs:
        ents = extract_entities(doc.text, nlp)
        for ent_text, label in ents:
            cypher = (
                "MERGE (e:Entity {name:$name, label:$label}) RETURN e"
            )
            neo.query(cypher, {"name": ent_text, "label": label})
    neo.close()
    logger.info("Inserted entities into Neo4j")


def main() -> None:  # noqa: D401
    parser = argparse.ArgumentParser(description="Document ingestion pipeline")
    parser.add_argument("--source_dir", default="data", help="Directory containing documents")
    args = parser.parse_args()

    src = Path(args.source_dir)
    if not src.exists():
        logger.error("Source directory %s does not exist", src)
        raise SystemExit(1)

    ingest(src)
    logger.info("Ingestion complete.")


if __name__ == "__main__":
    main()
