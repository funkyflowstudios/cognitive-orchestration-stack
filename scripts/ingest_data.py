#!/usr/bin/env python
"""Offline data ingestion pipeline.

Usage:
    python scripts/ingest_data.py --source_dir data/
"""
from __future__ import annotations

import argparse
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest documents into Neo4j and ChromaDB")
    parser.add_argument("--source_dir", default="data", help="Directory containing source documents")
    return parser.parse_args()


def main() -> None:  # noqa: D401
    args = parse_args()
    source = Path(args.source_dir)
    if not source.exists():
        logger.error("Source directory %s does not exist", source)
        raise SystemExit(1)

    # TODO: implement unstructured.io parsing, spaCy NER, embedding, LlamaIndex pipeline
    logger.info("Ingestion pipeline not yet implemented (placeholder).")


if __name__ == "__main__":
    main()
