"""
API Loader & Normalizer Module — Sahayak AI
============================================
Fetches scheme records from external government / portal APIs (e.g., data.gov.in,
myScheme, state welfare portals) and normalizes them into clean, validated
SchemeRecord and SchemeEligibilityRules Pydantic v2 objects.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Union

import httpx

from schemas import (
    SchemeEligibilityRules,
    SchemeRecord,
)

logger = logging.getLogger("api_loader")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ============================================================================
# 1. Custom Exceptions
# ============================================================================

class APILoaderError(Exception):
    """Base exception for API Loader failures."""
    pass


class APINetworkError(APILoaderError):
    """Raised when network connection fails or HTTP status is 4xx/5xx."""
    pass


class APITimeoutError(APILoaderError):
    """Raised when the external API request times out."""
    pass


class APIMalformedPayloadError(APILoaderError):
    """Raised when the external API returns invalid JSON or unexpected schema."""
    pass


# ============================================================================
# 2. Key Mapping & Normalization Utilities
# ============================================================================

WILDCARD_VALUES = {"all", "any", "*", "n/a", "na", "none", "null", "", "both"}

# Aliases for top-level scheme fields
SCHEME_FIELD_ALIASES: dict[str, list[str]] = {
    "scheme_code": ["scheme_code", "code", "schemeId", "scheme_id", "id", "identifier", "sr_no"],
    "name": ["name", "scheme_name", "schemeName", "title", "schemeTitle", "project_name"],
    "short_description": ["short_description", "description", "desc", "summary", "brief", "about"],
    "full_description": ["full_description", "details", "overview", "long_description", "background"],
    "benefits": ["benefits", "scheme_benefits", "financial_assistance", "benefit_description", "subsidy"],
    "category": ["category", "sector", "domain", "scheme_category", "department_category"],
    "ministry": ["ministry", "ministry_name", "nodal_ministry", "central_ministry"],
    "state": ["state", "applicable_state", "target_state", "state_name"],
    "scheme_type": ["scheme_type", "type", "scheme_level", "funding_pattern"],
    "official_url": ["official_url", "url", "portal_url", "website", "link", "apply_url"],
    "required_documents": ["required_documents", "documents", "documents_required", "doc_list", "docs"],
    "is_active": ["is_active", "status", "active", "is_open", "application_open"],
}

# Aliases for eligibility rules fields
RULE_FIELD_ALIASES: dict[str, list[str]] = {
    "min_age": ["min_age", "minAge", "minimum_age", "age_min", "from_age", "lower_age_limit"],
    "max_age": ["max_age", "maxAge", "maximum_age", "age_max", "to_age", "upper_age_limit"],
    "max_annual_income": [
        "max_annual_income", "maxIncome", "max_income", "annual_income_limit",
        "income_ceiling", "family_income_limit", "income_limit", "max_income_inr"
    ],
    "occupation": ["occupation", "occupations", "professions", "target_occupation", "eligible_occupations", "livelihood"],
    "farmer_status": ["farmer_status", "farmer_type", "farmer_category", "landholding_category", "farmer_size"],
    "social_category": ["social_category", "caste", "category", "social_group", "community", "caste_category"],
    "gender": ["gender", "target_gender", "applicable_gender", "sex", "beneficiary_gender"],
    "state": ["state", "states", "target_state", "applicable_states", "eligible_states"],
    "education": ["education", "qualification", "min_education", "education_level", "educational_qualification"],
    "marital_status": ["marital_status", "maritalStatus", "target_marital_status"],
    "disability_required": [
        "disability_required", "handicapped", "pwd_only", "disability_only",
        "is_disabled", "physically_challenged", "for_differently_abled"
    ],
    "min_disability_percentage": ["min_disability_percentage", "min_disability_percent", "pwd_percentage", "disability_min_percentage"],
}


def _extract_first_matching(d: dict[str, Any], aliases: list[str]) -> Any:
    """Finds the first key in dictionary matching any alias (case-insensitive)."""
    lower_map = {k.lower(): v for k, v in d.items()}
    for alias in aliases:
        if alias.lower() in lower_map:
            val = lower_map[alias.lower()]
            if val is not None:
                return val
    return None


def _clean_string(val: Any) -> Optional[str]:
    """Cleans string, stripping whitespace and returning None for empty or wildcard tokens."""
    if val is None:
        return None
    s = str(val).strip()
    if s.lower() in WILDCARD_VALUES:
        return None
    return s


def _clean_numeric(val: Any, target_type: type = float) -> Optional[Union[int, float]]:
    """Parses numeric values, handling commas, currency strings, or None."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return target_type(val)
    if isinstance(val, str):
        # Remove currency symbols, commas, and trailing units
        cleaned = re.sub(r"[^\d.-]", "", val)
        if not cleaned:
            return None
        try:
            return target_type(float(cleaned))
        except (ValueError, TypeError):
            return None
    return None


