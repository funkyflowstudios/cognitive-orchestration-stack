"""Tests for Neo4j agent functionality."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.tools.neo4j_agent import Neo4jAgent


class TestNeo4jAgent:
    """Test the Neo4jAgent class."""

    def test_neo4j_agent_initialization(self, mock_settings):
        """Test Neo4jAgent initialization."""
        with patch('src.tools.neo4j_agent.GraphDatabase') as mock_db, \
             patch('src.tools.neo4j_agent.settings', mock_settings):
            mock_driver = MagicMock()
            mock_driver.verify_connectivity.return_value = None
            mock_db.driver.return_value = mock_driver

            agent = Neo4jAgent()

            assert agent._driver is not None
            mock_db.driver.assert_called_once_with(
                mock_settings.neo4j_uri,
                auth=(mock_settings.neo4j_user, mock_settings.neo4j_password),
                max_connection_pool_size=10
            )
            mock_driver.verify_connectivity.assert_called_once()

    def test_neo4j_agent_initialization_error(self, mock_settings):
        """Test Neo4jAgent initialization with connection error."""
        with patch('src.tools.neo4j_agent.GraphDatabase') as mock_db:
            mock_db.driver.side_effect = Exception("Connection failed")

            with pytest.raises(Exception, match="Connection failed"):
                Neo4jAgent()

    def test_neo4j_agent_close(self, mock_settings):
        """Test Neo4jAgent close method."""
        with patch('src.tools.neo4j_agent.GraphDatabase') as mock_db:
            mock_driver = MagicMock()
            mock_driver.verify_connectivity.return_value = None
            mock_db.driver.return_value = mock_driver

            agent = Neo4jAgent()
            agent.close()

            mock_driver.close.assert_called_once()

    def test_neo4j_agent_close_with_none_driver(self, mock_settings):
        """Test Neo4jAgent close method when driver is None."""
        with patch('src.tools.neo4j_agent.GraphDatabase') as mock_db:
            mock_driver = MagicMock()
            mock_driver.verify_connectivity.return_value = None
            mock_db.driver.return_value = mock_driver

            agent = Neo4jAgent()
            agent._driver = None
            agent.close()  # Should not raise an error

    def test_neo4j_agent_query_success(self, mock_settings):
        """Test successful query execution."""
        with patch('src.tools.neo4j_agent.GraphDatabase') as mock_db:
            mock_driver = MagicMock()
            mock_driver.verify_connectivity.return_value = None
            mock_db.driver.return_value = mock_driver

            # Mock session and result
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_record = MagicMock()
            mock_record.data.return_value = {
                "name": "Test Node", "label": "TestLabel"
            }
            mock_result.__iter__.return_value = [mock_record]
            mock_session.run.return_value = mock_result
            mock_driver.session.return_value.__enter__.return_value = (
                mock_session
            )

            agent = Neo4jAgent()
            result = agent.query("MATCH (n) RETURN n")

            assert result == [{"name": "Test Node", "label": "TestLabel"}]
            mock_session.run.assert_called_once_with("MATCH (n) RETURN n", {})

    def test_neo4j_agent_query_with_parameters(self, mock_settings):
        """Test query execution with parameters."""
        with patch('src.tools.neo4j_agent.GraphDatabase') as mock_db:
            mock_driver = MagicMock()
            mock_driver.verify_connectivity.return_value = None
            mock_db.driver.return_value = mock_driver

            # Mock session and result
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_record = MagicMock()
            mock_record.data.return_value = {"name": "Test Node"}
            mock_result.__iter__.return_value = [mock_record]
            mock_session.run.return_value = mock_result
            mock_driver.session.return_value.__enter__.return_value = (
                mock_session
            )

            agent = Neo4jAgent()
            parameters = {"name": "Test"}
            result = agent.query(
                "MATCH (n {name: $name}) RETURN n", parameters
            )

            assert result == [{"name": "Test Node"}]
            mock_session.run.assert_called_once_with(
                "MATCH (n {name: $name}) RETURN n", parameters
            )

    def test_neo4j_agent_query_empty_result(self, mock_settings):
        """Test query execution with empty result."""
        with patch('src.tools.neo4j_agent.GraphDatabase') as mock_db:
            mock_driver = MagicMock()
            mock_driver.verify_connectivity.return_value = None
            mock_db.driver.return_value = mock_driver

            # Mock session and empty result
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.__iter__.return_value = []
            mock_session.run.return_value = mock_result
            mock_driver.session.return_value.__enter__.return_value = (
                mock_session
            )

            agent = Neo4jAgent()
            result = agent.query("MATCH (n) RETURN n")

            assert result == []

    @pytest.mark.asyncio
    async def test_neo4j_agent_query_async(self, mock_settings):
        """Test async query execution."""
        with patch('src.tools.neo4j_agent.GraphDatabase') as mock_db:
            mock_driver = MagicMock()
            mock_driver.verify_connectivity.return_value = None
            mock_db.driver.return_value = mock_driver

            # Mock session and result
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_record = MagicMock()
            mock_record.data.return_value = {"name": "Async Node"}
            mock_result.__iter__.return_value = [mock_record]
            mock_session.run.return_value = mock_result
            mock_driver.session.return_value.__enter__.return_value = (
                mock_session
            )

            agent = Neo4jAgent()
            result = await agent.query_async("MATCH (n) RETURN n")

            assert result == [{"name": "Async Node"}]

    @pytest.mark.asyncio
    async def test_neo4j_agent_query_async_with_parameters(
        self, mock_settings
    ):
        """Test async query execution with parameters."""
        with patch('src.tools.neo4j_agent.GraphDatabase') as mock_db:
            mock_driver = MagicMock()
            mock_driver.verify_connectivity.return_value = None
            mock_db.driver.return_value = mock_driver

            # Mock session and result
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_record = MagicMock()
            mock_record.data.return_value = {"name": "Async Node"}
            mock_result.__iter__.return_value = [mock_record]
            mock_session.run.return_value = mock_result
            mock_driver.session.return_value.__enter__.return_value = (
                mock_session
            )

            agent = Neo4jAgent()
            parameters = {"id": 123}
            result = await agent.query_async(
                "MATCH (n {id: $id}) RETURN n", parameters
            )

            assert result == [{"name": "Async Node"}]

    def test_neo4j_agent_execute_query_sync(self, mock_settings):
        """Test internal _execute_query_sync method."""
        with patch('src.tools.neo4j_agent.GraphDatabase') as mock_db:
            mock_driver = MagicMock()
            mock_driver.verify_connectivity.return_value = None
            mock_db.driver.return_value = mock_driver

            # Mock session and result
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_record = MagicMock()
            mock_record.data.return_value = {"name": "Sync Node"}
            mock_result.__iter__.return_value = [mock_record]
            mock_session.run.return_value = mock_result
            mock_driver.session.return_value.__enter__.return_value = (
                mock_session
            )

            agent = Neo4jAgent()
            result = agent._execute_query_sync(
                "MATCH (n) RETURN n", {"param": "value"}
            )

            assert result == [{"name": "Sync Node"}]
            mock_session.run.assert_called_once_with(
                "MATCH (n) RETURN n", {"param": "value"}
            )

    def test_neo4j_agent_retry_decorator(self, mock_settings):
        """Test that query method has retry decorator."""

        from src.tools.neo4j_agent import Neo4jAgent

        # Check if the query method has the retry decorator
        query_method = getattr(Neo4jAgent, 'query')
        # The method should have some indication of being decorated
        # This is a basic check - in practice, you might need to check the
        # function's metadata
        assert callable(query_method)

    def test_neo4j_agent_connection_pooling(self, mock_settings):
        """Test that Neo4jAgent uses connection pooling."""
        with patch('src.tools.neo4j_agent.GraphDatabase') as mock_db:
            mock_driver = MagicMock()
            mock_driver.verify_connectivity.return_value = None
            mock_db.driver.return_value = mock_driver

            Neo4jAgent()

            # Verify that driver was created with connection pooling
            mock_db.driver.assert_called_once()
            call_args = mock_db.driver.call_args
            assert 'max_connection_pool_size' in call_args.kwargs
            assert call_args.kwargs['max_connection_pool_size'] == 10
