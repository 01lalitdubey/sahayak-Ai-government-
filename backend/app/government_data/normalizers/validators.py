"""
Normalization Validators — Sahayak AI
=======================================
Validates field values before they are persisted.
Returns ValidationError objects rather than raising — callers decide severity.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from app.government_data.normalizers.schemas import ValidationError
from app.government_data.normalizers.transformers import _EMAIL_RE, _URL_SCHEME_RE

_VALID_CATEGORIES = frozenset({
    "agriculture", "education", "health", "housing", "women_and_child",
    "social_welfare", "financial_inclusion", "skill_development",
    "rural_development", "pension", "insurance", "employment",
    "disability", "minority", "farmer", "student", "women",
    "healthcare", "business", "tribal", "transport", "finance", "other",
})

_VALID_STATES = frozenset({
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
})


def validate_required(field: str, value: Any) -> ValidationError | None:
    """Return error if value is None, empty string, or whitespace-only."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return ValidationError(field=field, value=value, reason=f"{field} is required.")
    return None


def validate_url(field: str, value: str | None) -> ValidationError | None:
    """Return error if value is not a valid http/https URL."""
    if not value:
        return None  # Optional field — only validate if present
    if not _URL_SCHEME_RE.match(value):
        return ValidationError(field=field, value=value, reason=f"{field} must be a valid http/https URL.")
    return None


def validate_email(field: str, value: str | None) -> ValidationError | None:
    if not value:
        return None
    if not _EMAIL_RE.match(value):
        return ValidationError(field=field, value=value, reason=f"{field} must be a valid email address.")
    return None


def validate_date_range(
    start_field: str,
    end_field: str,
    start: date | None,
    end: date | None,
) -> ValidationError | None:
    if start and end and start > end:
        return ValidationError(
            field=end_field,
            value=str(end),
            reason=f"{end_field} must be after {start_field}.",
        )
    return None


def validate_category(field: str, value: str | None) -> ValidationError | None:
    if not value:
        return None
    if value not in _VALID_CATEGORIES:
        return ValidationError(
            field=field,
            value=value,
            reason=f"'{value}' is not a recognised category. Valid values: {sorted(_VALID_CATEGORIES)}",
        )
    return None


def validate_state(field: str, value: str | None) -> ValidationError | None:
    if not value:
        return None
    if value not in _VALID_STATES:
        return ValidationError(
            field=field,
            value=value,
            reason=f"'{value}' is not a recognised Indian state or UT.",
        )
    return None


def validate_scheme_type(field: str, value: str | None) -> ValidationError | None:
    if not value:
        return None
    if value not in {"central", "state"}:
        return ValidationError(field=field, value=value, reason="scheme_type must be 'central' or 'state'.")
    return None


def validate_application_mode(field: str, value: str | None) -> ValidationError | None:
    if not value:
        return None
    if value not in {"online", "offline", "both"}:
        return ValidationError(field=field, value=value, reason="application_mode must be 'online', 'offline', or 'both'.")
    return None


def validate_string_length(field: str, value: str | None, max_len: int) -> ValidationError | None:
    if value and len(value) > max_len:
        return ValidationError(
            field=field,
            value=value[:30] + "…",
            reason=f"{field} exceeds maximum length of {max_len} characters.",
        )
    return None


def validate_not_empty_string(field: str, value: Any) -> ValidationError | None:
    """Warn when a field is present but contains only whitespace."""
    if isinstance(value, str) and value.strip() == "":
        return ValidationError(field=field, value=value, reason=f"{field} is an empty string.")
    return None


def run_all_validations(scheme_dict: dict[str, Any]) -> list[ValidationError]:
    """
    Run all applicable validators against a normalized scheme dict.
    Returns a list of ValidationError (empty = all passed).
    """
    errors: list[ValidationError] = []

    def add(e: ValidationError | None) -> None:
        if e:
            errors.append(e)

    add(validate_required("name", scheme_dict.get("name")))
    add(validate_url("official_url", scheme_dict.get("official_url")))
    add(validate_url("official_pdf_url", scheme_dict.get("official_pdf_url")))
    add(validate_email("contact_email", scheme_dict.get("contact_email")))
    add(validate_category("category", scheme_dict.get("category")))
    add(validate_state("state", scheme_dict.get("state")))
    add(validate_scheme_type("scheme_type", scheme_dict.get("scheme_type")))
    add(validate_application_mode("application_mode", scheme_dict.get("application_mode")))
    add(validate_date_range(
        "application_start_date", "application_end_date",
        scheme_dict.get("application_start_date"),
        scheme_dict.get("application_end_date"),
    ))
    add(validate_string_length("name", scheme_dict.get("name"), 500))
    add(validate_string_length("short_description", scheme_dict.get("short_description"), 500))
    add(validate_string_length("scheme_code", scheme_dict.get("scheme_code"), 50))

    return errors
