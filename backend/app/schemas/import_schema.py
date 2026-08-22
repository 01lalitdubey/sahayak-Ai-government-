"""
Import Pipeline Schemas — Sahayak AI
=======================================
Pydantic v2 request/response contracts for the Government Import API.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from app.government_data.types import ImportMode, ImportStatus


# ── Request ───────────────────────────────────────────────────────────────

class ImportRequest(BaseModel):
    resource_id: str = Field(description="data.gov.in resource UUID")
    mode: ImportMode = ImportMode.MANUAL
    max_records: int | None = Field(default=None, ge=1, le=100000)
    dry_run: bool = Field(default=False, description="Preview only — no DB writes")


class PreviewRequest(BaseModel):
    resource_id: str
    limit: int = Field(default=20, ge=1, le=100)


# ── Statistics ────────────────────────────────────────────────────────────

class ImportStatistics(BaseModel):
    downloaded: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    duplicates: int = 0
    duration_ms: float = 0.0


# ── Record-level outcome ──────────────────────────────────────────────────

class RecordOutcome(BaseModel):
    action: str        # "created" | "updated" | "skipped" | "failed"
    scheme_code: str | None = None
    scheme_name: str | None = None
    reason: str | None = None


# ── Import report ─────────────────────────────────────────────────────────

class ImportReport(BaseModel):
    import_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    resource_id: str
    mode: str
    status: str
    statistics: ImportStatistics
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    outcomes: list[RecordOutcome] = Field(default_factory=list)
    dry_run: bool = False


# ── Preview ───────────────────────────────────────────────────────────────

class PreviewRecord(BaseModel):
    action: str             # "create" | "update" | "skip"
    scheme_code: str | None
    name: str | None
    category: str | None
    state: str | None
    validation_errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    mapped_fields: list[str] = Field(default_factory=list)
    ignored_fields: list[str] = Field(default_factory=list)


class PreviewResult(BaseModel):
    resource_id: str
    total_fetched: int
    to_create: int
    to_update: int
    to_skip: int
    records: list[PreviewRecord]


# ── API responses ─────────────────────────────────────────────────────────

class ImportResponse(BaseModel):
    success: bool = True
    message: str = "Import completed."
    report: ImportReport


class PreviewResponse(BaseModel):
    success: bool = True
    message: str = "Preview generated."
    preview: PreviewResult


class ImportStatusResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    is_running: bool
    current_import: ImportReport | None = None


class ImportHistoryResponse(BaseModel):
    success: bool = True
    data: list[ImportReport]
    total: int
