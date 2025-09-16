# src/utils/metrics.py
"""Comprehensive metrics collection for performance monitoring."""

from __future__ import annotations

import time
import threading
from collections import defaultdict, deque
from functools import wraps
from typing import Any, Callable, TypeVar, Dict, List

from src.utils.logger import get_logger

logger = get_logger(__name__)

_R = TypeVar("_R")

# Thread-safe metrics store with more detailed tracking
_metrics_lock = threading.Lock()
_metrics: dict[str, Any] = {
    "counters": defaultdict(int),
    "timers": defaultdict(list),
    "gauges": {},
    "histograms": defaultdict(list),
    "error_counts": defaultdict(int),
    "performance_trends": defaultdict(lambda: deque(maxlen=100)),
    "system_health": {
        "uptime_start": time.time(),
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
    }
}


def increment(counter_name: str, value: int = 1) -> None:
    """Increment a counter metric (thread-safe)."""
    with _metrics_lock:
        _metrics["counters"][counter_name] += value
        logger.debug("Counter %s incremented by %d", counter_name, value)


def timing(timer_name: str, duration_ms: float) -> None:
    """Record a timing metric in milliseconds (thread-safe)."""
    with _metrics_lock:
        _metrics["timers"][timer_name].append(duration_ms)
        # Keep only last 1000 measurements to prevent memory bloat
        if len(_metrics["timers"][timer_name]) > 1000:
            _metrics["timers"][timer_name] = _metrics["timers"][timer_name][-1000:]
        logger.debug("Timer %s recorded: %.2fms", timer_name, duration_ms)


def gauge(gauge_name: str, value: float) -> None:
    """Set a gauge metric value (thread-safe)."""
    with _metrics_lock:
        _metrics["gauges"][gauge_name] = value
        logger.debug("Gauge %s set to %.2f", gauge_name, value)


def histogram(histogram_name: str, value: float) -> None:
    """Record a histogram value."""
    with _metrics_lock:
        _metrics["histograms"][histogram_name].append(value)
        # Keep only last 1000 measurements
        if len(_metrics["histograms"][histogram_name]) > 1000:
            _metrics["histograms"][histogram_name] = _metrics["histograms"][histogram_name][-1000:]


def error_count(error_type: str, count: int = 1) -> None:
    """Increment error count for a specific error type."""
    with _metrics_lock:
        _metrics["error_counts"][error_type] += count
        _metrics["system_health"]["failed_requests"] += count
        logger.warning("Error %s count incremented by %d", error_type, count)


def success_count() -> None:
    """Increment success count."""
    with _metrics_lock:
        _metrics["system_health"]["successful_requests"] += 1


def request_count() -> None:
    """Increment total request count."""
    with _metrics_lock:
        _metrics["system_health"]["total_requests"] += 1


def get_metrics() -> dict[str, Any]:
    """Get current metrics snapshot with computed statistics."""
    with _metrics_lock:
        metrics = _metrics.copy()

    # Compute statistics for timers
    computed_metrics = {
        "counters": dict(metrics["counters"]),
        "timers": {},
        "gauges": metrics["gauges"],
        "histograms": {},
        "error_counts": dict(metrics["error_counts"]),
        "system_health": metrics["system_health"].copy(),
        "performance_summary": {}
    }

    # Calculate timer statistics
    for timer_name, values in metrics["timers"].items():
        if values:
            computed_metrics["timers"][timer_name] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "p50": sorted(values)[len(values) // 2],
                "p95": sorted(values)[int(len(values) * 0.95)],
                "p99": sorted(values)[int(len(values) * 0.99)],
            }

    # Calculate histogram statistics
    for hist_name, values in metrics["histograms"].items():
        if values:
            computed_metrics["histograms"][hist_name] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
            }

    # Calculate system health metrics
    total_requests = metrics["system_health"]["total_requests"]
    if total_requests > 0:
        success_rate = metrics["system_health"]["successful_requests"] / total_requests
        computed_metrics["system_health"]["success_rate"] = success_rate
        computed_metrics["system_health"]["uptime_seconds"] = time.time() - metrics["system_health"]["uptime_start"]

    return computed_metrics


def timed(timer_name: str) -> Callable[[Callable[..., _R]], Callable[..., _R]]:
    """Decorator to automatically time function execution."""

    def decorator(func: Callable[..., _R]) -> Callable[..., _R]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> _R:
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                timing(timer_name, duration_ms)

        return wrapper

    return decorator


def reset_metrics() -> None:
    """Reset all metrics (useful for testing)."""
    global _metrics
    with _metrics_lock:
        _metrics = {
            "counters": defaultdict(int),
            "timers": defaultdict(list),
            "gauges": {},
            "histograms": defaultdict(list),
            "error_counts": defaultdict(int),
            "performance_trends": defaultdict(lambda: deque(maxlen=100)),
            "system_health": {
                "uptime_start": time.time(),
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
            }
        }
    logger.info("Metrics reset")


def initialize_metrics() -> None:
    """Initialize metrics system (call at startup)."""
    global _metrics
    with _metrics_lock:
        if not _metrics:
            _metrics = {
                "counters": defaultdict(int),
                "timers": defaultdict(list),
                "gauges": {},
                "histograms": defaultdict(list),
                "error_counts": defaultdict(int),
                "performance_trends": defaultdict(lambda: deque(maxlen=100)),
                "system_health": {
                    "uptime_start": time.time(),
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                }
            }
    logger.info("Metrics system initialized")
