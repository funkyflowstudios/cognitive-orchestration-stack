from __future__ import annotations

"""Neo4j client wrapper used by the orchestration layer."""

from typing import Any, List

from neo4j import GraphDatabase, BoltDriver

from ..utils.logger import get_logger
from src.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class Neo4jAgent:  # noqa: D401
    """Thin convenience wrapper around the Neo4j Bolt driver."""

    def __init__(self) -> None:
        self._driver: BoltDriver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )
        logger.info("Connected to Neo4j at %s", settings.neo4j_uri)

    def query(self, cypher: str, parameters: dict | None = None) -> List[Any]:
        """Execute a Cypher query and return the resulting records as list."""

        with self._driver.session() as session:
            result = session.run(cypher, parameters or {})
            records = list(result)
            logger.debug("Returned %d records", len(records))
            return [r.data() for r in records]

    def close(self) -> None:  # noqa: D401
        """Close underlying driver."""

        self._driver.close()
        logger.info("Neo4j driver closed")
