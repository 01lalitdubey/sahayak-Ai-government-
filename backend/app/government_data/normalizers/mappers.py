"""
Field Mappers — Sahayak AI
============================
Configurable field mapping system that translates external field names
(from government APIs) to internal NormalizedScheme field names.

Design principles:
  - No hardcoded assumptions in business logic
  - Provider-specific maps declared here, reused everywhere
  - Support for aliases (multiple external names → one internal name)
  - Support for nested field access via dot-notation keys
  - Default values for missing fields
"""

from __future__ import annotations

from typing import Any


def safe_get_nested(record: dict[str, Any], key: str) -> Any:
    """
    Traverse a nested dict using dot-notation.
    Example: safe_get_nested(record, "details.ministry.name")
    """
    parts = key.split(".")
    current: Any = record
    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
        if current is None:
            return None
    return current


class FieldMapper:
    """
    Maps external record dict → internal field dict using a configured mapping.

    field_map format:
        {
            "internal_field_name": ["external_alias_1", "external_alias_2", ...],
        }

    The first alias that produces a non-None value wins.
    Supports dot-notation for nested fields.
    """

    def __init__(
        self,
        field_map: dict[str, list[str]],
        defaults: dict[str, Any] | None = None,
    ) -> None:
        self._field_map = field_map
        self._defaults: dict[str, Any] = defaults or {}

    def map(self, record: dict[str, Any]) -> tuple[dict[str, Any], list[str], list[str]]:
        """
        Map a raw record to an internal field dict.

        Returns:
            (mapped_dict, mapped_field_names, ignored_field_names)
        """
        result: dict[str, Any] = {}
        mapped_fields: list[str] = []
        ignored_fields: list[str] = []

        # Track which external keys were consumed
        consumed_keys: set[str] = set()

        for internal_field, aliases in self._field_map.items():
            value = None
            for alias in aliases:
                raw_value = safe_get_nested(record, alias)
                if raw_value is not None and raw_value != "":
                    value = raw_value
                    consumed_keys.add(alias.split(".")[0])  # track top-level key
                    break

            if value is not None:
                result[internal_field] = value
                mapped_fields.append(internal_field)
            elif internal_field in self._defaults:
                result[internal_field] = self._defaults[internal_field]

        # Track external fields that weren't mapped
        for key in record:
            if key not in consumed_keys:
                ignored_fields.append(key)

        return result, mapped_fields, ignored_fields


# ── data.gov.in field map ─────────────────────────────────────────────────
# Lists alias priority: first match wins.

DATA_GOV_FIELD_MAP: dict[str, list[str]] = {
    "name": [
        "scheme_name", "schemeName", "SchemeName",
        "title", "Title", "name", "Name",
        "scheme_title", "SchemeTitle",
    ],
    "short_description": [
        "short_desc", "shortDescription", "summary", "Summary",
        "brief", "Brief", "abstract",
    ],
    "full_description": [
        "description", "Description", "full_description",
        "details", "Details", "scheme_details", "about",
    ],
    "benefits": [
        "benefits", "Benefits", "benefit", "Benefit",
        "financial_assistance", "incentive", "Incentive",
        "scheme_benefits",
    ],
    "ministry": [
        "ministry", "Ministry", "ministry_name", "MinistryName",
        "nodal_ministry", "NodalMinistry",
        "dept", "Dept", "department", "Department",
        "department_name", "DepartmentName",
    ],
    "department": [
        "department", "Department", "department_name", "DepartmentName",
        "division", "Division", "directorate",
    ],
    "state": [
        "state", "State", "state_name", "StateName",
        "state_ut", "StateUT", "applicable_state",
    ],
    "district": [
        "district", "District", "district_name", "DistrictName",
    ],
    "category": [
        "category", "Category", "category_name", "CategoryName",
        "scheme_category", "SchemeCategory",
        "beneficiary_type", "BeneficiaryType", "target_group",
    ],
    "official_url": [
        "official_url", "officialUrl", "website", "Website",
        "scheme_url", "SchemeURL", "url", "URL", "link", "Link",
        "apply_url", "application_url",
    ],
    "official_pdf_url": [
        "pdf_url", "pdfUrl", "guideline_url", "guidelines_url",
        "circular_url", "document_url", "notification_url",
    ],
    "contact_email": [
        "contact_email", "contactEmail", "email", "Email",
        "helpdesk_email", "support_email",
    ],
    "contact_phone": [
        "contact_phone", "contactPhone", "phone", "Phone",
        "helpline", "Helpline", "helpdesk_no", "toll_free",
    ],
    "application_start_date": [
        "start_date", "startDate", "application_start_date",
        "open_date", "launch_date",
    ],
    "application_end_date": [
        "end_date", "endDate", "application_end_date",
        "close_date", "last_date", "deadline",
    ],
    "scheme_type": [
        "scheme_type", "schemeType", "type", "Type",
        "level", "Level", "central_state",
    ],
    "application_mode": [
        "application_mode", "applicationMode", "mode", "Mode",
        "apply_mode", "submission_mode",
    ],
    "scheme_code": [
        "scheme_code", "schemeCode", "code", "Code",
        "scheme_id", "SchemeID", "id",
    ],
}

DATA_GOV_DEFAULTS: dict[str, Any] = {
    "scheme_type": "central",
    "application_mode": "online",
    "is_active": True,
    "is_featured": False,
}

# Singleton mapper for data.gov.in
data_gov_mapper = FieldMapper(DATA_GOV_FIELD_MAP, DATA_GOV_DEFAULTS)
