# In agent_stack/src/utils/logger.py

import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any

try:
    import structlog

    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

try:
    from rich.logging import RichHandler

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def _get_settings():
    """Get settings with proper import handling."""
    # Add src to path for imports
    sys.path.append(str(Path(__file__).parent.parent))

    try:
        from src.config import get_settings

        return get_settings()
    except ImportError:
        from config import get_settings

        return get_settings()


settings = _get_settings()

# Define the format for log messages
FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
LOG_FILE = "logs/app.log"


def configure_structured_logging(
    log_level: str = "INFO", use_json: bool = False
) -> None:
    """
    Configure structured logging with structlog.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Whether to use JSON formatting for production
    """
    if not STRUCTLOG_AVAILABLE:
        logging.warning(
            "structlog not available, falling back to standard logging"
        )
        return

    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",
        stream=sys.stdout,
    )

    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Add JSON renderer for production or console renderer for development
    if use_json or os.getenv("APP_ENV") == "prod":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_structured_logger(name: str) -> Any:
    """
    Get a structured logger instance.

    Args:
        name: Logger name

    Returns:
        Structured logger instance
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    else:
        # Fallback to standard logger
        return logging.getLogger(name)


def get_console_handler():
    """Returns a handler that prints log messages to the console."""
    if RICH_AVAILABLE:
        # Use Rich handler for beautiful console output
        console_handler = RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_path=False,
        )
        console_handler.setFormatter(FORMATTER)
    else:
        # Fallback to null handler for clean UI
        console_handler = logging.NullHandler()
    return console_handler


def get_file_handler():
    """Returns a handler that writes log messages to a timed rotating file."""
    # Rotates the log file every day, keeping 7 days of backups
    file_handler = TimedRotatingFileHandler(
        LOG_FILE, when="midnight", backupCount=7
    )
    file_handler.setFormatter(FORMATTER)
    return file_handler


# Global flag to track if structured logging has been configured
_structured_logging_configured = False


def get_logger(logger_name: str) -> Any:
    """
    Configures and returns a logger with console and file handlers.
    Uses structured logging if available, falls back to standard logging.
    """
    global _structured_logging_configured

    # Configure structured logging if available
    if STRUCTLOG_AVAILABLE:
        # Configure structlog once
        if not _structured_logging_configured:
            configure_structured_logging(
                log_level=settings.log_level,
                use_json=os.getenv("APP_ENV") == "prod",
            )
            _structured_logging_configured = True

        return get_structured_logger(logger_name)
    else:
        # Fallback to standard logging
        logger = logging.getLogger(logger_name)
        logger.setLevel(settings.log_level.upper())

        # Add handlers only if they haven't been added before
        if not logger.handlers:
            logger.addHandler(get_console_handler())
            logger.addHandler(get_file_handler())

        # Prevents log messages from being propagated to the root logger
        logger.propagate = False

        return logger
