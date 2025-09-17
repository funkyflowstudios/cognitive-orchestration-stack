# In agent_stack/src/tools/neo4j_agent.py

from __future__ import annotations

import asyncio

from neo4j import GraphDatabase

from src.config import get_settings
from src.utils.logger import get_logger
from src.utils.retry import retry

logger = get_logger(__name__)
settings = get_settings()


class Neo4jAgent:
    def __init__(self):
        self._driver = None
        try:
            # Use connection pooling (pool size 10 by default)
            self._driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(
                    settings.neo4j_user,
                    settings.neo4j_password,
                ),
                max_connection_pool_size=10,
            )
            self._driver.verify_connectivity()
            logger.info("Connected to Neo4j at %s", settings.neo4j_uri)
        except Exception as e:
            logger.error("Failed to connect to Neo4j: %s", e)
            raise

    def close(self):
        if self._driver is not None:
            self._driver.close()
            logger.info("Neo4j driver closed")

    # In agent_stack/src/tools/neo4j_agent.py

    @retry
    def query(self, cypher: str, parameters: dict | None = None) -> list:
        """
        Execute a Cypher query with parameters.

        Args:
            cypher: The Cypher query template with parameter placeholders
            parameters: Dictionary of parameters to substitute in the query

        Returns:
            List of records from the query result

        Note:
            This method uses parameterized queries to prevent injection
            attacks.
            All user input should be passed via the parameters dict, not
            embedded directly in the cypher string.
        """
        with self._driver.session() as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]

    async def query_async(
        self, cypher: str, parameters: dict | None = None
    ) -> list:
        """
        Async version of query method for better performance.

        Args:
            cypher: The Cypher query template with parameter placeholders
            parameters: Dictionary of parameters to substitute in the query

        Returns:
            List of records from the query result

        Note:
            This method uses parameterized queries to prevent injection
            attacks.
            All user input should be passed via the parameters dict, not
            embedded directly in the cypher string.
        """
        # Run the synchronous query in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._execute_query_sync, cypher, parameters or {}
        )

    def _execute_query_sync(self, cypher: str, parameters: dict) -> list:
        """Synchronous query execution for use in thread pool."""
        with self._driver.session() as session:
            result = session.run(cypher, parameters)
            return [record.data() for record in result]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
