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
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any

import spacy
import yaml
from unstructured.partition.auto import partition
from unstructured.partition.common import UnsupportedFileFormatError
from llama_index.core import Document
from llama_index.embeddings.ollama import (
    OllamaEmbedding,
)

# Add src to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.config import get_settings  # noqa: E402
from src.tools.chromadb_agent import ChromaDBAgent  # noqa: E402
from src.tools.neo4j_agent import Neo4jAgent  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)
settings = get_settings()


def _load_spacy() -> spacy.language.Language:  # noqa: D401
    """Load (or download) the English spaCy model."""

    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        logger.info("Downloading spaCy model en_core_web_sm…")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "spacy",
                "download",
                "en_core_web_sm",
            ],
            check=True,
        )
        return spacy.load("en_core_web_sm")


def parse_yaml_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter from Markdown content.

    Args:
        content: The full content of the file

    Returns:
        Tuple of (metadata_dict, content_without_frontmatter)
    """
    # Check if content starts with YAML frontmatter
    if not content.startswith('---'):
        return {}, content

    # Find the end of frontmatter
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_text = parts[1].strip()
    content_without_frontmatter = parts[2].strip()

    try:
        metadata = yaml.safe_load(frontmatter_text) or {}
        return metadata, content_without_frontmatter
    except yaml.YAMLError as e:
        logger.warning("Failed to parse YAML frontmatter: %s", e)
        return {}, content


def parse_documents(source_dir: Path) -> List[Document]:  # noqa: D401
    """Parse files in the directory into LlamaIndex Document objects."""

    docs: List[Document] = []
    for file_path in source_dir.rglob("*.*"):
        if file_path.is_dir():
            continue

        # Skip temporary files
        if file_path.name.endswith('.tmp'):
            logger.info("Skipping temporary file: %s", file_path.name)
            continue

        logger.info("Parsing %s", file_path.name)

        # Handle ARIS-generated Markdown files with YAML frontmatter
        if file_path.suffix.lower() == '.md':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Parse YAML frontmatter
                metadata, clean_content = parse_yaml_frontmatter(content)

                # Add file-specific metadata
                metadata.update({
                    "filename": file_path.name,
                    "source": "aris",
                    "file_type": "markdown"
                })

                docs.append(
                    Document(
                        text=clean_content,
                        metadata=metadata,
                    )
                )
                logger.info(
                    "Parsed ARIS document with metadata: %s",
                    list(metadata.keys())
                )
                continue

            except Exception as exc:
                logger.error(
                    "Failed parsing ARIS document %s: %s", file_path.name, exc
                )
                continue

        # Handle other file types with unstructured
        try:
            elements = partition(str(file_path))
        except UnsupportedFileFormatError:  # noqa: E501
            logger.warning(
                "Skipping unsupported file type: %s", file_path.name
            )
            continue
        except ImportError as exc:
            logger.warning(
                "Skipping %s due to missing partition dependency: %s",
                file_path.name,
                exc,
            )
            continue
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed parsing %s: %s", file_path.name, exc)
            continue
        texts = [
            el.text for el in elements if hasattr(el, "text")
        ]
        docs.append(
            Document(
                text="\n".join(texts),
                metadata={
                    "filename": file_path.name, "source": "unstructured"
                },
            )
        )
    logger.info("Parsed %d documents", len(docs))
    return docs


def extract_entities(
    text: str, nlp: spacy.language.Language
) -> List[tuple[str, str]]:  # noqa: D401
    """Return list of (entity_text, label) pairs."""

    doc = nlp(text)
    return [(ent.text, ent.label_) for ent in doc.ents]


def ingest(source_dir: Path) -> None:  # noqa: D401
    nlp = _load_spacy()
    docs = parse_documents(source_dir)

    # ------------------------------------
    # Embedding + ChromaDB via LlamaIndex
    # ------------------------------------
    embed_model = OllamaEmbedding(
        model_name=settings.ollama_embedding_model,
        base_url=settings.ollama_host,
    )

    # Create ChromaDB agent and get the collection
    chroma_agent = ChromaDBAgent()
    collection = chroma_agent._collection

    # Create embeddings for each document and add to ChromaDB
    for i, doc in enumerate(docs):
        # Skip empty documents
        if not doc.text or len(doc.text.strip()) == 0:
            logger.warning(
                f"Skipping empty document {i}: "
                f"{doc.metadata.get('filename', 'unknown')}"
            )
            continue

        try:
            # Generate embedding for the document
            embedding = embed_model.get_text_embedding(doc.text)

            # Add document to ChromaDB collection
            collection.add(
                documents=[doc.text],
                embeddings=[embedding],
                metadatas=[doc.metadata],
                ids=[f"doc_{i}"]
            )
            logger.debug(
                f"Added document {i} to ChromaDB: "
                f"{doc.metadata.get('filename', 'unknown')}"
            )
        except Exception as e:
            logger.error(f"Failed to process document {i}: {e}")
            continue

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
    parser.add_argument(
        "--source_dir", default="data", help="Directory containing documents"
    )
    args = parser.parse_args()

    src = Path(args.source_dir)
    if not src.exists():
        logger.error("Source directory %s does not exist", src)
        raise SystemExit(1)

    ingest(src)
    logger.info("Ingestion complete.")


if __name__ == "__main__":
    main()
