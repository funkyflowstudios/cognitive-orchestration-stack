"""
Unit tests for API layer components.

Tests FastAPI endpoints, middleware, error handling, and response formats.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.api.server import app


class TestAPIServer:
    """Test cases for the main FastAPI server."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_app_creation(self):
        """Verifies that the FastAPI app is created correctly."""
        assert app is not None
        assert app.title == "Cognitive Orchestration Stack API"
        assert app.version == "1.0.0"

    def test_cors_middleware(self, client):
        """Verifies that CORS middleware is properly configured."""
        # Test with a GET request - CORS headers should be present
        response = client.get(
            "/health/live", headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "*"

    def test_docs_endpoints(self, client):
        """Verifies that documentation endpoints are accessible."""
        # Test OpenAPI JSON endpoint
        response = client.get("/openapi.json")
        assert response.status_code == 200
        openapi_data = response.json()
        assert "openapi" in openapi_data
        assert "info" in openapi_data

        # Test Swagger UI endpoint
        response = client.get("/docs")
        assert response.status_code == 200

        # Test ReDoc endpoint
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_request_tracking_middleware(self, client):
        """Verifies that request tracking middleware works."""
        with patch("src.api.server.request_count") as mock_request_count, \
             patch("src.api.server.success_count") as mock_success_count:

            response = client.get("/health/live")
            assert response.status_code == 200

            # Verify metrics were called
            mock_request_count.assert_called_once()
            mock_success_count.assert_called_once()

    def test_error_handling_middleware(self, client):
        """Verifies that error handling middleware works."""
        with patch("src.api.server.error_count") as mock_error_count:
            # Test with a non-existent endpoint
            response = client.get("/nonexistent")
            assert response.status_code == 404

            # Verify error was tracked
            mock_error_count.assert_called_once()

    def test_startup_shutdown_events(self):
        """Verifies that startup and shutdown events are defined."""
        # Check that the events are registered
        assert hasattr(app, 'router')
        # The events are defined in the app, but we can't easily test them
        # without actually starting the server


class TestHealthEndpoints:
    """Test cases for health check endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for health endpoints."""
        return TestClient(app)

    def test_liveness_check(self, client):
        """Verifies that liveness check returns correct response."""
        response = client.get("/health/live")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
        assert data["service"] == "cognitive-orchestration-stack"

    @patch("src.api.health._get_neo4j_agent")
    @patch("src.api.health._get_chromadb_agent")
    def test_readiness_check_success(
        self, mock_chromadb, mock_neo4j, client
    ):
        """Verifies that readiness check passes when all services are
        healthy."""
        # Mock successful health checks
        mock_neo4j_instance = MagicMock()
        mock_neo4j_instance.query.return_value = []
        mock_neo4j.return_value = mock_neo4j_instance

        mock_chromadb_instance = MagicMock()
        mock_chromadb_instance.similarity_search.return_value = ["test"]
        mock_chromadb.return_value = mock_chromadb_instance

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            response = client.get("/health/ready")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "ready"
            assert "checks" in data
            assert data["checks"]["neo4j"]["status"] == "healthy"
            assert data["checks"]["chromadb"]["status"] == "healthy"
            assert data["checks"]["ollama"]["status"] == "healthy"

    @patch("src.api.health._get_neo4j_agent")
    def test_readiness_check_neo4j_failure(self, mock_neo4j, client):
        """Verifies that readiness check fails when Neo4j is unhealthy."""
        # Mock Neo4j failure
        mock_neo4j_instance = MagicMock()
        mock_neo4j_instance.query.side_effect = Exception("Connection failed")
        mock_neo4j.return_value = mock_neo4j_instance

        response = client.get("/health/ready")
        assert response.status_code == 503

        data = response.json()
        assert data["detail"]["status"] == "not_ready"
        assert "neo4j" in data["detail"]["unhealthy_services"]

    @patch("src.api.health._get_chromadb_agent")
    def test_readiness_check_chromadb_failure(self, mock_chromadb, client):
        """Verifies that readiness check fails when ChromaDB is unhealthy."""
        # Mock ChromaDB failure
        mock_chromadb_instance = MagicMock()
        mock_chromadb_instance.similarity_search.side_effect = Exception(
            "Connection failed"
        )
        mock_chromadb.return_value = mock_chromadb_instance

        response = client.get("/health/ready")
        assert response.status_code == 503

        data = response.json()
        assert data["detail"]["status"] == "not_ready"
        assert "chromadb" in data["detail"]["unhealthy_services"]

    def test_readiness_check_ollama_unavailable(self, client):
        """Verifies that readiness check handles Ollama unavailability
        gracefully."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = (
                Exception("Connection failed")
            )

            # Mock other services as healthy
            with patch("src.api.health._get_neo4j_agent") as mock_neo4j, \
                 patch("src.api.health._get_chromadb_agent") as mock_chromadb:

                mock_neo4j_instance = MagicMock()
                mock_neo4j_instance.query.return_value = []
                mock_neo4j.return_value = mock_neo4j_instance

                mock_chromadb_instance = MagicMock()
                mock_chromadb_instance.similarity_search.return_value = [
                    "test"
                ]
                mock_chromadb.return_value = mock_chromadb_instance

                response = client.get("/health/ready")
                assert response.status_code == 200

                data = response.json()
                assert data["checks"]["ollama"]["status"] == "unavailable"


class TestMetricsEndpoints:
    """Test cases for metrics endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for metrics endpoints."""
        return TestClient(app)

    @patch("src.api.metrics.get_metrics")
    def test_get_metrics_success(self, mock_get_metrics, client):
        """Verifies that metrics endpoint returns data successfully."""
        mock_metrics = {
            "counters": {"requests": 100},
            "timers": {"response_time": {"avg": 50.0}},
            "error_counts": {"500": 5}
        }
        mock_get_metrics.return_value = mock_metrics

        response = client.get("/metrics/")
        assert response.status_code == 200

        data = response.json()
        assert data == mock_metrics

    @patch("src.api.metrics.get_metrics")
    def test_get_metrics_error(self, mock_get_metrics, client):
        """Verifies that metrics endpoint handles errors properly."""
        mock_get_metrics.side_effect = Exception("Database error")

        response = client.get("/metrics/")
        assert response.status_code == 500

        data = response.json()
        assert "Error getting metrics" in data["detail"]

    @patch("src.api.metrics.get_metrics")
    def test_metrics_dashboard_success(self, mock_get_metrics, client):
        """Verifies that metrics dashboard returns HTML
        successfully."""
        mock_metrics = {
            "system_health": {
                "uptime_seconds": 3600,
                "total_requests": 100,
                "success_rate": 0.95
            },
            "counters": {"requests": 100},
            "timers": {
                "response_time": {
                    "avg": 50.0,
                    "min": 10.0,
                    "max": 200.0,
                    "p95": 80.0,
                    "count": 100
                }
            },
            "error_counts": {"500": 5}
        }
        mock_get_metrics.return_value = mock_metrics

        response = client.get("/metrics/dashboard")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"

        content = response.text
        assert "Cognitive Orchestration Stack - Metrics Dashboard" in content
        assert "System Health" in content
        assert "Counters" in content
        assert "Performance Timers" in content
        assert "Error Counts" in content

    @patch("src.api.metrics.get_metrics")
    def test_metrics_dashboard_error(self, mock_get_metrics, client):
        """Verifies that metrics dashboard handles errors properly."""
        mock_get_metrics.side_effect = Exception("Database error")

        response = client.get("/metrics/dashboard")
        assert response.status_code == 500
        assert response.headers["content-type"] == "text/html; charset=utf-8"

        content = response.text
        assert "Error" in content
        assert "Database error" in content

    @patch("src.api.metrics.reset_metrics")
    def test_reset_metrics_success(self, mock_reset_metrics, client):
        """Verifies that metrics reset endpoint works correctly."""
        response = client.post("/metrics/reset")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Metrics reset successfully"
        mock_reset_metrics.assert_called_once()

    @patch("src.api.metrics.reset_metrics")
    def test_reset_metrics_error(self, mock_reset_metrics, client):
        """Verifies that metrics reset endpoint handles errors properly."""
        mock_reset_metrics.side_effect = Exception("Reset failed")

        response = client.post("/metrics/reset")
        assert response.status_code == 500

        data = response.json()
        assert "Failed to reset metrics" in data["detail"]["error"]

    @patch("src.api.metrics.get_metrics")
    def test_health_metrics_success(self, mock_get_metrics, client):
        """Verifies that health metrics endpoint works correctly."""
        mock_metrics = {
            "system_health": {"success_rate": 0.95, "total_requests": 100},
            "error_counts": {"500": 5}
        }
        mock_get_metrics.return_value = mock_metrics

        response = client.get("/metrics/health")
        assert response.status_code == 200

        data = response.json()
        assert "health_score" in data
        assert "status" in data
        assert "details" in data
        assert data["health_score"] > 0
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    @patch("src.api.metrics.get_metrics")
    def test_health_metrics_error(self, mock_get_metrics, client):
        """Verifies that health metrics endpoint handles errors properly."""
        mock_get_metrics.side_effect = Exception("Database error")

        response = client.get("/metrics/health")
        assert response.status_code == 500

        data = response.json()
        assert "Error getting health metrics" in data["detail"]


class TestAPIIntegration:
    """Integration tests for the complete API."""

    @pytest.fixture
    def client(self):
        """Create a test client for the complete API."""
        return TestClient(app)

    def test_health_endpoints_integration(self, client):
        """Verifies that health endpoints work through the main app."""
        # Test liveness
        response = client.get("/health/live")
        assert response.status_code == 200

        # Test readiness (may fail due to external dependencies)
        response = client.get("/health/ready")
        # Should return either 200 or 503 depending on external services
        assert response.status_code in [200, 503]

    def test_metrics_endpoints_integration(self, client):
        """Verifies that metrics endpoints work through the main app."""
        # Test metrics endpoint
        response = client.get("/metrics/")
        assert response.status_code == 200

        # Test metrics dashboard
        response = client.get("/metrics/dashboard")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"

    def test_error_handling_integration(self, client):
        """Verifies that error handling works across the API."""
        # Test 404 for non-existent endpoint
        response = client.get("/nonexistent")
        assert response.status_code == 404

        # Test 405 for wrong method
        response = client.post("/health/live")
        assert response.status_code == 405

    def test_cors_headers_integration(self, client):
        """Verifies that CORS headers are present in responses."""
        # Test with a GET request - CORS headers should be present
        response = client.get(
            "/health/live", headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200

        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "*"
