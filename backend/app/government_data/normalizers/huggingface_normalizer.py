"""
HuggingFace Dataset Normalizer — Sahayak AI
=============================================
Normalizes records from smartduketech/indian-government-schemes-2025.

Real dataset field names (verified from API):
  slug, name, description, ministry, department, state, category,
  beneficiary_type, benefits, eligibility_text, application_process,
  documents_required, apply_url, official_url,
  eligibility_age_min, eligibility_age_max, eligibility_gender,
  eligibility_caste, eligibility_income_max, eligibility_residence,
  eligibility_state, eligibility_disability, eligibility_bpl, scraped_at
"""

from __future__ import annotations

import json
from typing import Any

from app.government_data.normalizers.base_normalizer import BaseNormalizer
from app.government_data.normalizers.mappers import FieldMapper
from app.government_data.normalizers.schemas import (
    NormalizationResult,
    NormalizedScheme,
    ValidationError,
)
from app.government_data.normalizers.transformers import (
    clean_text,
    normalize_application_mode,
    normalize_bool,
    normalize_category,
    normalize_date,
    normalize_email,
    normalize_ministry,
    normalize_phone,
    normalize_scheme_code,
    normalize_scheme_type,
    normalize_state,
    normalize_url,
    truncate,
)
from app.government_data.normalizers.validators import run_all_validations

# ── Field map matched against real dataset fields ─────────────────────────
_HF_FIELD_MAP: dict[str, list[str]] = {
    # Identification
    "name":                ["name", "SchemeName", "Title", "title"],
    "scheme_code":         ["slug", "SchemeCode", "scheme_code", "Code"],

    # Content
    "full_description":    ["description", "Description", "full_description"],
    "benefits":            ["benefits", "Benefits"],
    "short_description":   ["short_description", "ShortDescription", "Summary"],

    # Classification
    "ministry":            ["ministry", "Ministry", "MinistryName"],
    "department":          ["department", "Department"],
    "category":            ["category", "Category", "beneficiary_type"],

    # Geography — eligibility_state is a JSON array e.g. '["Puducherry"]'
    "state":               ["eligibility_state", "state", "State"],

    # Links
    "official_url":        ["official_url", "OfficialWebsite", "Website"],
    "official_pdf_url":    ["apply_url", "PDFUrl", "DocumentURL"],

    # Contact
    "contact_email":       ["ContactEmail", "Email", "contact_email"],
    "contact_phone":       ["ContactPhone", "Phone", "Helpline"],

    # Dates
    "application_start_date": ["LaunchDate", "StartDate", "start_date"],
    "application_end_date":   ["EndDate", "DeadlineDate", "end_date"],

    # Application mode — detect from application_process text
    "application_mode":    ["application_process", "ApplicationMode", "Mode"],
    "scheme_type":         ["SchemeType", "scheme_type", "Level"],
}

_HF_DEFAULTS: dict[str, Any] = {
    "scheme_type": "central",
    "application_mode": "online",
    "is_active": True,
    "is_featured": False,
}

_hf_mapper = FieldMapper(_HF_FIELD_MAP, _HF_DEFAULTS)


def _parse_eligibility_state(raw_value: Any) -> str | None:
    """
    eligibility_state in this dataset is a JSON array string like:
      '["Puducherry"]'  or  '["All States"]'  or  '["State1","State2"]'

    Returns the first valid state, or None for pan-India / unknown.
    """
    if not raw_value:
        return None

    s = str(raw_value).strip()

    # Try JSON parse
    try:
        parsed = json.loads(s)
        if isinstance(parsed, list) and parsed:
            first = str(parsed[0]).strip()
            # "All States" → pan-India → None
            if first.lower() in {"all states", "all", "pan india", "national", ""}:
                return None
            return normalize_state(first)
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: treat as plain string
    return normalize_state(s)


