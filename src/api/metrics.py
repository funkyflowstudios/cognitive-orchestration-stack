# src/api/metrics.py
"""Comprehensive metrics endpoints for monitoring performance data."""
# flake8: noqa: E501

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from src.utils.metrics import get_metrics, reset_metrics
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/")
async def get_metrics_endpoint():
    """Get current metrics snapshot."""
    try:
        return get_metrics()
    except Exception as e:
        logger.error("Error getting metrics: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Error getting metrics: {str(e)}"
        )


@router.get("/dashboard")
async def get_metrics_dashboard():
    """Get a simple HTML dashboard for metrics visualization."""
    try:
        metrics = get_metrics()
    except Exception as e:
        logger.error("Error getting metrics for dashboard: %s", e)
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error - Metrics Dashboard</title></head>
        <body>
            <h1>Error</h1>
            <p>Failed to load metrics: {str(e)}</p>
        </body>
        </html>
        """, status_code=500)

    # Safely get system health data
    system_health = metrics.get('system_health', {})
    counters = metrics.get('counters', {})
    timers = metrics.get('timers', {})
    error_counts = metrics.get('error_counts', {})

    # Generate HTML dashboard
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cognitive Orchestration Stack - Metrics Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .card {{ background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .metric {{ display: flex; justify-content: space-between; margin: 10px 0; }}
            .metric-label {{ font-weight: bold; }}
            .metric-value {{ color: #666; }}
            .success {{ color: #28a745; }}
            .warning {{ color: #ffc107; }}
            .danger {{ color: #dc3545; }}
            .refresh-btn {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }}
            .refresh-btn:hover {{ background: #0056b3; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Cognitive Orchestration Stack - Metrics Dashboard</h1>

            <div class="card">
                <h2>📊 System Health</h2>
                <div class="metric">
                    <span class="metric-label">Uptime:</span>
                    <span class="metric-value">{system_health.get('uptime_seconds', 0):.1f} seconds</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Requests:</span>
                    <span class="metric-value">{system_health.get('total_requests', 0)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Success Rate:</span>
                    <span class="metric-value {'success' if system_health.get('success_rate', 0) > 0.9 else 'warning' if system_health.get('success_rate', 0) > 0.7 else 'danger'}">
                        {system_health.get('success_rate', 0):.1%}
                    </span>
                </div>
            </div>

            <div class="card">
                <h2>🔢 Counters</h2>
                {''.join([f'<div class="metric"><span class="metric-label">{k}:</span><span class="metric-value">{v}</span></div>' for k, v in counters.items()]) if counters else '<div class="metric"><span class="metric-label">No counters recorded</span><span class="metric-value">-</span></div>'}
            </div>

            <div class="card">
                <h2>⏱️ Performance Timers</h2>
                {''.join([f'''
                <div class="metric">
                    <span class="metric-label">{timer_name}:</span>
                    <span class="metric-value">
                        Avg: {stats.get('avg', 0):.2f}ms |
                        Min: {stats.get('min', 0):.2f}ms |
                        Max: {stats.get('max', 0):.2f}ms |
                        P95: {stats.get('p95', 0):.2f}ms |
                        Count: {stats.get('count', 0)}
                    </span>
                </div>
                ''' for timer_name, stats in timers.items()]) if timers else '<div class="metric"><span class="metric-label">No timers recorded</span><span class="metric-value">-</span></div>'}
            </div>

            <div class="card">
                <h2>❌ Error Counts</h2>
                {''.join([f'<div class="metric"><span class="metric-label">{k}:</span><span class="metric-value danger">{v}</span></div>' for k, v in error_counts.items()]) if error_counts else '<div class="metric"><span class="metric-label">No errors recorded</span><span class="metric-value success">✅</span></div>'}
            </div>

            <div class="card">
                <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Metrics</button>
                <button class="refresh-btn" onclick="resetMetrics()" style="background: #dc3545; margin-left: 10px;">🗑️ Reset Metrics</button>
            </div>
        </div>

        <script>
            function resetMetrics() {{
                if (confirm('Are you sure you want to reset all metrics?')) {{
                    fetch('/metrics/reset', {{ method: 'POST' }})
                        .then(() => location.reload())
                        .catch(err => alert('Error resetting metrics: ' + err));
                }}
            }}

            // Auto-refresh every 30 seconds
            setTimeout(() => location.reload(), 30000);
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@router.post("/reset")
async def reset_metrics_endpoint():
    """Reset all metrics (useful for testing)."""
    try:
        reset_metrics()
        logger.info("Metrics reset requested via API")
        return {"message": "Metrics reset successfully"}
    except Exception as e:
        logger.error("Failed to reset metrics: %s", e)
        raise HTTPException(status_code=500, detail={"error": f"Failed to reset metrics: {str(e)}"})


def get_health_score():
    """Get health score for monitoring systems."""
    metrics = get_metrics()

    # Calculate health score
    success_rate = metrics.get('system_health', {}).get('success_rate', 1.0)
    error_count = sum(metrics.get('error_counts', {}).values())
    total_requests = metrics.get('system_health', {}).get('total_requests', 1)

    # Health score calculation (0-100)
    health_score = 100
    if success_rate < 0.95:
        health_score -= 20
    if error_count > total_requests * 0.1:  # More than 10% errors
        health_score -= 30
    if total_requests == 0:
        health_score = 50  # No requests yet

    return {
        "health_score": max(0, health_score),
        "status": "healthy" if health_score > 80 else "degraded" if health_score > 50 else "unhealthy",
        "details": {
            "request_success_rate": success_rate,
            "error_rate": error_count / max(total_requests, 1)
        }
    }


@router.get("/health")
async def get_health_metrics():
    """Get health-focused metrics for monitoring systems."""
    try:
        return get_health_score()
    except Exception as e:
        logger.error("Error getting health metrics: %s", e)
        raise HTTPException(status_code=500, detail=f"Error getting health metrics: {str(e)}")
