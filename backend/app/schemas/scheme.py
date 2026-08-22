"""
Scheme Schemas — Sahayak AI (Phase 4)
=======================================
Pydantic v2 contracts for the full Scheme management API.
Original SchemeRead / SchemeResponse kept for backward compatibility.
"""

import re
import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from app.models.enums import SchemeCategoryEnum, SchemeTypeEnum, ApplicationModeEnum

_URL_RE = re.compile(
    r"^https?://"
    r"(?:[a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,}"
    r"(?:/[^\s]*)?$"
)
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_PHONE_RE = re.compile(r"^\+?[0-9\s\-]{7,20}$")


def _validate_url(v: str | None, field_name: str) -> str | None:
    if v is not None and not _URL_RE.match(v):
        raise ValueError(f"{field_name} must be a valid http/https URL.")
    return v


# ── Create ────────────────────────────────────────────────────────────────

class SchemeCreate(BaseModel):
    scheme_code: str = Field(
        min_length=3, max_length=50,
        description="Unique short code, e.g. PM-KISAN-2024",
    )
    name: str = Field(min_length=3, max_length=500)
    short_description: str | None = Field(default=None, max_length=500)
    full_description: str | None = None
    benefits: str | None = None
    required_documents: str | None = None
    application_process: str | None = None
    scheme_type: SchemeTypeEnum = SchemeTypeEnum.CENTRAL
    category: SchemeCategoryEnum | None = None
    ministry: str | None = Field(default=None, max_length=300)
    department: str | None = Field(default=None, max_length=300)
    state: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    application_mode: ApplicationModeEnum = ApplicationModeEnum.ONLINE
    application_start_date: date | None = None
    application_end_date: date | None = None
    official_url: str | None = Field(default=None, max_length=2000)
    official_pdf_url: str | None = Field(default=None, max_length=2000)
    contact_email: str | None = Field(default=None, max_length=255)
    contact_phone: str | None = Field(default=None, max_length=20)
    is_active: bool = True
    is_featured: bool = False

    @field_validator("scheme_code")
    @classmethod
    def normalise_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("official_url", "official_pdf_url")
    @classmethod
    def validate_urls(cls, v: str | None) -> str | None:
        return _validate_url(v, "URL")

    @field_validator("contact_email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is not None and not _EMAIL_RE.match(v):
            raise ValueError("contact_email must be a valid email address.")
        return v

    @field_validator("contact_phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None and not _PHONE_RE.match(v):
            raise ValueError("contact_phone must be a valid phone number.")
        return v

    @model_validator(mode="after")
    def check_dates(self) -> "SchemeCreate":
        if (
            self.application_start_date
            and self.application_end_date
            and self.application_start_date > self.application_end_date
        ):
            raise ValueError(
                "application_start_date must be before application_end_date."
            )
        return self


# ── Update ────────────────────────────────────────────────────────────────

class SchemeUpdate(BaseModel):
    """Partial update — all fields optional."""
    name: str | None = Field(default=None, min_length=3, max_length=500)
    short_description: str | None = Field(default=None, max_length=500)
    full_description: str | None = None
    benefits: str | None = None
    required_documents: str | None = None
    application_process: str | None = None
    scheme_type: SchemeTypeEnum | None = None
    category: SchemeCategoryEnum | None = None
    ministry: str | None = Field(default=None, max_length=300)
    department: str | None = Field(default=None, max_length=300)
    state: str | None = None
    district: str | None = None
    application_mode: ApplicationModeEnum | None = None
    application_start_date: date | None = None
    application_end_date: date | None = None
    official_url: str | None = None
    official_pdf_url: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    is_featured: bool | None = None


# ── Status-only update (PATCH /status) ───────────────────────────────────

class SchemeStatusUpdate(BaseModel):
    is_active: bool


# ── Read ──────────────────────────────────────────────────────────────────

class SchemeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scheme_code: str
    name: str
    short_description: str | None
    full_description: str | None
    benefits: str | None
    required_documents: str | None
    application_process: str | None
    scheme_type: SchemeTypeEnum
    category: SchemeCategoryEnum | None
    ministry: str | None
    department: str | None
    state: str | None
    district: str | None
    application_mode: ApplicationModeEnum
    application_start_date: date | None
    application_end_date: date | None
    official_url: str | None
    official_pdf_url: str | None
    contact_email: str | None
    contact_phone: str | None
    is_active: bool
    is_featured: bool
    view_count: int
    created_by: uuid.UUID | None
    updated_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


# ── Summary (list view — lighter payload) ─────────────────────────────────

class SchemeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scheme_code: str
    name: str
    short_description: str | None
    scheme_type: SchemeTypeEnum
    category: SchemeCategoryEnum | None
    ministry: str | None
    state: str | None
    application_mode: ApplicationModeEnum
    application_end_date: date | None
    is_active: bool
    is_featured: bool
    view_count: int
    created_at: datetime
    updated_at: datetime


# ── List / paginated response ─────────────────────────────────────────────

class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int


class SchemeListResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: list[SchemeSummary]
    meta: PaginationMeta


# ── Search / filter request ───────────────────────────────────────────────

class SortField(str):
    pass


VALID_SORT_FIELDS = {
    "newest": "created_at_desc",
    "oldest": "created_at_asc",
    "alphabetical": "name_asc",
    "most_viewed": "view_count_desc",
    "recently_updated": "updated_at_desc",
}


class SchemeSearchRequest(BaseModel):
    query: str | None = Field(default=None, max_length=200)
    category: SchemeCategoryEnum | None = None
    scheme_type: SchemeTypeEnum | None = None
    application_mode: ApplicationModeEnum | None = None
    state: str | None = None
    ministry: str | None = None
    is_featured: bool | None = None
    is_active: bool | None = True
    date_from: date | None = None
    date_to: date | None = None
    sort: str = "newest"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, v: str) -> str:
        if v not in VALID_SORT_FIELDS:
            raise ValueError(
                f"sort must be one of: {', '.join(VALID_SORT_FIELDS.keys())}"
            )
        return v


# ── Single-item response ──────────────────────────────────────────────────

class SchemeResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: SchemeRead | None = None


# ── Translation status (per scheme, per language) ─────────────────────────

LANGUAGE_DISPLAY_NAMES: dict[str, str] = {
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
}

TARGET_LANGUAGES = list(LANGUAGE_DISPLAY_NAMES.keys())


class TranslationStatusItem(BaseModel):
    language_code: str
    language_name: str
    status: str          # published | outdated | processing | missing
    is_published: bool
    version: int | None = None
    updated_at: datetime | None = None
    review_status: str | None = None


class TranslationStatusResponse(BaseModel):
    scheme_id: uuid.UUID
    scheme_code: str
    source_language: str = "English"
    translations: list[TranslationStatusItem]


# ── Audit history ─────────────────────────────────────────────────────────

class AuditHistoryItem(BaseModel):
    id: uuid.UUID
    action: str
    admin_email: str | None = None
    admin_name: str | None = None
    result: str | None = None
    details: dict[str, Any] | None = None
    timestamp: datetime


class AuditHistoryResponse(BaseModel):
    scheme_id: uuid.UUID
    scheme_code: str
    events: list[AuditHistoryItem]
    total: int


# ── Admin search filters ───────────────────────────────────────────────────

class AdminSchemeFilters(BaseModel):
    """Extended filters for admin scheme listing — includes inactive/draft/archived."""
    query: str | None = Field(default=None, max_length=200)
    category: SchemeCategoryEnum | None = None
    scheme_type: SchemeTypeEnum | None = None
    application_mode: ApplicationModeEnum | None = None
    state: str | None = None
    ministry: str | None = None
    is_featured: bool | None = None
    is_active: bool | None = None       # None = show all (draft + published + archived)
    sort: str = "newest"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