class HuggingFaceNormalizer(BaseNormalizer):
    """
    Normalizes raw records from the HuggingFace
    smartduketech/indian-government-schemes-2025 dataset.
    """

    PROVIDER_NAME = "huggingface"

    def __init__(self, source_dataset: str | None = None) -> None:
        super().__init__()
        self._dataset = (
            source_dataset or "smartduketech/indian-government-schemes-2025"
        )

    def normalize(self, record: dict[str, Any]) -> NormalizationResult:
        warnings: list[str] = []
        try:
            mapped_dict, mapped_fields, ignored_fields = _hf_mapper.map(record)

            if ignored_fields:
                warnings.append(
                    f"Ignored {len(ignored_fields)} unmapped fields: "
                    f"{ignored_fields[:5]}"
                )

            transformed = self._apply_transformers(mapped_dict, record, warnings)
            validation_errors = run_all_validations(transformed)

            scheme = NormalizedScheme(
                scheme_code=transformed.get("scheme_code"),
                name=transformed.get("name"),
                short_description=transformed.get("short_description"),
                full_description=transformed.get("full_description"),
                benefits=transformed.get("benefits"),
                scheme_type=transformed.get("scheme_type", "central"),
                category=transformed.get("category"),
                ministry=transformed.get("ministry"),
                department=transformed.get("department"),
                state=transformed.get("state"),
                district=None,
                application_mode=transformed.get("application_mode", "online"),
                application_start_date=transformed.get("application_start_date"),
                application_end_date=transformed.get("application_end_date"),
                official_url=transformed.get("official_url"),
                official_pdf_url=transformed.get("official_pdf_url"),
                contact_email=transformed.get("contact_email"),
                contact_phone=transformed.get("contact_phone"),
                is_active=transformed.get("is_active", True),
                is_featured=transformed.get("is_featured", False),
                source_provider=self.PROVIDER_NAME,
                source_resource_id=self._dataset,
                raw_record=record,
            )

            success = len(validation_errors) == 0
            if not success:
                self._logger.warning(
                    "Validation failed — name=%r errors=%d",
                    scheme.name, len(validation_errors),
                )

            return NormalizationResult(
                success=success,
                scheme=scheme,
                errors=validation_errors,
                warnings=warnings,
                ignored_fields=ignored_fields,
                mapped_fields=mapped_fields,
            )

        except Exception as exc:
            self._logger.error("HF normalization error: %s", exc)
            return NormalizationResult(
                success=False,
                errors=[ValidationError(
                    field="__record__", value=None,
                    reason=f"{type(exc).__name__}: {exc}",
                )],
                warnings=warnings,
            )

    def _apply_transformers(
        self,
        mapped: dict[str, Any],
        original: dict[str, Any],
        warnings: list[str],
    ) -> dict[str, Any]:
        out: dict[str, Any] = {}

        # Name
        name = clean_text(mapped.get("name"))
        out["name"] = truncate(name, 500)

        # Use slug as scheme_code (already a clean short ID)
        raw_code = mapped.get("scheme_code") or original.get("slug")
        out["scheme_code"] = normalize_scheme_code(raw_code, fallback=None)
        if not out["scheme_code"] and name:
            out["scheme_code"] = normalize_scheme_code(name)
            warnings.append("scheme_code auto-generated from name.")

        out["short_description"] = truncate(
            clean_text(mapped.get("short_description")), 500
        )
        out["full_description"] = clean_text(mapped.get("full_description"))
        out["benefits"] = clean_text(mapped.get("benefits"))
        out["department"] = clean_text(mapped.get("department"))

        out["ministry"] = normalize_ministry(mapped.get("ministry"))

        # State: eligibility_state is JSON array in original record
        raw_state = original.get("eligibility_state") or mapped.get("state")
        out["state"] = _parse_eligibility_state(raw_state)

        out["category"] = normalize_category(mapped.get("category"))
        out["scheme_type"] = normalize_scheme_type(mapped.get("scheme_type"))

        # Application mode: detect from application_process text
        out["application_mode"] = normalize_application_mode(
            mapped.get("application_mode")
        )

        out["official_url"] = normalize_url(mapped.get("official_url"))
        out["official_pdf_url"] = normalize_url(
            original.get("apply_url") or mapped.get("official_pdf_url")
        )
        out["contact_email"] = normalize_email(mapped.get("contact_email"))
        out["contact_phone"] = normalize_phone(mapped.get("contact_phone"))

        out["application_start_date"] = normalize_date(
            mapped.get("application_start_date")
        )
        out["application_end_date"] = normalize_date(
            mapped.get("application_end_date")
        )

        out["is_active"] = True
        out["is_featured"] = False

        return out
