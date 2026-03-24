"""Async utilities: rate limiter, retry, logging."""

from __future__ import annotations
import asyncio
import time
import sys
from typing import TypeVar, Callable, Awaitable, Any

from pipeline.config import MAX_RETRIES, RETRY_BACKOFF_BASE, LOG_PREFIX

T = TypeVar("T")


def log(message: str, level: str = "info") -> None:
    """Print a log message with BYS prefix."""
    symbol = {"info": "→", "success": "✓", "error": "✗", "warn": "⚠"}
    prefix = symbol.get(level, "→")
    timestamp = time.strftime("%H:%M:%S")
    print(f"{timestamp} {LOG_PREFIX} {prefix} {message}", file=sys.stderr)


class RateLimiter:
    """Token bucket rate limiter for async operations."""

    def __init__(self, max_concurrent: int) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def __aenter__(self) -> RateLimiter:
        await self._semaphore.acquire()
        return self

    async def __aexit__(self, *args: Any) -> None:
        self._semaphore.release()


async def retry_async(
    fn: Callable[..., Awaitable[T]],
    *args: Any,
    max_retries: int = MAX_RETRIES,
    backoff_base: float = RETRY_BACKOFF_BASE,
    retry_on: tuple[type[Exception], ...] = (Exception,),
    label: str = "call",
) -> T:
    """Retry an async function with exponential backoff."""
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            return await fn(*args)
        except retry_on as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = backoff_base ** attempt
                log(f"Retry {attempt + 1}/{max_retries} for {label} "
                    f"(waiting {wait:.1f}s): {e}", "warn")
                await asyncio.sleep(wait)
            else:
                log(f"Failed after {max_retries} retries for {label}: {e}", "error")
    raise last_error  # type: ignore[misc]


class ProgressTracker:
    """Simple progress tracker for batch operations."""

    def __init__(self, total: int, label: str = "items") -> None:
        self.total = total
        self.label = label
        self.completed = 0
        self.errors = 0
        self._lock = asyncio.Lock()

    async def tick(self, success: bool = True) -> None:
        async with self._lock:
            self.completed += 1
            if not success:
                self.errors += 1
            if self.completed % 5 == 0 or self.completed == self.total:
                log(f"{self.label}: {self.completed}/{self.total} "
                    f"({self.errors} errors)")
