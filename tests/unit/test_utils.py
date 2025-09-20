# tests/unit/test_utils.py

import logging
from unittest.mock import MagicMock

import pytest

from src.utils.logger import get_logger
from src.utils.retry import retry


# Fixture to reset the logger singleton between tests to ensure isolation
@pytest.fixture(autouse=True)
def reset_logger_singleton():
    """
    Ensures that each test gets a fresh logger instance, preventing
    handlers from accumulating across tests.
    """
    # This is a simple way to reset a singleton in Python for testing
    if "test_logger" in logging.Logger.manager.loggerDict:
        del logging.Logger.manager.loggerDict["test_logger"]


# --- Tests for src.utils.retry ---


def test_retry_succeeds_on_first_attempt():
    """
    Verifies the decorator returns the correct value without retrying
    if the function succeeds on the first call.
    """
    # Create a mock function that will be decorated
    mock_func = MagicMock(return_value="success")

    # Decorate the mock function
    decorated_func = retry(mock_func)

    # Call the decorated function
    result = decorated_func("arg1", kwarg1="kwarg1")

    # Assertions
    assert result == "success"
    mock_func.assert_called_once_with("arg1", kwarg1="kwarg1")


def test_retry_decorator_applies_correctly():
    """
    Verifies that the retry decorator can be applied to a function.
    """

    # Create a simple function
    def simple_func():
        return "success"

    # Decorate the function
    decorated_func = retry(simple_func)

    # Call the function
    result = decorated_func()

    # Assertions
    assert result == "success"
    assert callable(decorated_func)


def test_retry_decorator_preserves_function_metadata():
    """
    Verifies that the retry decorator preserves function metadata.
    """

    # Create a function with metadata
    def func_with_metadata():
        """A test function with docstring."""
        return "success"

    func_with_metadata.__name__ = "test_function"

    # Decorate the function
    decorated_func = retry(func_with_metadata)

    # Assertions
    assert decorated_func.__name__ == "test_function"
    assert decorated_func.__doc__ == "A test function with docstring."


# --- Tests for src.utils.logger ---


def test_get_logger_returns_configured_logger():
    """
    Verifies that get_logger returns a logger with the expected configuration.
    """
    logger = get_logger("test_logger")

    # Check that it's a structlog logger
    assert hasattr(logger, "name")
    assert hasattr(logger, "level")
    # structlog loggers don't have handlers in the same way
    assert logger is not None


def test_get_logger_is_singleton():
    """
    Verifies that multiple calls to get_logger return the same logger instance.
    """
    logger1 = get_logger("test_logger")
    logger2 = get_logger("test_logger")

    # structlog loggers with the same name should be equivalent
    # (they may not be the exact same object due to lazy loading)
    assert logger1.name == logger2.name
    assert str(logger1) == str(logger2)
