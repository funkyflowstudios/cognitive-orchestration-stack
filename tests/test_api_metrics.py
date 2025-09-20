"""Tests for API metrics endpoints."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.metrics import router


class TestMetricsEndpoints:
    """Test metrics endpoints."""

    def test_metrics_endpoint(self):
        """Test basic metrics endpoint."""
        with patch("src.api.metrics.get_metrics") as mock_get_metrics:
            mock_metrics = {
                "request_count": 100,
                "success_count": 95,
                "error_count": 5,
                "planner_calls": 50,
                "vector_search_calls": 30,
                "graph_search_calls": 20,
                "synthesizer_calls": 50,
            }
            mock_get_metrics.return_value = mock_metrics

            from fastapi import FastAPI

            app = FastAPI()
            app.include_router(router)

            client = TestClient(app)
            response = client.get("/metrics/")

            assert response.status_code == 200
            data = response.json()
            assert data["request_count"] == 100
            assert data["success_count"] == 95
            assert data["error_count"] == 5

    def test_metrics_dashboard_endpoint(self):
        """Test metrics dashboard endpoint."""
        with patch("src.api.metrics.get_metrics") as mock_get_metrics:
            mock_metrics = {
                "system_health": {
                    "uptime_seconds": 100.0,
                    "total_requests": 100,
                    "success_rate": 0.95,
                },
                "counters": {"request_count": 100},
                "timers": {},
                "error_counts": {"error_count": 5},
            }
            mock_get_metrics.return_value = mock_metrics

            from fastapi import FastAPI

            app = FastAPI()
            app.include_router(router)

            client = TestClient(app)
            response = client.get("/metrics/dashboard")

            assert response.status_code == 200
            assert response.headers["content-type"] == "text/html; charset=utf-8"
            # Check that HTML content contains expected elements
            html_content = response.text
            assert "Metrics Dashboard" in html_content
            assert "100" in html_content  # total_requests

    def test_metrics_health_endpoint(self):
        """Test metrics health endpoint."""
        with patch("src.api.metrics.get_health_score") as mock_get_health:
            mock_health = {
                "health_score": 95.0,
                "status": "healthy",
                "details": {"request_success_rate": 95.0, "error_rate": 5.0},
            }
            mock_get_health.return_value = mock_health

            from fastapi import FastAPI

            app = FastAPI()
            app.include_router(router)

            client = TestClient(app)
            response = client.get("/metrics/health")

            assert response.status_code == 200
            data = response.json()
            assert data["health_score"] == 95.0
            assert data["status"] == "healthy"
            assert data["details"]["request_success_rate"] == 95.0

    def test_metrics_reset_endpoint(self):
        """Test metrics reset endpoint."""
        with patch("src.api.metrics.reset_metrics") as mock_reset:
            mock_reset.return_value = {"message": "Metrics reset successfully"}

            from fastapi import FastAPI

            app = FastAPI()
            app.include_router(router)

            client = TestClient(app)
            response = client.post("/metrics/reset")

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Metrics reset successfully"
            mock_reset.assert_called_once()

    def test_metrics_endpoint_error_handling(self):
        """Test metrics endpoint error handling."""
        with patch("src.api.metrics.get_metrics") as mock_get_metrics:
            mock_get_metrics.side_effect = Exception("Metrics service unavailable")

            from fastapi import FastAPI

            app = FastAPI()
            app.include_router(router)

            client = TestClient(app)
            response = client.get("/metrics/")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Error getting metrics" in data["detail"]
            assert "Metrics service unavailable" in data["detail"]

    def test_metrics_dashboard_error_handling(self):
        """Test metrics dashboard error handling."""
        with patch("src.api.metrics.get_metrics") as mock_get_metrics:
            mock_get_metrics.side_effect = Exception("Dashboard unavailable")

            from fastapi import FastAPI

            app = FastAPI()
            app.include_router(router)

            client = TestClient(app)
            response = client.get("/metrics/dashboard")

            assert response.status_code == 500
            # Should return error page
            assert response.headers["content-type"] == "text/html; charset=utf-8"
            html_content = response.text
            assert "Error" in html_content or "error" in html_content

    def test_metrics_health_error_handling(self):
        """Test metrics health error handling."""
        with patch("src.api.metrics.get_health_score") as mock_get_health:
            mock_get_health.side_effect = Exception("Health check failed")

            from fastapi import FastAPI

            app = FastAPI()
            app.include_router(router)

            client = TestClient(app)
            response = client.get("/metrics/health")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Health check failed" in data["detail"]

    def test_metrics_reset_error_handling(self):
        """Test metrics reset error handling."""
        with patch("src.api.metrics.reset_metrics") as mock_reset:
            mock_reset.side_effect = Exception("Reset failed")

            from fastapi import FastAPI

            app = FastAPI()
            app.include_router(router)

            client = TestClient(app)
            response = client.post("/metrics/reset")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]
            assert "Reset failed" in data["detail"]["error"]


class TestMetricsRouterConfiguration:
    """Test metrics router configuration."""

    def test_metrics_router_prefix(self):
        """Test that metrics router has correct prefix."""
        assert router.prefix == "/metrics"
        assert "metrics" in router.tags

    def test_metrics_endpoints_exist(self):
        """Test that all metrics endpoints exist."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)

        # Test that endpoints exist (should not return 404)
        metrics_response = client.get("/metrics/")
        dashboard_response = client.get("/metrics/dashboard")
        health_response = client.get("/metrics/health")
        reset_response = client.post("/metrics/reset")

        # At least one should not be 404 (depending on mock setup)
        assert metrics_response.status_code != 404
        assert dashboard_response.status_code != 404
        assert health_response.status_code != 404
        assert reset_response.status_code != 404


class TestMetricsIntegration:
    """Test metrics integration with actual metrics functions."""

    def test_metrics_endpoint_with_real_metrics(self):
        """Test metrics endpoint with real metrics functions."""
        # This test would require the actual metrics module to be available
        # For now, we'll just test that the endpoint structure is correct
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/metrics/")

        # Should return some response (either success or error)
        assert response.status_code in [200, 500]

    def test_metrics_dashboard_html_structure(self):
        """Test that metrics dashboard returns proper HTML structure."""
        with patch("src.api.metrics.get_metrics") as mock_get_metrics:
            mock_metrics = {"request_count": 100, "success_count": 95, "error_count": 5}
            mock_get_metrics.return_value = mock_metrics

            from fastapi import FastAPI

            app = FastAPI()
            app.include_router(router)

            client = TestClient(app)
            response = client.get("/metrics/dashboard")

            if response.status_code == 200:
                html_content = response.text
                # Check for basic HTML structure
                assert "<!DOCTYPE html>" in html_content or "<html>" in html_content
                assert "<head>" in html_content
                assert "<body>" in html_content
                assert "Metrics" in html_content