def _clean_list_or_str(val: Any) -> Optional[Union[List[str], str]]:
    """
    Normalizes a scalar string or list into a clean list or string.
    Converts comma-separated or pipe-separated strings into lists.
    Wildcard values are converted to 'any' or None.
    """
    if val is None:
        return None

    if isinstance(val, (list, tuple, set)):
        cleaned_list: list[str] = []
        for item in val:
            if item is None:
                continue
            s = str(item).strip().lower()
            if s in WILDCARD_VALUES:
                return "any"
            if s:
                cleaned_list.append(s)
        return cleaned_list if cleaned_list else None

    if isinstance(val, str):
        s = val.strip().lower()
        if s in WILDCARD_VALUES:
            return "any"
        # Check if delimited (comma, semicolon, slash, or pipe)
        if any(delim in s for delim in [",", ";", "|", "/"]):
            tokens = [t.strip().lower() for t in re.split(r"[,;|/]", s) if t.strip()]
            if any(t in WILDCARD_VALUES for t in tokens):
                return "any"
            return tokens if tokens else None
        return s

    return str(val).strip().lower()


def _clean_bool(val: Any) -> Optional[bool]:
    """Parses boolean values from various formats (e.g. 'yes', 'true', '1', 'pwd', etc.)."""
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        s = val.strip().lower()
        if s in ("true", "yes", "y", "1", "required", "only"):
            return True
        if s in ("false", "no", "n", "0", "not_required", "none"):
            return False
        if s in WILDCARD_VALUES:
            return None
    return None


