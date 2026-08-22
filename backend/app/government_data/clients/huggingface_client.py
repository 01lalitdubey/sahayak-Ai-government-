"""
HuggingFace Datasets Server Client — Sahayak AI
=================================================
Fetches the smartduketech/indian-government-schemes-2025 dataset
(4,693 structured Indian Government Schemes) using the public
HuggingFace Datasets Server Rows API.

API:
  GET https://datasets-server.huggingface.co/rows
      ?dataset=smartduketech/indian-government-schemes-2025
      &config=default
      &split=train
      &offset=0
      &length=100

Response:
  {
    "features": [...],
    "rows": [{"row_idx": 0, "row": {...}}, ...],
    "num_rows": 4693,
    "offset": 0
  }

The client extracts rows[].row before returning — downstream normalizers
receive the same flat dict they always expect.
"""

from __future__ import annotations

import time
from typing import Any

from app.government_data.clients.base_client import BaseGovernmentClient
from app.government_data.clients.response_models import (
    GovernmentAPIResponse,
    GovernmentMetadata,
    HealthCheckResult,
    parse_huggingface_rows_response,
)
from app.government_data.config import GovtDataSettings
from app.government_data.constants import (
    HF_ROWS_BASE_URL,
    HF_METADATA_BASE_URL,
    HF_DEFAULT_DATASET,
    HF_DEFAULT_CONFIG,
    HF_DEFAULT_SPLIT,
    HF_MAX_LENGTH,
    HF_TOKEN_HEADER,
)
from app.government_data.exceptions import (
    GovernmentAPIException,
    InvalidResponseException,
)
from app.government_data.logger import GovtDataLogger

_logger = GovtDataLogger("client.huggingface")


