"""Test logging configuration to identify hanging issues."""

import logging
import sys
from pathlib import Path

# Set up detailed test logging
test_logger = logging.getLogger("test_debug")
test_logger.setLevel(logging.DEBUG)

# Create a test-specific log file
test_log_file = Path("logs/test_debug.log")
test_log_file.parent.mkdir(exist_ok=True)

# File handler for test logs
file_handler = logging.FileHandler(test_log_file, mode="w")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
)
file_handler.setFormatter(file_formatter)

# Console handler for immediate feedback
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)

# Add handlers
test_logger.addHandler(file_handler)
test_logger.addHandler(console_handler)
test_logger.propagate = False


def log_test_start(test_name: str):
    """Log the start of a test."""
    test_logger.info(f"=== STARTING TEST: {test_name} ===")


def log_test_step(step: str):
    """Log a test step."""
    test_logger.info(f"TEST STEP: {step}")


def log_test_error(error: str, exc_info=None):
    """Log a test error."""
    test_logger.error(f"TEST ERROR: {error}", exc_info=exc_info)


def log_test_complete(test_name: str, success: bool):
    """Log test completion."""
    status = "PASSED" if success else "FAILED"
    test_logger.info(f"=== TEST {status}: {test_name} ===")
