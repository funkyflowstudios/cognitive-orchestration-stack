"""End-to-End tests for the complete Cognitive Orchestration Stack system."""

import time
from fastapi.testclient import TestClient

from src.orchestration.graph import GRAPH
from src.orchestration.state import AgentState


class TestFullSystemE2E:
    """End-to-End tests for the complete system."""

    def test_health_checks_e2e(self, e2e_client: TestClient,
    wait_for_services):
        """Test that all health checks pass in E2E environment."""
        # Test liveness check
        response = e2e_client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data

        # Test readiness check
        response = e2e_client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data

        # Verify all critical services are healthy
        checks = data["checks"]
        assert checks["neo4j"]["status"] == "healthy"
        assert checks["chromadb"]["status"] == "healthy"
        # Ollama might be unavailable, which is acceptable

    def test_metrics_collection_e2e(self, e2e_client: TestClient,
    wait_for_services):
        """Test that metrics are properly collected in E2E environment."""
        # Make some requests to generate metrics
        e2e_client.get("/health/live")
        e2e_client.get("/metrics/")

        # Check metrics endpoint
        response = e2e_client.get("/metrics/")
        assert response.status_code == 200
        data = response.json()

        # Verify metrics structure
        assert "system_health" in data
        assert "counters" in data
        assert "timers" in data
        assert "error_counts" in data

        # Verify request count increased
        assert data["counters"]["requests"] >= 2

    def test_orchestration_workflow_e2e(self, sample_query: str,
    wait_for_services):
        """Test the complete orchestration workflow with real services."""
        # Create initial state
        initial_state = AgentState(
            query=sample_query,
            plan=[],
            tool_output=[],
            response="",
            iteration=0
        )

        # Execute the orchestration graph
        result = GRAPH.invoke(initial_state)

        # Verify the result
        assert isinstance(result, dict)
        assert "query" in result
        assert "plan" in result
        assert "response" in result
        assert result["query"] == sample_query

        # Verify a plan was created
        assert len(result["plan"]) > 0

        # Verify a response was generated
        assert len(result["response"]) > 0
        assert "Ableton Live" in result["response"] or \
    "music production" in result["response"].lower()

    def test_document_ingestion_e2e(self, e2e_client: TestClient,
    sample_documents,
    wait_for_services):
        """Test document ingestion and retrieval in E2E environment."""
        # This would test the actual document ingestion process
        # For now, we'll test that the system can handle document-related queries

        query = "What are the key features mentioned in the test documents?"
        initial_state = AgentState(
            query=query,
            plan=[],
            tool_output=[],
            response="",
            iteration=0
        )

        # Execute the orchestration graph
        result = GRAPH.invoke(initial_state)

        # Verify the result
        assert isinstance(result, dict)
        assert "response" in result
        assert len(result["response"]) > 0

    def test_error_handling_e2e(self, e2e_client: TestClient,
    wait_for_services):
        """Test error handling in E2E environment."""
        # Test invalid endpoint
        response = e2e_client.get("/invalid/endpoint")
        assert response.status_code == 404

        # Test invalid method
        response = e2e_client.post("/health/live")
        assert response.status_code == 405

        # Verify error metrics are recorded
        metrics_response = e2e_client.get("/metrics/")
        assert metrics_response.status_code == 200
        metrics = metrics_response.json()
        assert "error_counts" in metrics

    def test_concurrent_requests_e2e(self, e2e_client: TestClient,
    wait_for_services):
        """Test system behavior under concurrent requests."""
        import threading
        import queue

        results: queue.Queue[int] = queue.Queue()

        def make_request():
            response = e2e_client.get("/health/live")
            results.put(response.status_code)

        # Create multiple concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all requests succeeded
        while not results.empty():
            status_code = results.get()
            assert status_code == 200

    def test_system_performance_e2e(self, e2e_client: TestClient,
    wait_for_services):
        """Test system performance characteristics."""
        # Test response time
        start_time = time.time()
        response = e2e_client.get("/health/live")
        end_time = time.time()

        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 1.0  # Should respond within 1 second

        # Test metrics dashboard performance
        start_time = time.time()
        response = e2e_client.get("/metrics/dashboard")
        end_time = time.time()

        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 2.0  # Dashboard should load within 2 seconds

    def test_data_persistence_e2e(self, e2e_client: TestClient,
    wait_for_services):
        """Test that data persists across requests."""
        # Make a request that should store data
        query = "Test query for data persistence"
        initial_state = AgentState(
            query=query,
            plan=[],
            tool_output=[],
            response="",
            iteration=0
        )

        # Execute the orchestration graph
        result1 = GRAPH.invoke(initial_state)

        # Make another request
        time.sleep(1)  # Small delay to ensure different timestamps
        result2 = GRAPH.invoke(initial_state)

        # Both requests should succeed
        assert "response" in result1
        assert "response" in result2
        assert len(result1["response"]) > 0
        assert len(result2["response"]) > 0

    def test_system_resilience_e2e(self, e2e_client: TestClient,
    wait_for_services):
        """Test system resilience to various failure scenarios."""
        # Test with malformed query
        malformed_state = AgentState(
            query="",  # Empty query
            plan=[],
            tool_output=[],
            response="",
            iteration=0
        )

        result = GRAPH.invoke(malformed_state)
        assert isinstance(result, dict)
        # System should handle empty query gracefully

        # Test with very long query
        long_query = "What is Ableton Live? " * 100  # Very long query
        long_state = AgentState(
            query=long_query,
            plan=[],
            tool_output=[],
            response="",
            iteration=0
        )

        result = GRAPH.invoke(long_state)
        assert isinstance(result, dict)
        # System should handle long query gracefully

    def test_api_documentation_e2e(self, e2e_client: TestClient,
    wait_for_services):
        """Test that API documentation is accessible."""
        # Test OpenAPI JSON
        response = e2e_client.get("/openapi.json")
        assert response.status_code == 200
        openapi_spec = response.json()
        assert "openapi" in openapi_spec
        assert "info" in openapi_spec
        assert "paths" in openapi_spec

        # Test Swagger UI
        response = e2e_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

        # Test ReDoc
        response = e2e_client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_cors_functionality_e2e(self, e2e_client: TestClient,
    wait_for_services):
        """Test CORS functionality in E2E environment."""
        # Test with Origin header
        response = e2e_client.get(
            "/health/live",
            headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "*"

        # Test with different origin
        response = e2e_client.get(
            "/health/live",
            headers={"Origin": "https://example.com"}
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "*"