class HuggingFaceClient(BaseGovernmentClient):
    """
    Client for HuggingFace Datasets Server.

    Public datasets (like indian-government-schemes-2025) need no token.
    Private datasets: set HF_TOKEN in .env.

    Usage:
        async with HuggingFaceClient() as client:
            # Fetch first 100 rows
            result = await client.get_dataset(offset=0, length=100)

            # Fetch ALL rows (auto-paginated)
            async for batch in client.iter_all_rows():
                process(batch.records)

            # Health check
            health = await client.health_check()
    """

    PROVIDER_NAME = "huggingface"

    # Rows API caps at 100 per request
    MAX_LENGTH: int = HF_MAX_LENGTH

    def __init__(
        self,
        settings: GovtDataSettings | None = None,
        dataset: str | None = None,
        config: str | None = None,
        split: str | None = None,
    ) -> None:
        super().__init__(settings)
        self._dataset = dataset or self._settings.HF_DATASET
        self._config = config or self._settings.HF_CONFIG
        self._split = split or self._settings.HF_SPLIT
        self._hf_token: str | None = self._settings.HF_TOKEN or None

    # ── Auth ──────────────────────────────────────────────────────────────

    def _get_auth_headers(self) -> dict[str, str]:
        """
        HuggingFace uses Bearer token for private datasets.
        Public datasets (like our target) work without any token.
        """
        if self._hf_token:
            return {HF_TOKEN_HEADER: f"Bearer {self._hf_token}"}
        return {}

    # ── Query builder ─────────────────────────────────────────────────────

    def build_query(
        self,
        *,
        offset: int = 0,
        length: int | None = None,
    ) -> dict[str, Any]:
        """
        Build query params for the HuggingFace Rows API.
        """
        return {
            "dataset": self._dataset,
            "config": self._config,
            "split": self._split,
            "offset": offset,
            "length": min(length or self.MAX_LENGTH, self.MAX_LENGTH),
        }

    # ── Core data fetch ───────────────────────────────────────────────────

    async def get_dataset(
        self,
        offset: int = 0,
        length: int | None = None,
    ) -> GovernmentAPIResponse:
        """
        Fetch one page of rows from the HuggingFace Rows API.

        Args:
            offset: Pagination offset (0-indexed)
            length: Number of rows to fetch (max 100 per request)

        Returns:
            GovernmentAPIResponse with records + pagination
        """
        actual_length = min(length or self.MAX_LENGTH, self.MAX_LENGTH)
        params = self.build_query(offset=offset, length=actual_length)

        self._logger.info(
            "Fetching rows — dataset=%s offset=%d length=%d",
            self._dataset, offset, actual_length,
        )

        raw = await self._request("GET", HF_ROWS_BASE_URL, params=params)
        response = parse_huggingface_rows_response(
            raw,
            dataset=self._dataset,
            offset=offset,
            length=actual_length,
        )

        self._logger.info(
            "Rows fetched — dataset=%s records=%d total=%d offset=%d",
            self._dataset,
            response.record_count,
            response.pagination.total if response.pagination else 0,
            offset,
        )
        return response

    async def get_total_rows(self) -> int:
        """Fetch total row count from the HF /info endpoint."""
        try:
            url = f"https://datasets-server.huggingface.co/info?dataset={self._dataset}"
            await self._ensure_client()
            assert self._client is not None
            resp = await self._client.get(url, timeout=15.0)
            if resp.status_code == 200:
                data = resp.json()
                splits = (data.get("dataset_info", {})
                              .get(self._config, {})
                              .get("splits", {}))
                split_info = splits.get(self._split, {})
                return int(split_info.get("num_examples", 0))
        except Exception:
            pass
        return 0

    async def get_all_rows(
        self,
        max_records: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Download every row in the dataset by auto-paginating.

        Args:
            max_records: Optional cap on total records (None = all)

        Returns:
            Flat list of all row dicts.
        """
        all_records: list[dict[str, Any]] = []
        offset = 0
        total_available: int | None = None

        while True:
            if max_records and len(all_records) >= max_records:
                break

            remaining = None
            if max_records:
                remaining = max_records - len(all_records)

            response = await self.get_dataset(
                offset=offset,
                length=min(remaining or self.MAX_LENGTH, self.MAX_LENGTH),
            )

            if not response.records:
                break

            all_records.extend(response.records)

            if total_available is None and response.pagination:
                total_available = response.pagination.total
                self._logger.info(
                    "Total rows available: %d", total_available
                )

            # Stop if we've fetched everything
            if response.pagination and not response.pagination.has_more:
                break
            if not response.pagination:
                break

            offset += len(response.records)

        self._logger.info(
            "All rows downloaded — total=%d dataset=%s",
            len(all_records), self._dataset,
        )
        return all_records

    async def get_metadata(self) -> GovernmentMetadata:
        """
        Fetch dataset metadata from the HuggingFace API.

        Returns:
            GovernmentMetadata with title, description, download count, etc.
        """
        url = f"{HF_METADATA_BASE_URL}/{self._dataset}"

        self._logger.info("Fetching metadata — dataset=%s", self._dataset)

        try:
            raw = await self._request("GET", url)
        except GovernmentAPIException:
            # Metadata is best-effort — don't fail the whole pipeline
            return GovernmentMetadata(
                resource_id=self._dataset,
                title=self._dataset,
            )

        return GovernmentMetadata(
            resource_id=self._dataset,
            title=raw.get("id") or self._dataset,
            description=raw.get("cardData", {}).get("description") if isinstance(raw.get("cardData"), dict) else None,
            organization=raw.get("author"),
            last_updated=raw.get("lastModified"),
            extra={
                "downloads": raw.get("downloads", 0),
                "likes": raw.get("likes", 0),
                "tags": raw.get("tags", []),
            },
        )

    # ── Health check ──────────────────────────────────────────────────────

    async def health_check(self) -> HealthCheckResult:
        """
        Verify connectivity to HuggingFace Datasets Server.
        Fetches 1 row to confirm the dataset is reachable and counts total rows.

        Returns:
            HealthCheckResult with connected, latency_ms, and total rows.
        """
        start = time.monotonic()
        try:
            await self._ensure_client()
            params = self.build_query(offset=0, length=1)

            assert self._client is not None
            resp = await self._client.get(
                HF_ROWS_BASE_URL,
                params=params,
                timeout=15.0,
            )
            latency_ms = round((time.monotonic() - start) * 1000, 2)

            if resp.status_code >= 500:
                return HealthCheckResult(
                    provider=self.PROVIDER_NAME,
                    connected=False,
                    latency_ms=latency_ms,
                    message=f"HTTP {resp.status_code}",
                )

            try:
                data = resp.json()
                total_rows = data.get("num_rows", 0)
                message = f"OK — dataset has {total_rows:,} rows"
            except Exception:
                total_rows = 0
                message = "OK (could not parse row count)"

            return HealthCheckResult(
                provider=self.PROVIDER_NAME,
                connected=resp.status_code < 400,
                latency_ms=latency_ms,
                message=message,
                extra={
                    "dataset": self._dataset,
                    "total_rows": total_rows,
                },
            )

        except Exception as exc:
            latency_ms = round((time.monotonic() - start) * 1000, 2)
            return HealthCheckResult(
                provider=self.PROVIDER_NAME,
                connected=False,
                latency_ms=latency_ms,
                message=f"Connection failed: {type(exc).__name__}: {exc}",
            )
