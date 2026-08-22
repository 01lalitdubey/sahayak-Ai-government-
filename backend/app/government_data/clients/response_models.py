"""
Government API Response Models — Sahayak AI
=============================================
Pydantic v2 models that represent validated API responses.
All HTTP responses are parsed into these models before being
returned to callers — raw dicts never escape the client layer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.government_data.exceptions import InvalidResponseException


# ── Pagination ────────────────────────────────────────────────────────────

class GovernmentPagination(BaseModel):
    """Pagination metadata extracted from a government API response."""
    total: int = Field(ge=0, description="Total number of records available")
    count: int = Field(ge=0, description="Number of records in this page")
    limit: int = Field(ge=1, description="Page size requested")
    offset: int = Field(ge=0, description="Offset of this page")

    @property
    def has_more(self) -> bool:
        return self.offset + self.count < self.total

    @property
    def next_offset(self) -> int | None:
        return self.offset + self.count if self.has_more else None


# ── Metadata ──────────────────────────────────────────────────────────────

class GovernmentMetadata(BaseModel):
    """Metadata about a government dataset / resource."""
    resource_id: str = Field(description="Unique resource identifier")
    title: str | None = Field(default=None, description="Human-readable dataset title")
    description: str | None = Field(default=None)
    organization: str | None = Field(default=None)
    last_updated: str | None = Field(default=None)
    format: str | None = Field(default=None)
    source_url: str | None = Field(default=None)
    extra: dict[str, Any] = Field(default_factory=dict)


# ── Main API response ─────────────────────────────────────────────────────

class GovernmentAPIResponse(BaseModel):
    """
    Validated wrapper around a government API JSON response.
    Created by the client after receiving and validating an HTTP response.
    """
    provider: str = Field(description="Provider name e.g. 'data_gov'")
    resource_id: str | None = Field(default=None)
    status: str = Field(description="API-level status string if provided")
    records: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of raw record dicts from the API",
    )
    pagination: GovernmentPagination | None = None
    metadata: GovernmentMetadata | None = None
    raw_response: dict[str, Any] = Field(
        default_factory=dict,
        description="The full original response dict (for debugging)",
    )
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
    )

    @property
    def record_count(self) -> int:
        return len(self.records)

    @property
    def has_more(self) -> bool:
        return self.pagination.has_more if self.pagination else False


# ── Error response ────────────────────────────────────────────────────────

class GovernmentAPIError(BaseModel):
    """Structured representation of an error returned by a government API."""
    provider: str
    status_code: int
    error_code: str | None = None
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
    )


# ── Health check result ───────────────────────────────────────────────────

class HealthCheckResult(BaseModel):
    """Result of a provider health check."""
    provider: str
    connected: bool
    latency_ms: float | None = None
    api_version: str | None = None
    message: str = "OK"
    extra: dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
    )


# ── Response parser ───────────────────────────────────────────────────────

def parse_data_gov_response(
    raw: dict[str, Any],
    resource_id: str | None = None,
) -> GovernmentAPIResponse:
    """
    Parse and validate a data.gov.in API JSON response into a
    GovernmentAPIResponse model.
    """
    if not isinstance(raw, dict):
        raise InvalidResponseException(
            message="Expected a JSON object from data.gov.in, got a different type.",
            details={"got_type": type(raw).__name__},
        )

    status = raw.get("status", "")
    records = raw.get("records", [])

    if not isinstance(records, list):
        raise InvalidResponseException(
            message="'records' field is not a list in data.gov.in response.",
            details={"records_type": type(records).__name__},
        )

    pagination: GovernmentPagination | None = None
    try:
        pagination = GovernmentPagination(
            total=int(raw.get("total", 0)),
            count=int(raw.get("count", len(records))),
            limit=int(raw.get("limit", len(records))),
            offset=int(raw.get("offset", 0)),
        )
    except (ValueError, TypeError):
        pass

    return GovernmentAPIResponse(
        provider="data_gov",
        resource_id=resource_id,
        status=str(status),
        records=records,
        pagination=pagination,
        raw_response=raw,
    )


def parse_huggingface_rows_response(
    raw: dict[str, Any],
    dataset: str,
    offset: int = 0,
    length: int = 100,
) -> GovernmentAPIResponse:
    """
    Parse the HuggingFace Datasets Server /rows response.

    HF response shape:
    {
        "features": [...],
        "rows": [{"row_idx": 0, "row": {...}, "truncated_cells": []}, ...],
        "num_rows": 4693,
        "offset": 0
    }

    Extracts rows[].row before returning, so the normalization engine
    receives the same flat dict it always expects.

    Raises:
        InvalidResponseException: if the response is malformed.
    """
    if not isinstance(raw, dict):
        raise InvalidResponseException(
            message="Expected a JSON object from HuggingFace, got a different type.",
            details={"got_type": type(raw).__name__},
        )

    rows_list = raw.get("rows", [])
    if not isinstance(rows_list, list):
        raise InvalidResponseException(
            message="'rows' field is not a list in HuggingFace response.",
            details={"rows_type": type(rows_list).__name__},
        )

    # Extract the nested .row dict from each entry
    records: list[dict[str, Any]] = []
    for entry in rows_list:
        if isinstance(entry, dict) and "row" in entry:
            records.append(entry["row"])
        elif isinstance(entry, dict):
            records.append(entry)

    num_rows = raw.get("num_rows") or raw.get("total") or 0
    try:
        total = int(num_rows) if num_rows else len(records)
    except (ValueError, TypeError):
        total = len(records)

    pagination = GovernmentPagination(
        total=total,
        count=len(records),
        limit=length,
        offset=offset,
    )

    return GovernmentAPIResponse(
        provider="huggingface",
        resource_id=dataset,
        status="ok",
        records=records,
        pagination=pagination,
        raw_response=raw,
    )
