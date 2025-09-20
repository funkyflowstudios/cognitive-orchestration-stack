# src/api/server.py
"""FastAPI server setup with comprehensive API endpoints."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.docs import create_openapi_schema
from src.api.docs import router as docs_router
from src.api.health import router as health_router
from src.api.metrics import router as metrics_router
from src.utils.logger import get_logger
from src.utils.metrics import (
    error_count,
    initialize_metrics,
    request_count,
    success_count,
)

logger = get_logger(__name__)

app = FastAPI(
    title="Cognitive Orchestration Stack API",
    description=(
        "Comprehensive API for cognitive orchestration with monitoring, "
        "metrics, and documentation"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routes
app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(docs_router)

# Add middleware for request tracking


@app.middleware("http")
async def track_requests(request, call_next):
    """Track requests for metrics collection."""
    request_count()

    try:
        response = await call_next(request)
        if response.status_code < 400:
            success_count()
        else:
            error_count(f"http_{response.status_code}")
        return response
    except Exception as e:
        logger.error("Request processing error: %s", e)
        error_count("internal_error")
        raise


# Override OpenAPI schema generation
app.openapi = lambda: create_openapi_schema(app)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    logger.info("FastAPI server starting up")
    initialize_metrics()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on shutdown."""
    logger.info("FastAPI server shutting down")
