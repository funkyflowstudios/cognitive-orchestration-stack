from __future__ import annotations

"""Centralized logger for the stack."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

log_file = LOG_DIR / "app.log"

# Standard log format
_FMT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

# Use cached configuration to avoid adding handlers multiple times
def get_logger(name: str | None = None) -> logging.Logger:
    """Return configured logger instance.

    Creates a rotating file handler (5 MB, 3 backups) and a console stream
    handler. Both share the same formatter.
    """
    # Obtain (or create) logger
    logger = logging.getLogger(name or "cog-stack")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(_FMT)

    # File handler
    fh = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=3)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
