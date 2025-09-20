"""Tests for structured logging system."""

from __future__ import annotations

import json
import os
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from src.utils.logger import (
    STRUCTLOG_AVAILABLE,
    configure_structured_logging,
    get_logger,
    get_structured_logger,
    reset_logging_configuration,
)


class TestStructuredLogging:
    """Test structured logging functionality."""

    def test_configure_structured_logging_development(self):
        """Test structured logging configuration for development."""
        if not STRUCTLOG_AVAILABLE:
            pytest.skip("structlog not available")

        # Reset logging configuration
        reset_logging_configuration()

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            configure_structured_logging(log_level="DEBUG", use_json=False)

            # Get a logger and log a message
            logger = get_structured_logger("test_logger")
            logger.info("Test message", user_id=123, action="test_action")

            output = captured_output.getvalue()

            # Should contain the log message and structured data
            assert "Test message" in output
            assert "user_id" in output or "123" in output

        finally:
            sys.stdout = old_stdout

    def test_configure_structured_logging_production(self):
        """Test structured logging configuration for production."""
        if not STRUCTLOG_AVAILABLE:
            pytest.skip("structlog not available")

        # Reset logging configuration
        reset_logging_configuration()

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            configure_structured_logging(log_level="INFO", use_json=True)

            # Get a logger and log a message
            logger = get_structured_logger("test_logger")
            logger.info("Test message", user_id=123, action="test_action")

            output = captured_output.getvalue().strip()

            # Should be valid JSON
            log_data = json.loads(output)
            assert log_data["event"] == "Test message"
            assert log_data["user_id"] == 123
            assert log_data["action"] == "test_action"

        finally:
            sys.stdout = old_stdout

    def test_configure_structured_logging_without_structlog(self):
        """Test structured logging configuration when structlog is not available."""
        with patch("src.utils.logger.STRUCTLOG_AVAILABLE", False):
            # Should not raise an error
            configure_structured_logging(log_level="INFO", use_json=False)

    def test_get_structured_logger_with_structlog(self):
        """Test getting structured logger when structlog is available."""
        if not STRUCTLOG_AVAILABLE:
            pytest.skip("structlog not available")

        logger = get_structured_logger("test_logger")

        # Should be a structlog logger
        assert hasattr(logger, "info")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")

    def test_get_structured_logger_without_structlog(self):
        """Test getting structured logger when structlog is not available."""
        with patch("src.utils.logger.STRUCTLOG_AVAILABLE", False):
            logger = get_structured_logger("test_logger")

            # Should be a standard logger
            assert hasattr(logger, "info")
            assert hasattr(logger, "debug")
            assert hasattr(logger, "warning")
            assert hasattr(logger, "error")

    def test_get_logger_with_structured_logging(self):
        """Test get_logger function with structured logging enabled."""
        if not STRUCTLOG_AVAILABLE:
            pytest.skip("structlog not available")

        # Reset the configured flag
        if hasattr(get_logger, "_configured"):
            delattr(get_logger, "_configured")

        with patch("src.utils.logger.settings") as mock_settings:
            mock_settings.log_level = "DEBUG"

            logger = get_logger("test_logger")

            # Should be a structlog logger
            assert hasattr(logger, "info")
            assert hasattr(logger, "debug")
            assert hasattr(logger, "warning")
            assert hasattr(logger, "error")

    def test_get_logger_without_structured_logging(self):
        """Test get_logger function without structured logging."""
        with patch("src.utils.logger.STRUCTLOG_AVAILABLE", False):
            # Reset the configured flag
            if hasattr(get_logger, "_configured"):
                delattr(get_logger, "_configured")

            with patch("src.utils.logger.settings") as mock_settings:
                mock_settings.log_level = "DEBUG"

                logger = get_logger("test_logger")

                # Should be a standard logger
                assert hasattr(logger, "info")
                assert hasattr(logger, "debug")
                assert hasattr(logger, "warning")
                assert hasattr(logger, "error")

    def test_structured_logging_with_context(self):
        """Test structured logging with context data."""
        if not STRUCTLOG_AVAILABLE:
            pytest.skip("structlog not available")

        # Reset logging configuration
        reset_logging_configuration()

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            configure_structured_logging(log_level="INFO", use_json=True)

            # Get a logger and log with context
            logger = get_structured_logger("test_logger")
            logger = logger.bind(user_id=456, session_id="abc123")
            logger.info("User action", action="login", ip_address="192.168.1.1")

            output = captured_output.getvalue().strip()

            # Extract JSON from the output (it might have additional formatting)
            import re
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                json_output = json_match.group(0)
                log_data = json.loads(json_output)
            else:
                # If no JSON found, try to parse the whole output
                log_data = json.loads(output)

            # Should contain all context data
            assert log_data["event"] == "User action"
            assert log_data["user_id"] == 456
            assert log_data["session_id"] == "abc123"
            assert log_data["action"] == "login"
            assert log_data["ip_address"] == "192.168.1.1"

        finally:
            sys.stdout = old_stdout

    def test_structured_logging_error_handling(self):
        """Test structured logging with error information."""
        if not STRUCTLOG_AVAILABLE:
            pytest.skip("structlog not available")

        # Reset logging configuration
        reset_logging_configuration()

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            configure_structured_logging(log_level="ERROR", use_json=True)

            # Get a logger and log an error
            logger = get_structured_logger("test_logger")

            try:
                raise ValueError("Test error")
            except ValueError as e:
                logger.error("An error occurred", error=str(e), exc_info=True)

            output = captured_output.getvalue().strip()

            # Extract JSON from the output (it might have additional formatting)
            import re
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                json_output = json_match.group(0)
                # Clean up control characters and normalize whitespace
                json_output = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_output)
                json_output = re.sub(r'\s+', ' ', json_output)
                log_data = json.loads(json_output)
            else:
                # If no JSON found, try to parse the whole output
                log_data = json.loads(output)

            # Should contain error information
            assert log_data["event"] == "An error occurred"
            assert log_data["error"] == "Test error"
            assert "exception" in log_data

        finally:
            sys.stdout = old_stdout

    def test_environment_based_json_formatting(self):
        """Test that JSON formatting is used in production environment."""
        if not STRUCTLOG_AVAILABLE:
            pytest.skip("structlog not available")

        # Reset logging configuration
        reset_logging_configuration()

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            with patch.dict(os.environ, {"APP_ENV": "prod"}):
                with patch("src.utils.logger.settings") as mock_settings:
                    mock_settings.log_level = "INFO"

                    configure_structured_logging(log_level="INFO", use_json=True)
                    logger = get_structured_logger("test_logger")
                    logger.info("Production message", service="api")

                    output = captured_output.getvalue().strip()

                    # Extract JSON from the output (it might have additional formatting)
                    import re
                    json_match = re.search(r'\{.*\}', output, re.DOTALL)
                    if json_match:
                        json_output = json_match.group(0)
                        log_data = json.loads(json_output)
                    else:
                        # If no JSON found, try to parse the whole output
                        log_data = json.loads(output)

                    # Should be valid JSON in production
                    assert log_data["event"] == "Production message"
                    assert log_data["service"] == "api"

        finally:
            sys.stdout = old_stdout

    def test_development_console_formatting(self):
        """Test that console formatting is used in development environment."""
        if not STRUCTLOG_AVAILABLE:
            pytest.skip("structlog not available")

        # Reset logging configuration
        reset_logging_configuration()

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            with patch.dict(os.environ, {"APP_ENV": "dev"}):
                with patch("src.utils.logger.settings") as mock_settings:
                    mock_settings.log_level = "DEBUG"

                    logger = get_logger("test_logger")
                    logger.debug("Development message", component="test")

                    output = captured_output.getvalue()

                    # Should be human-readable format in development
                    assert "Development message" in output
                    assert "component" in output or "test" in output

        finally:
            sys.stdout = old_stdout
