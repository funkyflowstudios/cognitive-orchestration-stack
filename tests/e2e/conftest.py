"""End-to-End test configuration and fixtures."""

import asyncio
import os
import subprocess
import time
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import requests
from fastapi.testclient import TestClient

from src.api.server import app
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def docker_compose_file():
    """Return the path to the docker-compose file for E2E tests."""
    return Path(__file__).parent / "docker-compose.e2e.yml"


@pytest.fixture(scope="session")
def docker_services():
    """Start and stop Docker services for E2E tests."""
    # This will be handled by pytest-docker-compose if available
    # For now, we'll assume services are running externally
    yield


@pytest.fixture(scope="session")
def e2e_settings():
    """Get settings configured for E2E testing."""
    settings = get_settings()
    # Override settings for E2E testing
    settings.neo4j_uri = "bolt://localhost:7687"
    settings.neo4j_user = "neo4j"
    settings.neo4j_password = "test_password"
    settings.ollama_host = "http://localhost:11434"
    # ChromaDB uses local persistent storage, no host/port needed
    return settings


@pytest.fixture(scope="session")
def e2e_client(e2e_settings) -> Generator[TestClient, None, None]:
    """Create a test client for E2E testing."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def wait_for_services():
    """Wait for all external services to be ready."""
    services = [
        ("Neo4j", "http://localhost:7474"),
        ("Ollama", "http://localhost:11434/api/tags"),
    ]

    for service_name, url in services:
        logger.info(f"Waiting for {service_name} to be ready...")
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"{service_name} is ready!")
                    break
            except requests.exceptions.RequestException:
                if attempt < max_attempts - 1:
                    time.sleep(2)
                else:
                    pytest.skip(f"{service_name} is not available for E2E testing")
        else:
            pytest.skip(f"{service_name} is not available for E2E testing")


@pytest.fixture(scope="function")
def clean_test_data():
    """Clean up test data before and after each test."""
    # This would clean up any test data created during tests
    # Implementation depends on the specific services being used
    yield
    # Cleanup after test
    pass


@pytest.fixture(scope="function")
def sample_query():
    """Provide a sample query for E2E testing."""
    return "What are the key features of Ableton Live for music production?"


@pytest.fixture(scope="function")
def sample_documents():
    """Provide sample documents for testing document ingestion."""
    return [
        {
            "content": "Ableton Live is a digital audio workstation (DAW) designed for live performance and music production.",
            "metadata": {"source": "test", "type": "introduction"}
        },
        {
            "content": "Key features include real-time audio manipulation, MIDI sequencing, and extensive built-in effects.",
            "metadata": {"source": "test", "type": "features"}
        },
        {
            "content": "The software supports both Mac and Windows platforms and integrates with various hardware controllers.",
            "metadata": {"source": "test", "type": "compatibility"}
        }
    ]
