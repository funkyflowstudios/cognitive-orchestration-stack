# src/api/health.py
"""Health check endpoints for monitoring service status."""

from __future__ import annotations

import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from src.config import get_settings
from src.tools.chromadb_agent import ChromaDBAgent
from src.tools.neo4j_agent import Neo4jAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix="/health", tags=["health"])

# Global instances for health checks
_neo4j_agent: Neo4jAgent | None = None
_chromadb_agent: ChromaDBAgent | None = None


def _get_neo4j_agent() -> Neo4jAgent:
    """Lazy initialization of Neo4j agent for health checks."""
    global _neo4j_agent
    if _neo4j_agent is None:
        _neo4j_agent = Neo4jAgent()
    return _neo4j_agent


def _get_chromadb_agent() -> ChromaDBAgent:
    """Lazy initialization of ChromaDB agent for health checks."""
    global _chromadb_agent
    if _chromadb_agent is None:
        _chromadb_agent = ChromaDBAgent()
    return _chromadb_agent


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """Basic liveness probe - returns 200 if process is running."""
    return {
        "status": "alive",
        "timestamp": time.time(),
        "service": "cognitive-orchestration-stack",
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness probe - checks all external dependencies."""
    checks = {
        "neo4j": {"status": "unknown", "error": None},
        "chromadb": {"status": "unknown", "error": None},
        "ollama": {"status": "unknown", "error": None},
    }

    # Check Neo4j connectivity
    try:
        neo4j_agent = _get_neo4j_agent()
        neo4j_agent.query("MATCH RETURN 1")
        checks["neo4j"]["status"] = "healthy"
    except Exception as e:
        checks["neo4j"]["status"] = "unhealthy"
        checks["neo4j"]["error"] = str(e)
        logger.warning("Neo4j health check failed: %s", e)

    # Check ChromaDB connectivity
    try:
        chromadb_agent = _get_chromadb_agent()
        # Simple operation to verify connection
        chromadb_agent.similarity_search("test", n_results=1)
        checks["chromadb"]["status"] = "healthy"
    except Exception as e:
        checks["chromadb"]["status"] = "unhealthy"
        checks["chromadb"]["error"] = str(e)
        logger.warning("ChromaDB health check failed: %s", e)

    # Check Ollama (optional - don't fail if not available)
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.ollama_host}/api/tags", timeout=5.0)
            if response.status_code == 200:
                checks["ollama"]["status"] = "healthy"
            else:
                checks["ollama"]["status"] = "unhealthy"
                checks["ollama"]["error"] = f"HTTP {response.status_code}"
    except Exception as e:
        checks["ollama"]["status"] = "unavailable"
        checks["ollama"]["error"] = str(e)
        logger.info("Ollama health check failed (optional): %s", e)

    # Determine overall readiness
    critical_services = ["neo4j", "chromadb"]
    unhealthy_services = [
        name
        for name, check in checks.items()
        if name in critical_services and check["status"] != "healthy"
    ]

    if unhealthy_services:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "unhealthy_services": unhealthy_services,
                "checks": checks,
            },
        )

    return {
        "status": "ready",
        "timestamp": time.time(),
        "checks": checks,
    }
