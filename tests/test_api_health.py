"""Tests for API health endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.api.health import _get_chromadb_agent, _get_neo4j_agent, router


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_liveness_endpoint(self):
        """Test liveness endpoint."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data

    def test_readiness_endpoint_success(self):
        """Test readiness endpoint with successful health checks."""
        with (
            patch("src.api.health._get_neo4j_agent") as mock_get_neo4j,
            patch("src.api.health._get_chromadb_agent") as mock_get_chromadb,
            patch("httpx.AsyncClient") as mock_httpx_client,
        ):

            # Mock successful health checks
            mock_neo4j = MagicMock()
            mock_neo4j.query.return_value = [{"test": "data"}]
            mock_get_neo4j.return_value = mock_neo4j

            mock_chromadb = MagicMock()
            mock_chromadb.similarity_search.return_value = ["test"]
            mock_get_chromadb.return_value = mock_chromadb

            # Mock successful Ollama check
            mock_response = MagicMock(status_code=200)
            mock_client = mock_httpx_client.return_value.__aenter__.return_value
            mock_client.get.return_value = mock_response

            from fastapi import FastAPI

            app = FastAPI()
            app.include_router(router)

            client = TestClient(app)
            response = client.get("/health/ready")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
            assert data["checks"]["neo4j"]["status"] == "healthy"
            assert data["checks"]["chromadb"]["status"] == "healthy"
            assert "timestamp" in data

    def test_readiness_endpoint_neo4j_failure(self):
        """Test readiness endpoint with Neo4j failure."""
        with (
            patch("src.api.health._get_neo4j_agent") as mock_get_neo4j,
            patch("src.api.health._get_chromadb_agent") as mock_get_chromadb,
            patch("httpx.AsyncClient") as mock_httpx_client,
        ):

            # Mock Neo4j failure by targeting the correct method
            mock_neo4j = MagicMock()
            mock_neo4j.query.side_effect = Exception("Neo4j connection failed")
            mock_get_neo4j.return_value = mock_neo4j

            mock_chromadb = MagicMock()
            mock_chromadb.similarity_search.return_value = ["test"]
            mock_get_chromadb.return_value = mock_chromadb

            # Mock successful Ollama check
            mock_response = MagicMock(status_code=200)
            mock_client = mock_httpx_client.return_value.__aenter__.return_value
            mock_client.get.return_value = mock_response

            from fastapi import FastAPI

            app = FastAPI()
            app.include_router(router)

            client = TestClient(app)
            response = client.get("/health/ready")

            assert response.status_code == 503
            data = response.json()
            assert data["detail"]["status"] == "not_ready"
            assert data["detail"]["checks"]["neo4j"]["status"] == "unhealthy"
            assert (
                data["detail"]["checks"]["neo4j"]["error"] == "Neo4j connection failed"
            )
            assert data["detail"]["checks"]["chromadb"]["status"] == "healthy"

    def test_readiness_endpoint_chromadb_failure(self):
        """Test readiness endpoint with ChromaDB failure."""
        with (
            patch("src.api.health._get_neo4j_agent") as mock_get_neo4j,
            patch("src.api.health._get_chromadb_agent") as mock_get_chromadb,
            patch("httpx.AsyncClient") as mock_httpx_client,
        ):

            # Mock successful Neo4j
            mock_neo4j = MagicMock()
            mock_neo4j.query.return_value = [{"test": "data"}]
            mock_get_neo4j.return_value = mock_neo4j

            # Mock ChromaDB failure by targeting the correct method
            mock_chromadb = MagicMock()
            mock_chromadb.similarity_search.side_effect = Exception(
                "ChromaDB connection failed"
            )
            mock_get_chromadb.return_value = mock_chromadb

            # Mock successful Ollama check
            mock_response = MagicMock(status_code=200)
            mock_client = mock_httpx_client.return_value.__aenter__.return_value
            mock_client.get.return_value = mock_response

            from fastapi import FastAPI

            app = FastAPI()
            app.include_router(router)

            client = TestClient(app)
            response = client.get("/health/ready")

            assert response.status_code == 503
            data = response.json()
            assert data["detail"]["status"] == "not_ready"
            assert data["detail"]["checks"]["neo4j"]["status"] == "healthy"
            assert data["detail"]["checks"]["chromadb"]["status"] == "unhealthy"
            assert (
                data["detail"]["checks"]["chromadb"]["error"]
                == "ChromaDB connection failed"
            )

    def test_readiness_endpoint_both_failures(self):
        """Test readiness endpoint with both services failing."""
        with (
            patch("src.api.health._get_neo4j_agent") as mock_get_neo4j,
            patch("src.api.health._get_chromadb_agent") as mock_get_chromadb,
            patch("httpx.AsyncClient") as mock_httpx_client,
        ):

            # Mock both failures by targeting the correct methods
            mock_neo4j = MagicMock()
            mock_neo4j.query.side_effect = Exception("Neo4j connection failed")
            mock_get_neo4j.return_value = mock_neo4j

            mock_chromadb = MagicMock()
            mock_chromadb.similarity_search.side_effect = Exception(
                "ChromaDB connection failed"
            )
            mock_get_chromadb.return_value = mock_chromadb

            # Mock successful Ollama check
            mock_response = MagicMock(status_code=200)
            mock_client = mock_httpx_client.return_value.__aenter__.return_value
            mock_client.get.return_value = mock_response

            from fastapi import FastAPI

            app = FastAPI()
            app.include_router(router)

            client = TestClient(app)
            response = client.get("/health/ready")

            assert response.status_code == 503
            data = response.json()
            assert data["detail"]["status"] == "not_ready"
            assert data["detail"]["checks"]["neo4j"]["status"] == "unhealthy"
            assert data["detail"]["checks"]["chromadb"]["status"] == "unhealthy"


