# In agent_stack/src/utils/logger.py

import logging
from logging.handlers import TimedRotatingFileHandler
try:
    from src.config import get_settings
except ImportError:
    from config import get_settings

try:
    from rich.logging import RichHandler
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

settings = get_settings()

# Define the format for log messages
FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
LOG_FILE = "logs/app.log"


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
        LOG_FILE, when='midnight', backupCount=7
    )
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(logger_name: str) -> logging.Logger:
    """
    Configures and returns a logger with console and file handlers.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(settings.log_level.upper())

    # Add handlers only if they haven't been added before
    if not logger.handlers:
        logger.addHandler(get_console_handler())
        logger.addHandler(get_file_handler())

    # Prevents log messages from being propagated to the root logger
    logger.propagate = False

    return logger
