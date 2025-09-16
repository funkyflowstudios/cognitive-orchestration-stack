# src/utils/retry.py
"""Reusable retry decorators using Tenacity.

All external I/O that may experience transient network failures should be
wrapped with :func:`retry` to ensure graceful automatic retries.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from tenacity import retry as _retry
from tenacity import stop_after_attempt, wait_exponential

_R = TypeVar("_R")


def retry(func: Callable[..., _R]) -> Callable[..., _R]:  # noqa: D401
    """Apply a sensible default retry policy (3 attempts, exp. back-off)."""

    wrapped = _retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    )(func)

    @wraps(func)
    def _wrapper(*args: Any, **kwargs: Any) -> _R:
        return wrapped(*args, **kwargs)

    return _wrapper