class TestHealthAgentGetters:
    """Test the agent getter functions."""

    def test_get_neo4j_agent_lazy_initialization(self):
        """Test lazy initialization of Neo4j agent."""
        # Clear the global variable
        import src.api.health

        src.api.health._neo4j_agent = None

        with patch("src.api.health.Neo4jAgent") as mock_neo4j_class:
            mock_agent = MagicMock()
            mock_neo4j_class.return_value = mock_agent

            # First call should create new instance
            agent1 = _get_neo4j_agent()
            assert agent1 is mock_agent
            assert src.api.health._neo4j_agent is mock_agent
            mock_neo4j_class.assert_called_once()

            # Second call should return same instance
            agent2 = _get_neo4j_agent()
            assert agent2 is mock_agent
            assert mock_neo4j_class.call_count == 1  # Still only called once

    def test_get_chromadb_agent_lazy_initialization(self):
        """Test lazy initialization of ChromaDB agent."""
        # Clear the global variable
        import src.api.health

        src.api.health._chromadb_agent = None

        with patch("src.api.health.ChromaDBAgent") as mock_chromadb_class:
            mock_agent = MagicMock()
            mock_chromadb_class.return_value = mock_agent

            # First call should create new instance
            agent1 = _get_chromadb_agent()
            assert agent1 is mock_agent
            assert src.api.health._chromadb_agent is mock_agent
            mock_chromadb_class.assert_called_once()

            # Second call should return same instance
            agent2 = _get_chromadb_agent()
            assert agent2 is mock_agent
            assert mock_chromadb_class.call_count == 1  # Still only called once


class TestHealthEndpointIntegration:
    """Test health endpoints with full integration."""

    def test_health_router_prefix(self):
        """Test that health router has correct prefix."""
        assert router.prefix == "/health"
        assert "health" in router.tags

    def test_health_endpoints_exist(self):
        """Test that all health endpoints exist."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)

        # Test that endpoints exist (should not return 404)
        live_response = client.get("/health/live")
        ready_response = client.get("/health/ready")

        # At least one should not be 404 (depending on mock setup)
        assert live_response.status_code != 404
        assert ready_response.status_code != 404
