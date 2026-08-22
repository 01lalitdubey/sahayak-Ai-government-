"""
Normalization Schemas — Sahayak AI
=====================================
Pydantic v2 models representing normalized scheme objects and
the result envelopes returned by the normalization pipeline.
These are pure Python objects — no database interaction.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


# ── Normalized scheme ─────────────────────────────────────────────────────

class NormalizedScheme(BaseModel):
    """
    Internal representation of a government scheme after normalization.
    Maps 1-to-1 with the Scheme ORM model's writable fields.
    All fields are optional — downstream code decides what is required.
    """
    # Identification
    scheme_code: str | None = None
    name: str | None = None
    short_description: str | None = None
    full_description: str | None = None
    benefits: str | None = None

    # Classification
    scheme_type: str = "central"          # central | state
    category: str | None = None
    ministry: str | None = None
    department: str | None = None

    # Geography
    state: str | None = None
    district: str | None = None

    # Application
    application_mode: str = "online"      # online | offline | both
    application_start_date: date | None = None
    application_end_date: date | None = None

    # Links & contacts
    official_url: str | None = None
    official_pdf_url: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None

    # Flags
    is_active: bool = True
    is_featured: bool = False

    # Provenance
    source_provider: str | None = None    # e.g. "data_gov"
    source_resource_id: str | None = None
    raw_record: dict[str, Any] = Field(default_factory=dict)

    normalized_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )


# ── Validation error ──────────────────────────────────────────────────────

class ValidationError(BaseModel):
    field: str
    value: Any
    reason: str


# ── Single record result ──────────────────────────────────────────────────

class NormalizationResult(BaseModel):
    """Result of normalizing one raw record."""
    success: bool
    scheme: NormalizedScheme | None = None
    errors: list[ValidationError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    ignored_fields: list[str] = Field(default_factory=list)
    mapped_fields: list[str] = Field(default_factory=list)


# ── Batch result ──────────────────────────────────────────────────────────

class BatchNormalizationStats(BaseModel):
    total_records: int
    normalized_records: int
    failed_records: int
    warnings_count: int
    missing_fields_count: int


class BatchNormalizationResult(BaseModel):
    """Result of normalizing a batch of raw records."""
    results: list[NormalizationResult]
    stats: BatchNormalizationStats

    @property
    def successful(self) -> list[NormalizedScheme]:
        return [r.scheme for r in self.results if r.success and r.scheme is not None]

    @property
    def failed(self) -> list[NormalizationResult]:
        return [r for r in self.results if not r.success]
