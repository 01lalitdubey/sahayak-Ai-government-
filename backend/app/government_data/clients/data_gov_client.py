"""
data.gov.in API Client — Sahayak AI
======================================
Concrete client for the Indian Open Government Data Platform.

API documentation: https://data.gov.in/help/how-use-datasets-apis
Base URL: https://api.data.gov.in/resource/{resource_id}

Request flow:
  DataGovClient.get_dataset(resource_id)
    → _build_query(resource_id, offset, limit, ...)
    → BaseGovernmentClient._request("GET", url, params=query)
    → parse_data_gov_response(raw_json)
    → GovernmentAPIResponse
"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlencode

from app.government_data.clients.base_client import BaseGovernmentClient
from app.government_data.clients.response_models import (
    GovernmentAPIResponse,
    HealthCheckResult,
    parse_data_gov_response,
)
from app.government_data.config import GovtDataSettings
from app.government_data.constants import (
    DATA_GOV_BASE_URL,
    DATA_GOV_API_KEY_HEADER,
    ACCEPT_JSON,
)
from app.government_data.exceptions import (
    ConfigurationException,
    GovernmentAPIException,
)
from app.government_data.security import get_auth_headers, validate_api_key


class DataGovClient(BaseGovernmentClient):
    """
    Client for data.gov.in — Indian Open Government Data Platform.

    Usage:
        async with DataGovClient() as client:
            result = await client.get_dataset("your-resource-id")
            for record in result.records:
                print(record)
    """

    PROVIDER_NAME = "data_gov"

    def __init__(self, settings: GovtDataSettings | None = None) -> None:
        super().__init__(settings)
        self._base_url = self._settings.DATA_GOV_BASE_URL or DATA_GOV_BASE_URL
        self._api_key: str | None = self._settings.DATA_GOV_API_KEY or None

    # ── Auth ──────────────────────────────────────────────────────────────

    def _get_auth_headers(self) -> dict[str, str]:
        """
        data.gov.in authenticates via 'api-key' query parameter, NOT a header.
        Returns empty dict — auth is injected into query params by _build_query().
        """
        return {}

    def _require_api_key(self) -> str:
        """Return validated API key or raise ConfigurationException."""
        if not self._api_key:
            raise ConfigurationException(
                message="DATA_GOV_API_KEY is not set. "
                        "Register at https://data.gov.in/user/register to obtain a key.",
                details={"provider": self.PROVIDER_NAME},
            )
        return validate_api_key(self._api_key, provider=self.PROVIDER_NAME)

    # ── Query builder ─────────────────────────────────────────────────────

    def build_query(
        self,
        resource_id: str,
        *,
        offset: int = 0,
        limit: int | None = None,
        filters: dict[str, Any] | None = None,
        sort: str | None = None,
        fields: list[str] | None = None,
        fmt: str = "json",
    ) -> dict[str, Any]:
        """
        Build the query parameter dict for a data.gov.in API request.

        Args:
            resource_id: The dataset resource UUID
            offset:      Record offset for pagination (default 0)
            limit:       Max records to return (default from settings)
            filters:     Dict of {field: value} equality filters
            sort:        Field name to sort by (prefix with '-' for desc)
            fields:      List of field names to include in response
            fmt:         Response format — "json" (default) or "csv"

        Returns:
            Dict of query parameters ready for httpx params=
        """
        api_key = self._require_api_key()
        page_size = limit if limit is not None else self._settings.GOVT_DEFAULT_PAGE_SIZE

        params: dict[str, Any] = {
            "api-key": api_key,
            "format": fmt,
            "offset": offset,
            "limit": page_size,
        }

        if filters:
            for field, value in filters.items():
                params[f"filters[{field}]"] = value

        if sort:
            params["sort[]"] = sort

        if fields:
            params["fields"] = ",".join(fields)

        return params

    def build_url(self, resource_id: str) -> str:
        """Return the full API URL for a resource."""
        return f"{self._base_url}/{resource_id}"

    # ── Public API methods ────────────────────────────────────────────────

    async def get_dataset(
        self,
        resource_id: str,
        *,
        offset: int = 0,
        limit: int | None = None,
        filters: dict[str, Any] | None = None,
        sort: str | None = None,
        fields: list[str] | None = None,
    ) -> GovernmentAPIResponse:
        """
        Fetch one page of records from a data.gov.in resource.

        Args:
            resource_id: The UUID of the resource (from data.gov.in)
            offset:      Pagination offset
            limit:       Number of records per page
            filters:     Field equality filters
            sort:        Sort field (prefix '-' for descending)
            fields:      Fields to include

        Returns:
            GovernmentAPIResponse with records + pagination
        """
        url = self.build_url(resource_id)
        params = self.build_query(
            resource_id,
            offset=offset,
            limit=limit,
            filters=filters,
            sort=sort,
            fields=fields,
        )

        self._logger.info(
            "Fetching dataset — resource_id=%s offset=%d",
            resource_id, offset,
        )

        raw = await self._request("GET", url, params=params)
        response = parse_data_gov_response(raw, resource_id=resource_id)

        self._logger.info(
            "Dataset fetched — resource_id=%s records=%d total=%d",
            resource_id,
            response.record_count,
            response.pagination.total if response.pagination else 0,
        )
        return response

    async def get_resource(self, resource_id: str) -> GovernmentAPIResponse:
        """
        Alias for get_dataset() — fetches first page with default settings.
        """
        return await self.get_dataset(resource_id)

    async def search_resources(
        self,
        query: str,
        *,
        offset: int = 0,
        limit: int | None = None,
    ) -> GovernmentAPIResponse:
        """
        Search across data.gov.in resources using the catalog endpoint.
        NOTE: The catalog endpoint has a different URL pattern.
        """
        from app.government_data.constants import DATA_GOV_CATALOG_URL

        api_key = self._require_api_key()
        page_size = limit or self._settings.GOVT_DEFAULT_PAGE_SIZE

        params: dict[str, Any] = {
            "api-key": api_key,
            "format": "json",
            "q": query,
            "offset": offset,
            "limit": page_size,
        }

        self._logger.info("Searching resources — query=%r offset=%d", query, offset)
        raw = await self._request("GET", DATA_GOV_CATALOG_URL, params=params)
        response = parse_data_gov_response(raw, resource_id=None)
        self._logger.info("Search complete — results=%d", response.record_count)
        return response

    async def list_resources(
        self,
        offset: int = 0,
        limit: int | None = None,
    ) -> GovernmentAPIResponse:
        """
        List available resources on data.gov.in catalog.
        """
        return await self.search_resources("", offset=offset, limit=limit)

    # ── Health check ──────────────────────────────────────────────────────

    async def health_check(self) -> HealthCheckResult:
        """
        Verify connectivity to data.gov.in.
        Uses a lightweight catalog call to measure latency.

        Returns:
            HealthCheckResult with connected=True and latency_ms on success.
            HealthCheckResult with connected=False on failure.
        """
        start = time.monotonic()
        try:
            await self._ensure_client()
            api_key = self._require_api_key()
            params = {"api-key": api_key, "format": "json", "limit": 1}

            import httpx as _httpx
            assert self._client is not None
            resp = await self._client.get(
                DATA_GOV_BASE_URL,
                params=params,
                timeout=10.0,
            )
            latency_ms = (time.monotonic() - start) * 1000

            connected = resp.status_code < 500

            return HealthCheckResult(
                provider=self.PROVIDER_NAME,
                connected=connected,
                latency_ms=round(latency_ms, 2),
                message="OK" if connected else f"HTTP {resp.status_code}",
            )

        except ConfigurationException as exc:
            return HealthCheckResult(
                provider=self.PROVIDER_NAME,
                connected=False,
                message=f"Configuration error: {exc.message}",
            )
        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            return HealthCheckResult(
                provider=self.PROVIDER_NAME,
                connected=False,
                latency_ms=round(latency_ms, 2),
                message=f"Connection failed: {type(exc).__name__}: {exc}",
            )
