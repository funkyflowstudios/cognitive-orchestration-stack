# src/api/docs.py
"""API documentation and OpenAPI schema generation."""

from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from src.api.health import router as health_router
from src.api.metrics import router as metrics_router
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/docs", tags=["documentation"])


def create_openapi_schema(app: FastAPI) -> dict:
    """Create a comprehensive OpenAPI schema for the API."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Cognitive Orchestration Stack API",
        version="1.0.0",
        description="""
        A comprehensive API for the Cognitive Orchestration Stack, providing:

        - **Health Monitoring**: Liveness and readiness probes for production deployment
        - **Metrics Collection**: Performance monitoring and system health metrics
        - **Query Processing**: Async vector and graph search capabilities
        - **Caching**: Intelligent caching for improved performance

        ## Architecture

        The system is built on:
        - **LangGraph**: Orchestration and workflow management
        - **Ollama**: Local LLM serving
        - **Neo4j**: Graph database for knowledge storage
        - **ChromaDB**: Vector database for semantic search
        - **FastAPI**: High-performance API framework

        ## Performance Features

        - **Async/Await Support**: Non-blocking operations for better throughput
        - **Connection Pooling**: Optimized database connections
        - **Intelligent Caching**: Reduces redundant computations
        - **Query Optimization**: Automatic query performance improvements
        - **Memory Management**: Automatic cleanup and garbage collection

        ## Monitoring

        - Real-time metrics dashboard at `/metrics/dashboard`
        - Health checks at `/health/ready` and `/health/live`
        - Performance metrics at `/metrics/`
        - System health score at `/metrics/health`
        """,
        routes=app.routes,
    )

    # Add custom schema information
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }

    # Add server information
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.cognitive-stack.example.com",
            "description": "Production server"
        }
    ]

    # Add tags for better organization
    openapi_schema["tags"] = [
        {
            "name": "health",
            "description": "Health monitoring endpoints for production deployment"
        },
        {
            "name": "metrics",
            "description": "Performance metrics and monitoring"
        },
        {
            "name": "documentation",
            "description": "API documentation and schema information"
        }
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


@router.get("/")
async def get_api_docs():
    """Get comprehensive API documentation."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cognitive Orchestration Stack - API Documentation</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .endpoint { margin: 15px 0; padding: 10px; background: #f8f9fa; border-left: 4px solid #007bff; }
            .method { display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; margin-right: 10px; }
            .get { background: #28a745; color: white; }
            .post { background: #007bff; color: white; }
            .put { background: #ffc107; color: black; }
            .delete { background: #dc3545; color: white; }
            .code { background: #e9ecef; padding: 2px 4px; border-radius: 3px; font-family: monospace; }
            .section { margin: 30px 0; }
            .feature-list { list-style: none; padding: 0; }
            .feature-list li { margin: 10px 0; padding: 10px; background: #e8f5e8; border-radius: 4px; }
            .feature-list li:before { content: "✅ "; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Cognitive Orchestration Stack - API Documentation</h1>

            <div class="card">
                <h2>📋 Overview</h2>
                <p>The Cognitive Orchestration Stack provides a comprehensive API for building intelligent applications with local LLMs, vector search, and graph databases.</p>

                <h3>🔧 Key Features</h3>
                <ul class="feature-list">
                    <li><strong>Async/Await Support:</strong> Non-blocking operations for better performance</li>
                    <li><strong>Connection Pooling:</strong> Optimized database connections</li>
                    <li><strong>Intelligent Caching:</strong> Reduces redundant computations</li>
                    <li><strong>Query Optimization:</strong> Automatic performance improvements</li>
                    <li><strong>Memory Management:</strong> Automatic cleanup and garbage collection</li>
                    <li><strong>Comprehensive Monitoring:</strong> Real-time metrics and health checks</li>
                    <li><strong>Production Ready:</strong> Health probes and error handling</li>
                </ul>
            </div>

            <div class="section">
                <h2>🏥 Health Monitoring</h2>
                <div class="endpoint">
                    <span class="method get">GET</span>
                    <strong>/health/live</strong>
                    <p>Basic liveness probe - returns 200 if process is running</p>
                    <p><span class="code">curl http://localhost:8000/health/live</span></p>
                </div>

                <div class="endpoint">
                    <span class="method get">GET</span>
                    <strong>/health/ready</strong>
                    <p>Readiness probe - checks all external dependencies (Neo4j, ChromaDB, Ollama)</p>
                    <p><span class="code">curl http://localhost:8000/health/ready</span></p>
                </div>
            </div>

            <div class="section">
                <h2>📊 Metrics & Monitoring</h2>
                <div class="endpoint">
                    <span class="method get">GET</span>
                    <strong>/metrics/</strong>
                    <p>Get current metrics snapshot with performance statistics</p>
                    <p><span class="code">curl http://localhost:8000/metrics/</span></p>
                </div>

                <div class="endpoint">
                    <span class="method get">GET</span>
                    <strong>/metrics/dashboard</strong>
                    <p>Interactive HTML dashboard for metrics visualization</p>
                    <p><span class="code">http://localhost:8000/metrics/dashboard</span></p>
                </div>

                <div class="endpoint">
                    <span class="method get">GET</span>
                    <strong>/metrics/health</strong>
                    <p>Health-focused metrics for monitoring systems</p>
                    <p><span class="code">curl http://localhost:8000/metrics/health</span></p>
                </div>

                <div class="endpoint">
                    <span class="method post">POST</span>
                    <strong>/metrics/reset</strong>
                    <p>Reset all metrics (useful for testing)</p>
                    <p><span class="code">curl -X POST http://localhost:8000/metrics/reset</span></p>
                </div>
            </div>

            <div class="section">
                <h2>🔧 Usage Examples</h2>

                <h3>Starting the Server</h3>
                <div class="card">
                    <pre><code># Start the monitoring API server
uvicorn src.api.server:app --host 0.0.0.0 --port 8000

# Or with auto-reload for development
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload</code></pre>
                </div>

                <h3>Health Check Integration</h3>
                <div class="card">
                    <pre><code># Kubernetes liveness probe
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

# Kubernetes readiness probe
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5</code></pre>
                </div>

                <h3>Monitoring Integration</h3>
                <div class="card">
                    <pre><code># Prometheus metrics scraping
- job_name: 'cognitive-stack'
  static_configs:
    - targets: ['localhost:8000']
  metrics_path: '/metrics/'
  scrape_interval: 30s

# Grafana dashboard
# Import the dashboard from /metrics/dashboard</code></pre>
                </div>
            </div>

            <div class="section">
                <h2>📚 Additional Resources</h2>
                <div class="card">
                    <ul>
                        <li><strong>OpenAPI Schema:</strong> <a href="/openapi.json">/openapi.json</a></li>
                        <li><strong>Interactive Docs:</strong> <a href="/docs">/docs</a> (Swagger UI)</li>
                        <li><strong>ReDoc:</strong> <a href="/redoc">/redoc</a> (Alternative documentation)</li>
                        <li><strong>Metrics Dashboard:</strong> <a href="/metrics/dashboard">/metrics/dashboard</a></li>
                    </ul>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@router.get("/troubleshooting")
async def get_troubleshooting_guide():
    """Get troubleshooting guide for common issues."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Troubleshooting Guide - Cognitive Orchestration Stack</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .issue { margin: 20px 0; padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; }
            .solution { margin: 10px 0; padding: 10px; background: #d4edda; border-radius: 4px; }
            .code { background: #e9ecef; padding: 10px; border-radius: 4px; font-family: monospace; white-space: pre-wrap; }
            .warning { background: #f8d7da; color: #721c24; padding: 10px; border-radius: 4px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 Troubleshooting Guide</h1>

            <div class="card">
                <h2>🚨 Common Issues & Solutions</h2>

                <div class="issue">
                    <h3>❌ Health Check Failing</h3>
                    <p><strong>Symptoms:</strong> <code>/health/ready</code> returns 503 or times out</p>
                    <div class="solution">
                        <h4>Solution:</h4>
                        <ol>
                            <li>Check if all services are running:
                                <div class="code"># Check Neo4j
docker ps | grep neo4j

# Check Ollama
curl http://localhost:11434/api/tags

# Check ChromaDB (should start automatically)</div>
                            </li>
                            <li>Verify environment variables in <code>.env</code> file</li>
                            <li>Check logs: <code>tail -f logs/app.log</code></li>
                        </ol>
                    </div>
                </div>

                <div class="issue">
                    <h3>🐌 Slow Performance</h3>
                    <p><strong>Symptoms:</strong> High response times, memory usage growing</p>
                    <div class="solution">
                        <h4>Solution:</h4>
                        <ol>
                            <li>Check metrics dashboard: <code>http://localhost:8000/metrics/dashboard</code></li>
                            <li>Enable async tools in your queries</li>
                            <li>Check memory usage and restart if needed</li>
                            <li>Verify connection pooling is working</li>
                        </ol>
                    </div>
                </div>

                <div class="issue">
                    <h3>💾 Memory Issues</h3>
                    <p><strong>Symptoms:</strong> High memory usage, out of memory errors</p>
                    <div class="solution">
                        <h4>Solution:</h4>
                        <ol>
                            <li>Check memory usage: <code>curl http://localhost:8000/metrics/health</code></li>
                            <li>Clear caches: <code>curl -X POST http://localhost:8000/metrics/reset</code></li>
                            <li>Restart the service if memory usage is too high</li>
                            <li>Consider reducing batch sizes or query limits</li>
                        </ol>
                    </div>
                </div>

                <div class="issue">
                    <h3>🔌 Connection Issues</h3>
                    <p><strong>Symptoms:</strong> Database connection errors, timeouts</p>
                    <div class="solution">
                        <h4>Solution:</h4>
                        <ol>
                            <li>Check connection strings in <code>.env</code></li>
                            <li>Verify network connectivity</li>
                            <li>Check if services are accepting connections</li>
                            <li>Review connection pool settings</li>
                        </ol>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>📊 Monitoring & Debugging</h2>

                <h3>Key Metrics to Monitor</h3>
                <ul>
                    <li><strong>Success Rate:</strong> Should be > 95%</li>
                    <li><strong>Response Time:</strong> P95 should be < 2 seconds</li>
                    <li><strong>Memory Usage:</strong> Should be stable, not growing continuously</li>
                    <li><strong>Error Counts:</strong> Should be minimal</li>
                </ul>

                <h3>Debug Commands</h3>
                <div class="code"># Check system health
curl http://localhost:8000/metrics/health

# Get detailed metrics
curl http://localhost:8000/metrics/ | jq

# Check logs
tail -f logs/app.log

# Monitor in real-time
watch -n 5 'curl -s http://localhost:8000/metrics/health | jq'</div>
            </div>

            <div class="card">
                <h2>🆘 Getting Help</h2>
                <p>If you're still experiencing issues:</p>
                <ol>
                    <li>Check the logs in <code>logs/app.log</code></li>
                    <li>Collect metrics: <code>curl http://localhost:8000/metrics/ > metrics.json</code></li>
                    <li>Check system resources: <code>htop</code> or <code>top</code></li>
                    <li>Verify all dependencies are installed: <code>pip list</code></li>
                </ol>
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)
