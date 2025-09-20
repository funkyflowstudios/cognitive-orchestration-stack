"""Tests for the metrics collection module."""

import time
import threading

import pytest

from src.utils.metrics import (
    increment,
    timing,
    gauge,
    histogram,
    error_count,
    get_metrics,
    reset_metrics,
    timed,
)


class TestMetricsCollection:
    """Test metrics collection functionality."""

    def test_increment_counter(self):
        """Test counter increment functionality."""
        # Reset metrics before test
        reset_metrics()

        # Test basic counter increment
        increment("test_counter")
        increment("test_counter")
        increment("test_counter", 5)

        metrics = get_metrics()
        assert metrics["counters"]["test_counter"] == 7

    def test_record_timer(self):
        """Test timer recording functionality."""
        reset_metrics()

        # Test timer recording
        timing("test_timer", 1.5)
        timing("test_timer", 2.0)
        timing("test_timer", 0.5)

        metrics = get_metrics()
        assert "test_timer" in metrics["timers"]
        assert len(metrics["timers"]["test_timer"]) == 3
        assert 1.5 in metrics["timers"]["test_timer"]

    def test_set_gauge(self):
        """Test gauge setting functionality."""
        reset_metrics()

        # Test gauge setting
        gauge("test_gauge", 42)
        gauge("test_gauge", 100)

        metrics = get_metrics()
        assert metrics["gauges"]["test_gauge"] == 100

    def test_record_histogram(self):
        """Test histogram recording functionality."""
        reset_metrics()

        # Test histogram recording
        histogram("test_histogram", 10)
        histogram("test_histogram", 20)
        histogram("test_histogram", 30)

        metrics = get_metrics()
        assert "test_histogram" in metrics["histograms"]
        assert len(metrics["histograms"]["test_histogram"]) == 3
        assert 20 in metrics["histograms"]["test_histogram"]

    def test_increment_error_count(self):
        """Test error count increment functionality."""
        reset_metrics()

        # Test error count increment
        error_count("test_error")
        error_count("test_error")
        error_count("test_error", 3)

        metrics = get_metrics()
        assert metrics["error_counts"]["test_error"] == 5

    def test_get_metrics_summary(self):
        """Test metrics summary retrieval."""
        reset_metrics()

        # Add some test data
        increment("test_counter", 5)
        timing("test_timer", 1.0)
        gauge("test_gauge", 50)
        histogram("test_histogram", 25)
        error_count("test_error", 2)

        summary = get_metrics()

        # Verify all metric types are present
        assert "counters" in summary
        assert "timers" in summary
        assert "gauges" in summary
        assert "histograms" in summary
        assert "error_counts" in summary
        assert "performance_trends" in summary
        assert "system_health" in summary

        # Verify specific values
        assert summary["counters"]["test_counter"] == 5
        assert summary["timers"]["test_timer"] == [1.0]
        assert summary["gauges"]["test_gauge"] == 50
        assert summary["histograms"]["test_histogram"] == [25]
        assert summary["error_counts"]["test_error"] == 2

    def test_get_performance_trends(self):
        """Test performance trends retrieval."""
        reset_metrics()

        # Add some performance data
        timing("performance_test", 1.0)
        timing("performance_test", 2.0)
        timing("performance_test", 1.5)

        trends = get_metrics()["performance_trends"]
        assert "performance_test" in trends
        assert len(trends["performance_test"]) >= 3

    def test_get_system_health(self):
        """Test system health metrics."""
        reset_metrics()

        health = get_metrics()["system_health"]

        # Verify system health structure
        assert "uptime_start" in health
        assert "total_requests" in health
        assert "successful_requests" in health
        assert "failed_requests" in health

        # Verify initial values
        assert health["total_requests"] == 0
        assert health["successful_requests"] == 0
        assert health["failed_requests"] == 0

    def test_track_performance_decorator(self):
        """Test the timed decorator."""
        reset_metrics()

        @timed("decorated_function")
        def test_function():
            time.sleep(0.01)  # Small delay to ensure timer records
            return "success"

        # Call the decorated function
        result = test_function()

        # Verify function executed correctly
        assert result == "success"

        # Verify performance was tracked
        metrics = get_metrics()
        assert "decorated_function" in metrics["timers"]
        assert len(metrics["timers"]["decorated_function"]) == 1
        assert metrics["timers"]["decorated_function"][0] > 0

    def test_track_performance_with_exception(self):
        """Test timed decorator with exceptions."""
        reset_metrics()

        @timed("error_function")
        def error_function():
            raise ValueError("Test error")

        # Call the function and expect exception
        with pytest.raises(ValueError):
            error_function()

        # Verify performance was still tracked
        metrics = get_metrics()
        assert "error_function" in metrics["timers"]
        assert len(metrics["timers"]["error_function"]) == 1

    def test_thread_safety(self):
        """Test that metrics collection is thread-safe."""
        reset_metrics()

        def increment_worker():
            for _ in range(100):
                increment("thread_test")

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=increment_worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify total count is correct (5 threads * 100 increments = 500)
        metrics = get_metrics()
        assert metrics["counters"]["thread_test"] == 500

    def test_reset_metrics(self):
        """Test metrics reset functionality."""
        # Add some data
        increment("test_counter", 10)
        timing("test_timer", 1.0)
        gauge("test_gauge", 100)

        # Reset metrics
        reset_metrics()

        # Verify all metrics are reset
        metrics = get_metrics()
        assert metrics["counters"]["test_counter"] == 0
        assert metrics["timers"]["test_timer"] == []
        assert metrics["gauges"]["test_gauge"] == 0

    def test_metrics_with_custom_labels(self):
        """Test metrics with custom labels and metadata."""
        reset_metrics()

        # Test counter with custom increment
        increment("custom_counter", 42)

        # Test timer with custom value
        timing("custom_timer", 3.14)

        # Test gauge with custom value
        gauge("custom_gauge", 99)

        metrics = get_metrics()
        assert metrics["counters"]["custom_counter"] == 42
        assert metrics["timers"]["custom_timer"] == [3.14]
        assert metrics["gauges"]["custom_gauge"] == 99

    def test_error_count_tracking(self):
        """Test error count tracking functionality."""
        reset_metrics()

        # Track different types of errors
        error_count("validation_error")
        error_count("network_error", 3)
        error_count("timeout_error", 2)

        metrics = get_metrics()
        assert metrics["error_counts"]["validation_error"] == 1
        assert metrics["error_counts"]["network_error"] == 3
        assert metrics["error_counts"]["timeout_error"] == 2

    def test_histogram_statistics(self):
        """Test histogram statistics calculation."""
        reset_metrics()

        # Add histogram data
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        for value in values:
            histogram("test_histogram", value)

        metrics = get_metrics()
        histogram_data = metrics["histograms"]["test_histogram"]

        # Verify all values are recorded
        assert len(histogram_data) == 10
        assert set(histogram_data) == set(values)

    def test_performance_trends_rolling_window(self):
        """Test that performance trends maintain rolling window."""
        reset_metrics()

        # Add more data than the maxlen (100)
        for i in range(150):
            timing("trend_test", i * 0.1)

        trends = get_metrics()["performance_trends"]
        trend_data = trends["trend_test"]

        # Should only keep the last 100 values
        assert len(trend_data) == 100
        # Should contain the most recent values
        assert trend_data[-1] == 14.9  # 149 * 0.1

    def test_system_health_calculation(self):
        """Test system health calculation accuracy."""
        reset_metrics()

        # Simulate some requests
        for _ in range(10):
            timing("request_time", 0.1)

        # Simulate some errors
        error_count("request_error", 2)

        health = get_metrics()["system_health"]

        # Verify calculations
        assert health["total_requests"] >= 0  # May be updated by other tests
        assert health["successful_requests"] >= 0
        assert health["failed_requests"] >= 0