def normalize_raw_scheme_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Transforms a raw external API scheme dictionary into a clean dictionary
    compatible with SchemeRecord.model_validate().
    """
    if not isinstance(raw, dict):
        raise ValueError(f"Expected dictionary payload, got {type(raw).__name__}")

    # 1. Extract nested eligibility dictionary if present
    nested_rules_dict = (
        raw.get("eligibility_rules")
        or raw.get("eligibility")
        or raw.get("rules")
        or raw.get("criteria")
        or {}
    )
    if not isinstance(nested_rules_dict, dict):
        nested_rules_dict = {}

    # Combined lookup source: top-level raw dictionary merged with nested rules
    combined_source: dict[str, Any] = {**raw, **nested_rules_dict}

    # 2. Build normalized eligibility rules dictionary
    norm_rules: dict[str, Any] = {}

    min_age_val = _extract_first_matching(combined_source, RULE_FIELD_ALIASES["min_age"])
    norm_rules["min_age"] = _clean_numeric(min_age_val, int)

    max_age_val = _extract_first_matching(combined_source, RULE_FIELD_ALIASES["max_age"])
    norm_rules["max_age"] = _clean_numeric(max_age_val, int)

    max_income_val = _extract_first_matching(combined_source, RULE_FIELD_ALIASES["max_annual_income"])
    norm_rules["max_annual_income"] = _clean_numeric(max_income_val, float)

    occ_val = _extract_first_matching(combined_source, RULE_FIELD_ALIASES["occupation"])
    norm_rules["occupation"] = _clean_list_or_str(occ_val)

    farmer_val = _extract_first_matching(combined_source, RULE_FIELD_ALIASES["farmer_status"])
    norm_rules["farmer_status"] = _clean_list_or_str(farmer_val)

    social_val = _extract_first_matching(combined_source, RULE_FIELD_ALIASES["social_category"])
    norm_rules["social_category"] = _clean_list_or_str(social_val)

    gender_val = _extract_first_matching(combined_source, RULE_FIELD_ALIASES["gender"])
    norm_rules["gender"] = _clean_list_or_str(gender_val)

    state_rule_val = _extract_first_matching(combined_source, RULE_FIELD_ALIASES["state"])
    norm_rules["state"] = _clean_list_or_str(state_rule_val)

    edu_val = _extract_first_matching(combined_source, RULE_FIELD_ALIASES["education"])
    norm_rules["education"] = _clean_list_or_str(edu_val)

    marital_val = _extract_first_matching(combined_source, RULE_FIELD_ALIASES["marital_status"])
    norm_rules["marital_status"] = _clean_list_or_str(marital_val)

    disability_val = _extract_first_matching(combined_source, RULE_FIELD_ALIASES["disability_required"])
    norm_rules["disability_required"] = _clean_bool(disability_val)

    disability_pct_val = _extract_first_matching(combined_source, RULE_FIELD_ALIASES["min_disability_percentage"])
    norm_rules["min_disability_percentage"] = _clean_numeric(disability_pct_val, float)

    # 3. Build top-level scheme record dictionary
    norm_scheme: dict[str, Any] = {}

    scheme_code_val = _extract_first_matching(raw, SCHEME_FIELD_ALIASES["scheme_code"])
    norm_scheme["scheme_code"] = _clean_string(scheme_code_val) or "UNKNOWN-SCHEME"

    name_val = _extract_first_matching(raw, SCHEME_FIELD_ALIASES["name"])
    norm_scheme["name"] = _clean_string(name_val) or norm_scheme["scheme_code"]

    norm_scheme["short_description"] = _clean_string(
        _extract_first_matching(raw, SCHEME_FIELD_ALIASES["short_description"])
    )
    norm_scheme["full_description"] = _clean_string(
        _extract_first_matching(raw, SCHEME_FIELD_ALIASES["full_description"])
    )
    norm_scheme["benefits"] = _clean_string(
        _extract_first_matching(raw, SCHEME_FIELD_ALIASES["benefits"])
    )
    norm_scheme["category"] = _clean_string(
        _extract_first_matching(raw, SCHEME_FIELD_ALIASES["category"])
    )
    norm_scheme["ministry"] = _clean_string(
        _extract_first_matching(raw, SCHEME_FIELD_ALIASES["ministry"])
    )
    norm_scheme["state"] = _clean_string(
        _extract_first_matching(raw, SCHEME_FIELD_ALIASES["state"])
    )
    norm_scheme["scheme_type"] = _clean_string(
        _extract_first_matching(raw, SCHEME_FIELD_ALIASES["scheme_type"])
    ) or ("state" if norm_scheme["state"] else "central")

    norm_scheme["official_url"] = _clean_string(
        _extract_first_matching(raw, SCHEME_FIELD_ALIASES["official_url"])
    )
    doc_val = _extract_first_matching(raw, SCHEME_FIELD_ALIASES["required_documents"])
    norm_scheme["required_documents"] = _clean_list_or_str(doc_val)

    active_val = _extract_first_matching(raw, SCHEME_FIELD_ALIASES["is_active"])
    norm_scheme["is_active"] = _clean_bool(active_val) if active_val is not None else True

    norm_scheme["eligibility_rules"] = norm_rules

    return norm_scheme


def _extract_records_from_response(json_data: Any) -> list[dict[str, Any]]:
    """Extracts raw record list from various standard API response wrapper schemas."""
    if isinstance(json_data, list):
        return [item for item in json_data if isinstance(item, dict)]

    if isinstance(json_data, dict):
        # Check common pagination or data wrapper keys
        for key in ["records", "data", "schemes", "results", "items", "rows", "payload"]:
            val = json_data.get(key)
            if isinstance(val, list):
                return [item for item in val if isinstance(item, dict)]

        # If data is a nested dict with records
        if isinstance(json_data.get("data"), dict):
            nested_data = json_data["data"]
            for key in ["records", "schemes", "results", "items"]:
                val = nested_data.get(key)
                if isinstance(val, list):
                    return [item for item in val if isinstance(item, dict)]

        # Single record payload
        if "scheme_code" in json_data or "name" in json_data or "scheme_name" in json_data:
            return [json_data]

    raise APIMalformedPayloadError("Response payload does not contain an array of scheme records.")


# ============================================================================
# 3. Public Fetch & Normalize Functions
# ============================================================================

def fetch_and_normalize_schemes(
    api_url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 15.0,
    skip_invalid: bool = True,
) -> List[SchemeRecord]:
    """
    Fetches scheme records from an external API endpoint synchronously and normalizes them
    into a clean list of validated `SchemeRecord` instances.

    Args:
        api_url: Target external API URL.
        headers: Optional HTTP headers (Authorization, Accept, etc.).
        timeout: Request timeout in seconds (default 15.0s).
        skip_invalid: If True, logs a warning and skips invalid records instead of raising.

    Returns:
        List of validated `SchemeRecord` objects.

    Raises:
        APITimeoutError: When network call exceeds timeout limit.
        APINetworkError: When HTTP status is 4xx/5xx or connection fails.
        APIMalformedPayloadError: When response is not valid JSON or lacks records.
    """
    default_headers = {
        "Accept": "application/json",
        "User-Agent": "SahayakAI-SchemeIngestion/1.0",
    }
    if headers:
        default_headers.update(headers)

    logger.info(f"Fetching scheme records from external API: {api_url}")

    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(api_url, headers=default_headers)
            response.raise_for_status()

    except httpx.TimeoutException as exc:
        msg = f"Timeout ({timeout}s) while connecting to external scheme API at {api_url}: {exc}"
        logger.error(msg)
        raise APITimeoutError(msg) from exc

    except httpx.HTTPStatusError as exc:
        msg = f"HTTP error {exc.response.status_code} received from {api_url}: {exc.response.text[:200]}"
        logger.error(msg)
        raise APINetworkError(msg) from exc

    except httpx.RequestError as exc:
        msg = f"Network connection error while reaching {api_url}: {exc}"
        logger.error(msg)
        raise APINetworkError(msg) from exc

    # Parse JSON payload
    try:
        payload_data = response.json()
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        msg = f"Malformed JSON received from {api_url}: {exc}"
        logger.error(msg)
        raise APIMalformedPayloadError(msg) from exc

    raw_records = _extract_records_from_response(payload_data)
    logger.info(f"Extracted {len(raw_records)} raw records from response. Starting normalization...")

    validated_schemes: List[SchemeRecord] = []
    for idx, raw in enumerate(raw_records):
        try:
            normalized_dict = normalize_raw_scheme_payload(raw)
            record = SchemeRecord.model_validate(normalized_dict)
            validated_schemes.append(record)
        except Exception as exc:
            msg = f"Validation failed for record #{idx} ({raw.get('scheme_code') or raw.get('name') or 'unknown'}): {exc}"
            if skip_invalid:
                logger.warning(msg)
            else:
                logger.error(msg)
                raise APILoaderError(msg) from exc

    logger.info(f"Successfully normalized and validated {len(validated_schemes)}/{len(raw_records)} schemes.")
    return validated_schemes


async def async_fetch_and_normalize_schemes(
    api_url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 15.0,
    skip_invalid: bool = True,
) -> List[SchemeRecord]:
    """
    Asynchronous version of fetch_and_normalize_schemes for FastAPI or async pipelines.
    """
    default_headers = {
        "Accept": "application/json",
        "User-Agent": "SahayakAI-SchemeIngestion/1.0",
    }
    if headers:
        default_headers.update(headers)

    logger.info(f"Async fetching scheme records from: {api_url}")

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(api_url, headers=default_headers)
            response.raise_for_status()

    except httpx.TimeoutException as exc:
        msg = f"Async timeout ({timeout}s) for API at {api_url}: {exc}"
        logger.error(msg)
        raise APITimeoutError(msg) from exc

    except httpx.HTTPStatusError as exc:
        msg = f"Async HTTP {exc.response.status_code} error from {api_url}: {exc.response.text[:200]}"
        logger.error(msg)
        raise APINetworkError(msg) from exc

    except httpx.RequestError as exc:
        msg = f"Async request error while reaching {api_url}: {exc}"
        logger.error(msg)
        raise APINetworkError(msg) from exc

    try:
        payload_data = response.json()
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        msg = f"Malformed JSON from {api_url}: {exc}"
        logger.error(msg)
        raise APIMalformedPayloadError(msg) from exc

    raw_records = _extract_records_from_response(payload_data)
    validated_schemes: List[SchemeRecord] = []

    for idx, raw in enumerate(raw_records):
        try:
            normalized_dict = normalize_raw_scheme_payload(raw)
            record = SchemeRecord.model_validate(normalized_dict)
            validated_schemes.append(record)
        except Exception as exc:
            msg = f"Async validation error at #{idx}: {exc}"
            if skip_invalid:
                logger.warning(msg)
            else:
                logger.error(msg)
                raise APILoaderError(msg) from exc

    return validated_schemes


# ============================================================================
# Self-test block
# ============================================================================
if __name__ == "__main__":
    print("--- Running api_loader.py Self-Tests ---")

    # Sample heterogenous external API payload with non-standard field names & wildcards
    sample_api_response = {
        "status": "success",
        "total_records": 2,
        "records": [
            {
                "schemeId": "PM-KISAN-2024",
                "schemeTitle": "Pradhan Mantri Kisan Samman Nidhi",
                "desc": "Income support of Rs. 6,000 per year to all landholding farmer families.",
                "department_category": "Agriculture",
                "state_name": "all",
                "scheme_level": "Central",
                "apply_url": "https://pmkisan.gov.in",
                "documents_required": "Aadhaar Card, Land Ownership Papers, Bank Account Details",
                # Non-standard flat eligibility fields with wildcards & formatted numbers
                "minAge": "18",
                "maxAge": "100",
                "annual_income_limit": "2,00,000",
                "professions": "farmer, agricultural_labourer",
                "farmer_category": "small_farmer, marginal_farmer",
                "caste_category": "ALL",
                "sex": "any",
                "pwd_only": "false",
            },
            {
                "id": "MHA-ASHA-2024",
                "project_name": "Maharashtra Balika Samriddhi Yojana",
                "about": "Financial aid and scholarship for girl child education in rural areas.",
                "sector": "Women & Child Development",
                "state": "Maharashtra",
                "eligibility": {
                    "from_age": 6,
                    "to_age": 18,
                    "income_ceiling": "100000",
                    "target_gender": "female",
                    "caste": ["sc", "st", "obc"],
                    "professions": "student",
                    "handicapped": "any",
                }
            }
        ]
    }

    # Test normalization logic directly
    raw_list = sample_api_response["records"]
    for idx, raw in enumerate(raw_list):
        norm = normalize_raw_scheme_payload(raw)
        scheme_obj = SchemeRecord.model_validate(norm)
        print(f"\n[PASS] Parsed Scheme #{idx+1}: {scheme_obj.scheme_code} - {scheme_obj.name}")
        print(f"       Category: {scheme_obj.category}, State: {scheme_obj.state}")
        print(f"       Rules: Min Age={scheme_obj.eligibility_rules.min_age}, Max Age={scheme_obj.eligibility_rules.max_age}")
        print(f"              Income Ceiling={scheme_obj.eligibility_rules.max_annual_income}")
        print(f"              Occupations={scheme_obj.eligibility_rules.occupation}")
        print(f"              Farmer Status={scheme_obj.eligibility_rules.farmer_status}")
        print(f"              Disability Required={scheme_obj.eligibility_rules.disability_required}")

        assert scheme_obj.scheme_code in ("PM-KISAN-2024", "MHA-ASHA-2024")
        assert scheme_obj.eligibility_rules.min_age in (18, 6)

    print("\n[PASS] All field mapping, wildcard handling, and normalization tests passed successfully!")
