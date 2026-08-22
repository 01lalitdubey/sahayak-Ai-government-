"""
data.gov.in Normalizer — Sahayak AI
======================================
Converts raw records from DataGovClient.get_dataset() into NormalizedScheme objects.

Pipeline for each record:
  1. Map external field names → internal names (via FieldMapper)
  2. Apply type transformers to each value
  3. Run validators on transformed values
  4. Build NormalizedScheme
  5. Return NormalizationResult (never raises)
"""

from __future__ import annotations

from typing import Any

from app.government_data.normalizers.base_normalizer import BaseNormalizer
from app.government_data.normalizers.mappers import data_gov_mapper
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


class DataGovNormalizer(BaseNormalizer):
    """
    Normalizes raw records from the data.gov.in API.

    Handles:
      - Multiple external field name aliases
      - Missing / null / placeholder values
      - Unicode normalisation
      - Date parsing in Indian formats
      - State and category name normalisation
    """

    PROVIDER_NAME = "data_gov"

    def __init__(self, source_resource_id: str | None = None) -> None:
        super().__init__()
        self._resource_id = source_resource_id

    def normalize(self, record: dict[str, Any]) -> NormalizationResult:
        """
        Normalize one raw data.gov.in API record.

        Args:
            record: Raw dict from GovernmentAPIResponse.records

        Returns:
            NormalizationResult — always, never raises.
        """
        warnings: list[str] = []

        try:
            # Step 1: Map external fields → internal names
            mapped_dict, mapped_fields, ignored_fields = data_gov_mapper.map(record)

            if ignored_fields:
                warnings.append(
                    f"Ignored {len(ignored_fields)} unmapped fields: {ignored_fields[:5]}"
                )

            # Step 2: Apply transformers to each mapped value
            transformed = self._apply_transformers(mapped_dict, warnings)

            # Step 3: Validate transformed values
            validation_errors = run_all_validations(transformed)

            # Step 4: Build NormalizedScheme even with validation errors
            #          (callers decide whether to accept partial records)
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
                district=clean_text(transformed.get("district")),
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
                source_resource_id=self._resource_id,
                raw_record=record,
            )

            # Success = no validation errors (warnings are non-blocking)
            success = len(validation_errors) == 0

            if not success:
                self._logger.warning(
                    "Record failed validation — name=%r errors=%d",
                    scheme.name, len(validation_errors),
                )
            else:
                self._logger.debug(
                    "Record normalized — name=%r fields=%d",
                    scheme.name, len(mapped_fields),
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
            self._logger.error("Normalization error: %s", exc, exc_info=True)
            return NormalizationResult(
                success=False,
                errors=[ValidationError(
                    field="__record__",
                    value=None,
                    reason=f"Unexpected error: {type(exc).__name__}: {exc}",
                )],
                warnings=warnings,
            )

    def _apply_transformers(
        self, mapped: dict[str, Any], warnings: list[str]
    ) -> dict[str, Any]:
        """Apply type-specific transformers to each mapped field."""
        out: dict[str, Any] = {}

        # Text fields
        name = clean_text(mapped.get("name"))
        out["name"] = truncate(name, 500)

        out["short_description"] = truncate(clean_text(mapped.get("short_description")), 500)
        out["full_description"] = clean_text(mapped.get("full_description"))
        out["benefits"] = clean_text(mapped.get("benefits"))
        out["department"] = clean_text(mapped.get("department"))
        out["district"] = clean_text(mapped.get("district"))

        # Specialised transformers
        raw_code = mapped.get("scheme_code")
        out["scheme_code"] = normalize_scheme_code(raw_code, fallback=None)
        if not out["scheme_code"] and name:
            out["scheme_code"] = normalize_scheme_code(name)
            warnings.append("scheme_code was auto-generated from name.")

        out["ministry"] = normalize_ministry(mapped.get("ministry"))
        out["state"] = normalize_state(mapped.get("state"))
        out["category"] = normalize_category(mapped.get("category"))
        out["scheme_type"] = normalize_scheme_type(mapped.get("scheme_type"))
        out["application_mode"] = normalize_application_mode(mapped.get("application_mode"))

        out["official_url"] = normalize_url(mapped.get("official_url"))
        out["official_pdf_url"] = normalize_url(mapped.get("official_pdf_url"))
        out["contact_email"] = normalize_email(mapped.get("contact_email"))
        out["contact_phone"] = normalize_phone(mapped.get("contact_phone"))

        out["application_start_date"] = normalize_date(mapped.get("application_start_date"))
        out["application_end_date"] = normalize_date(mapped.get("application_end_date"))

        out["is_active"] = normalize_bool(mapped.get("is_active"), default=True)
        out["is_featured"] = normalize_bool(mapped.get("is_featured"), default=False)

        return out
