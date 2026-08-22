"""
Retry Strategy — Sahayak AI Government API Client
===================================================
Centralised retry decision logic used by all HTTP clients.
Reuses calculate_retry_delay() from Phase 6.1 utils.

Retry rules:
  - RETRY  : 429, 500, 502, 503, 504, network/timeout errors
  - NO-RETRY: 400, 401, 403, 404 (client errors — retrying won't help)
"""

from __future__ import annotations

import asyncio
from typing import Callable, Awaitable, TypeVar

import httpx

from app.government_data.exceptions import (
    RateLimitException,
    APIUnavailableException,
    GovernmentAPIException,
)
from app.government_data.logger import GovtDataLogger
from app.government_data.utils import calculate_retry_delay

_logger = GovtDataLogger(__name__)

T = TypeVar("T")

# HTTP status codes that are safe to retry
RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({429, 500, 502, 503, 504})

# HTTP status codes that must NOT be retried (client errors)
NON_RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({400, 401, 403, 404, 422})


def should_retry(status_code: int) -> bool:
    """Return True if this HTTP status code warrants a retry."""
    return status_code in RETRYABLE_STATUS_CODES


def parse_retry_after(response: httpx.Response) -> int | None:
    """
    Parse the Retry-After header from an HTTP 429 response.
    Returns the number of seconds to wait, or None if header is absent/unparseable.
    """
    header = response.headers.get("retry-after") or response.headers.get("Retry-After")
    if header is None:
        return None
    try:
        return int(header)
    except (ValueError, TypeError):
        return None


async def execute_with_retry(
    fn: Callable[[], Awaitable[T]],
    *,
    max_retries: int,
    backoff_base: float,
    provider: str = "unknown",
    operation: str = "request",
) -> T:
    """
    Execute an async callable with exponential-backoff retry.

    Args:
        fn:           Async callable that performs the actual HTTP request.
        max_retries:  Maximum number of retry attempts (0 = no retries).
        backoff_base: Base value for exponential backoff (seconds).
        provider:     Provider name for log messages.
        operation:    Human-readable operation name for log messages.

    Returns:
        The return value of fn() on success.

    Raises:
        GovernmentAPIException subclass on final failure.
    """
    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await fn()

        except RateLimitException as exc:
            last_exc = exc
            if attempt >= max_retries:
                raise
            delay = float(exc.retry_after) if exc.retry_after else calculate_retry_delay(
                attempt + 1, base=backoff_base, jitter=True
            )
            _logger.retry_scheduled(attempt + 1, max_retries, delay, f"rate_limit provider={provider}")
            await asyncio.sleep(delay)

        except APIUnavailableException as exc:
            last_exc = exc
            if attempt >= max_retries:
                raise
            delay = calculate_retry_delay(attempt + 1, base=backoff_base, jitter=True)
            _logger.retry_scheduled(attempt + 1, max_retries, delay, f"unavailable provider={provider} op={operation}")
            await asyncio.sleep(delay)

        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            last_exc = exc
            if attempt >= max_retries:
                raise GovernmentAPIException(
                    message=f"Network error after {max_retries} retries: {exc}",
                    details={"provider": provider, "operation": operation},
                )
            delay = calculate_retry_delay(attempt + 1, base=backoff_base, jitter=True)
            _logger.retry_scheduled(attempt + 1, max_retries, delay, f"network_error: {type(exc).__name__}")
            await asyncio.sleep(delay)

    # Should never reach here — all paths either return or raise
    raise GovernmentAPIException(
        message=f"Exhausted {max_retries} retries for {operation}",
        details={"provider": provider},
    )
