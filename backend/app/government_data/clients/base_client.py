"""
Base Government API Client — Sahayak AI
=========================================
Abstract async HTTP client that all provider-specific clients inherit.
Handles: connection pooling, timeouts, auth hooks, retry, logging.
Provider clients only override _get_auth_headers() and implement
their own query/response methods.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.government_data.clients.response_models import GovernmentAPIResponse, HealthCheckResult
from app.government_data.clients.retry import (
    execute_with_retry,
    should_retry,
    parse_retry_after,
    NON_RETRYABLE_STATUS_CODES,
)
from app.government_data.config import GovtDataSettings, govt_settings
from app.government_data.exceptions import (
    AuthenticationException,
    RateLimitException,
    APIUnavailableException,
    InvalidResponseException,
    GovernmentAPIException,
)
from app.government_data.logger import GovtDataLogger


class BaseGovernmentClient(ABC):
    """
    Abstract base for all government API HTTP clients.

    Subclass this for every provider:
        class DataGovClient(BaseGovernmentClient):
            PROVIDER_NAME = "data_gov"
            ...

    Lifecycle:
        async with DataGovClient() as client:
            result = await client.get_dataset("resource-id")
        # Connection pool is automatically closed on exit
    """

    PROVIDER_NAME: str = "base"

    def __init__(self, settings: GovtDataSettings | None = None) -> None:
        self._settings = settings or govt_settings
        self._logger = GovtDataLogger(f"client.{self.PROVIDER_NAME}")
        self._client: httpx.AsyncClient | None = None
        self._logger.config_loaded(self.PROVIDER_NAME)

    # ── Context manager ───────────────────────────────────────────────────

    async def __aenter__(self) -> "BaseGovernmentClient":
        await self._ensure_client()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def _ensure_client(self) -> None:
        """Lazily create the httpx.AsyncClient with production-grade settings."""
        if self._client is None or self._client.is_closed:
            timeout = httpx.Timeout(
                connect=min(10.0, self._settings.GOVT_REQUEST_TIMEOUT / 3),
                read=float(self._settings.GOVT_REQUEST_TIMEOUT),
                write=float(self._settings.GOVT_REQUEST_TIMEOUT),
                pool=float(self._settings.GOVT_REQUEST_TIMEOUT),
            )
            limits = httpx.Limits(
                max_keepalive_connections=20,
                max_connections=50,
                keepalive_expiry=30.0,
            )
            self._client = httpx.AsyncClient(
                timeout=timeout,
                limits=limits,
                http2=False,   # data.gov.in does not support HTTP/2
                follow_redirects=True,
                headers=self._default_headers(),
            )

    async def close(self) -> None:
        """Gracefully close the connection pool."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
            self._logger.info("Connection pool closed for provider=%s", self.PROVIDER_NAME)

    # ── Headers ───────────────────────────────────────────────────────────

    def _default_headers(self) -> dict[str, str]:
        """Default headers sent with every request."""
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": f"SahayakAI/1.0 ({self.PROVIDER_NAME}-client)",
        }

    @abstractmethod
    def _get_auth_headers(self) -> dict[str, str]:
        """
        Return authentication headers for this provider.
        Implemented by each concrete client.
        NEVER log the returned dict.
        """
        ...

    # ── Core request ──────────────────────────────────────────────────────

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute one HTTP request with retry logic.

        Returns parsed JSON dict on success.
        Raises appropriate GovernmentAPIException subclass on failure.
        """
        await self._ensure_client()
        assert self._client is not None

        headers = {**self._get_auth_headers(), **(extra_headers or {})}
        start_ms = time.monotonic() * 1000

        self._logger.info(
            "Request started — provider=%s method=%s url=%s",
            self.PROVIDER_NAME, method, url,
        )

        async def _do_request() -> dict[str, Any]:
            response = await self._client.request(  # type: ignore[union-attr]
                method,
                url,
                params=params,
                json=json,
                headers=headers,
            )
            elapsed = time.monotonic() * 1000 - start_ms

            self._logger.info(
                "Response received — provider=%s status=%d latency=%.0fms url=%s",
                self.PROVIDER_NAME, response.status_code, elapsed, url,
            )

            # ── Handle specific status codes ──────────────────────────────

            if response.status_code == 401:
                self._logger.auth_failed(self.PROVIDER_NAME, response.status_code)
                raise AuthenticationException(
                    details={"status_code": 401, "url": url},
                )

            if response.status_code == 429:
                retry_after = parse_retry_after(response)
                self._logger.rate_limited(self.PROVIDER_NAME, retry_after)
                raise RateLimitException(
                    retry_after=retry_after,
                    details={"url": url},
                )

            if response.status_code in {500, 502, 503, 504}:
                raise APIUnavailableException(
                    message=f"Provider returned {response.status_code}.",
                    details={"status_code": response.status_code, "url": url},
                )

            if response.status_code == 404:
                raise GovernmentAPIException(
                    message=f"Resource not found: {url}",
                    error_code="GOVT_NOT_FOUND",
                    details={"status_code": 404, "url": url},
                )

            if response.status_code >= 400:
                raise GovernmentAPIException(
                    message=f"Client error {response.status_code} for {url}",
                    details={"status_code": response.status_code},
                )

            # ── Parse JSON ────────────────────────────────────────────────
            try:
                return response.json()
            except Exception as exc:
                raise InvalidResponseException(
                    message="Response body is not valid JSON.",
                    details={"url": url, "error": str(exc)},
                )

        return await execute_with_retry(
            _do_request,
            max_retries=self._settings.GOVT_MAX_RETRIES,
            backoff_base=self._settings.GOVT_BACKOFF_FACTOR,
            provider=self.PROVIDER_NAME,
            operation=f"{method} {url}",
        )

    # ── Health check (default implementation) ─────────────────────────────

    @abstractmethod
    async def health_check(self) -> HealthCheckResult:
        """
        Ping the provider and return connectivity + latency information.
        Each client implements this against their own health endpoint.
        """
        ...
