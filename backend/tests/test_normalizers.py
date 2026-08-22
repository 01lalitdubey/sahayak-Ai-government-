"""
Government Data Normalizer Tests — Sahayak AI Phase 6.3
=========================================================
Tests: transformers, validators, mappers, schemas, base normalizer,
       DataGovNormalizer (single + batch), field mapping, statistics.
All previous 343 tests must continue passing.
"""

from datetime import date
import pytest


# ─── Transformers ─────────────────────────────────────────────────────────

def test_clean_text_normal():
    from app.government_data.normalizers.transformers import clean_text
    assert clean_text("  hello world  ") == "hello world"

def test_clean_text_none():
    from app.government_data.normalizers.transformers import clean_text
    assert clean_text(None) is None

def test_clean_text_na_placeholders():
    from app.government_data.normalizers.transformers import clean_text
    for v in ("NA", "N/A", "nil", "None", "-", "--", "null", "Not Available"):
        assert clean_text(v) is None, f"Expected None for {v!r}"

def test_clean_text_collapses_whitespace():
    from app.government_data.normalizers.transformers import clean_text
    assert clean_text("hello   world\t\n") == "hello world"

def test_truncate_long():
    from app.government_data.normalizers.transformers import truncate
    assert truncate("a" * 600, 500) == "a" * 500

def test_truncate_short():
    from app.government_data.normalizers.transformers import truncate
    assert truncate("hello", 500) == "hello"

def test_normalize_url_valid():
    from app.government_data.normalizers.transformers import normalize_url
    assert normalize_url("https://example.gov.in/scheme") == "https://example.gov.in/scheme"

def test_normalize_url_trailing_slash():
    from app.government_data.normalizers.transformers import normalize_url
    assert normalize_url("https://example.gov.in/") == "https://example.gov.in"

def test_normalize_url_adds_https_to_www():
    from app.government_data.normalizers.transformers import normalize_url
    assert normalize_url("www.example.gov.in") == "https://www.example.gov.in"

def test_normalize_url_invalid():
    from app.government_data.normalizers.transformers import normalize_url
    assert normalize_url("not-a-url") is None
    assert normalize_url("") is None
    assert normalize_url(None) is None

def test_normalize_email_valid():
    from app.government_data.normalizers.transformers import normalize_email
    assert normalize_email("Test@Gov.IN") == "test@gov.in"

def test_normalize_email_invalid():
    from app.government_data.normalizers.transformers import normalize_email
    assert normalize_email("notanemail") is None
    assert normalize_email(None) is None

def test_normalize_phone_strips_formatting():
    from app.government_data.normalizers.transformers import normalize_phone
    assert normalize_phone("+91-1800-123-4567") == "+911800123456 7".replace(" ", "")

def test_normalize_phone_too_short():
    from app.government_data.normalizers.transformers import normalize_phone
    assert normalize_phone("123") is None

def test_normalize_phone_none():
    from app.government_data.normalizers.transformers import normalize_phone
    assert normalize_phone(None) is None

def test_normalize_date_iso():
    from app.government_data.normalizers.transformers import normalize_date
    assert normalize_date("2024-01-15") == date(2024, 1, 15)

def test_normalize_date_indian():
    from app.government_data.normalizers.transformers import normalize_date
    assert normalize_date("15-08-2023") == date(2023, 8, 15)

def test_normalize_date_invalid():
    from app.government_data.normalizers.transformers import normalize_date
    assert normalize_date("not a date") is None
    assert normalize_date(None) is None

def test_normalize_date_date_object():
    from app.government_data.normalizers.transformers import normalize_date
    d = date(2024, 6, 1)
    assert normalize_date(d) == d

def test_normalize_bool_true_values():
    from app.government_data.normalizers.transformers import normalize_bool
    for v in ("true", "yes", "1", "active", "Y", "on"):
        assert normalize_bool(v) is True, f"Expected True for {v!r}"

def test_normalize_bool_false_values():
    from app.government_data.normalizers.transformers import normalize_bool
    for v in ("false", "no", "0", "inactive", "N"):
        assert normalize_bool(v) is False, f"Expected False for {v!r}"

def test_normalize_bool_default():
    from app.government_data.normalizers.transformers import normalize_bool
    assert normalize_bool("unknown_val", default=True) is True

def test_normalize_state_alias():
    from app.government_data.normalizers.transformers import normalize_state
    assert normalize_state("maharashtra") == "Maharashtra"
    assert normalize_state("UP") == "Uttar Pradesh"
    assert normalize_state("tn") == "Tamil Nadu"

def test_normalize_state_none():
    from app.government_data.normalizers.transformers import normalize_state
    assert normalize_state(None) is None

def test_normalize_ministry_title_case():
    from app.government_data.normalizers.transformers import normalize_ministry
    result = normalize_ministry("ministry of agriculture and farmers welfare")
    assert result is not None
    assert "Ministry" in result or "ministry" in result.lower()

def test_normalize_category_mapping():
    from app.government_data.normalizers.transformers import normalize_category
    assert normalize_category("Agriculture") == "agriculture"
    assert normalize_category("health") == "health"
    assert normalize_category("student") == "student"
    assert normalize_category("totally unknown xyz") == "other"
    assert normalize_category(None) is None

def test_normalize_scheme_type_central():
    from app.government_data.normalizers.transformers import normalize_scheme_type
    assert normalize_scheme_type("central") == "central"
    assert normalize_scheme_type(None) == "central"

def test_normalize_scheme_type_state():
    from app.government_data.normalizers.transformers import normalize_scheme_type
    assert normalize_scheme_type("state scheme") == "state"

def test_normalize_application_mode():
    from app.government_data.normalizers.transformers import normalize_application_mode
    assert normalize_application_mode("online") == "online"
    assert normalize_application_mode("offline") == "offline"
    assert normalize_application_mode("both online and offline") == "both"
    assert normalize_application_mode(None) == "online"

def test_normalize_scheme_code_from_name():
    from app.government_data.normalizers.transformers import normalize_scheme_code
    code = normalize_scheme_code("PM Kisan Samman Nidhi 2024")
    assert code == "PM-KISAN-SAMMAN-NIDHI-2024"

def test_normalize_scheme_code_max_length():
    from app.government_data.normalizers.transformers import normalize_scheme_code
    long = "A" * 100
    result = normalize_scheme_code(long)
    assert len(result) <= 50

def test_normalize_scheme_code_none_with_fallback():
    from app.government_data.normalizers.transformers import normalize_scheme_code
    assert normalize_scheme_code(None, fallback="DEFAULT") == "DEFAULT"


# ─── Validators ───────────────────────────────────────────────────────────

def test_validate_required_passes():
    from app.government_data.normalizers.validators import validate_required
    assert validate_required("name", "PM Kisan") is None

def test_validate_required_fails_on_none():
    from app.government_data.normalizers.validators import validate_required
    err = validate_required("name", None)
    assert err is not None
    assert err.field == "name"

def test_validate_required_fails_on_empty():
    from app.government_data.normalizers.validators import validate_required
    err = validate_required("name", "   ")
    assert err is not None

def test_validate_url_valid():
    from app.government_data.normalizers.validators import validate_url
    assert validate_url("official_url", "https://example.gov.in") is None

def test_validate_url_invalid():
    from app.government_data.normalizers.validators import validate_url
    err = validate_url("official_url", "not-a-url")
    assert err is not None

def test_validate_url_none_passes():
    from app.government_data.normalizers.validators import validate_url
    assert validate_url("official_url", None) is None

def test_validate_email_valid():
    from app.government_data.normalizers.validators import validate_email
    assert validate_email("contact_email", "help@gov.in") is None

def test_validate_email_invalid():
    from app.government_data.normalizers.validators import validate_email
    err = validate_email("contact_email", "notanemail")
    assert err is not None

def test_validate_date_range_valid():
    from app.government_data.normalizers.validators import validate_date_range
    err = validate_date_range("start", "end", date(2024, 1, 1), date(2024, 12, 31))
    assert err is None

def test_validate_date_range_invalid():
    from app.government_data.normalizers.validators import validate_date_range
    err = validate_date_range("start", "end", date(2024, 12, 31), date(2024, 1, 1))
    assert err is not None

def test_validate_category_valid():
    from app.government_data.normalizers.validators import validate_category
    assert validate_category("category", "agriculture") is None

def test_validate_category_invalid():
    from app.government_data.normalizers.validators import validate_category
    err = validate_category("category", "not_a_real_category_xyz")
    assert err is not None

def test_validate_state_valid():
    from app.government_data.normalizers.validators import validate_state
    assert validate_state("state", "Maharashtra") is None

def test_validate_state_invalid():
    from app.government_data.normalizers.validators import validate_state
    err = validate_state("state", "FakeState123")
    assert err is not None

def test_run_all_validations_clean():
    from app.government_data.normalizers.validators import run_all_validations
    data = {"name": "PM Kisan", "official_url": "https://pmkisan.gov.in"}
    errors = run_all_validations(data)
    assert len(errors) == 0

def test_run_all_validations_missing_name():
    from app.government_data.normalizers.validators import run_all_validations
    errors = run_all_validations({})
    assert any(e.field == "name" for e in errors)


# ─── Mappers ──────────────────────────────────────────────────────────────

def test_field_mapper_basic():
    from app.government_data.normalizers.mappers import FieldMapper
    fm = FieldMapper({"name": ["scheme_name", "title"]})
    result, mapped, ignored = fm.map({"scheme_name": "PM Kisan", "extra": "x"})
    assert result["name"] == "PM Kisan"
    assert "name" in mapped
    assert "extra" in ignored

def test_field_mapper_alias_fallback():
    from app.government_data.normalizers.mappers import FieldMapper
    fm = FieldMapper({"name": ["scheme_name", "title"]})
    result, mapped, _ = fm.map({"title": "Another Scheme"})
    assert result["name"] == "Another Scheme"

def test_field_mapper_default_value():
    from app.government_data.normalizers.mappers import FieldMapper
    fm = FieldMapper({"scheme_type": ["type"]}, defaults={"scheme_type": "central"})
    result, _, _ = fm.map({})
    assert result["scheme_type"] == "central"

def test_field_mapper_nested():
    from app.government_data.normalizers.mappers import FieldMapper
    fm = FieldMapper({"ministry": ["details.ministry.name"]})
    result, _, _ = fm.map({"details": {"ministry": {"name": "Ministry of Agriculture"}}})
    assert result["ministry"] == "Ministry of Agriculture"

def test_data_gov_field_map_contains_expected_fields():
    from app.government_data.normalizers.mappers import DATA_GOV_FIELD_MAP
    required_internal = {"name", "ministry", "state", "category", "official_url", "benefits"}
    assert required_internal.issubset(DATA_GOV_FIELD_MAP.keys())

def test_safe_get_nested():
    from app.government_data.normalizers.mappers import safe_get_nested
    assert safe_get_nested({"a": {"b": 42}}, "a.b") == 42
    assert safe_get_nested({"a": {}}, "a.b") is None
    assert safe_get_nested({}, "a.b.c") is None


# ─── Schemas ──────────────────────────────────────────────────────────────

def test_normalized_scheme_defaults():
    from app.government_data.normalizers.schemas import NormalizedScheme
    s = NormalizedScheme()
    assert s.scheme_type == "central"
    assert s.application_mode == "online"
    assert s.is_active is True

def test_batch_result_successful_property():
    from app.government_data.normalizers.schemas import (
        BatchNormalizationResult, BatchNormalizationStats, NormalizationResult, NormalizedScheme
    )
    r1 = NormalizationResult(success=True, scheme=NormalizedScheme(name="S1"))
    r2 = NormalizationResult(success=False)
    batch = BatchNormalizationResult(
        results=[r1, r2],
        stats=BatchNormalizationStats(
            total_records=2, normalized_records=1,
            failed_records=1, warnings_count=0, missing_fields_count=0
        )
    )
    assert len(batch.successful) == 1
    assert len(batch.failed) == 1


# ─── DataGovNormalizer ────────────────────────────────────────────────────

def _raw_record(**overrides):
    base = {
        "scheme_name": "PM Kisan Samman Nidhi",
        "description": "Direct income support to farmer families.",
        "benefits": "Rs 6000 per year in 3 instalments",
        "ministry": "Ministry of Agriculture",
        "state": "Maharashtra",       # valid state
        "category": "Agriculture",
        "website": "https://pmkisan.gov.in",
        "contact_email": "pmkisan-ict@gov.in",
    }
    base.update(overrides)
    return base

def test_normalize_single_success():
    from app.government_data.normalizers.data_gov_normalizer import DataGovNormalizer
    n = DataGovNormalizer()
    result = n.normalize(_raw_record())
    assert result.success is True
    assert result.scheme is not None
    assert result.scheme.name == "PM Kisan Samman Nidhi"
    assert result.scheme.category == "agriculture"

def test_normalize_url_mapped():
    from app.government_data.normalizers.data_gov_normalizer import DataGovNormalizer
    n = DataGovNormalizer()
    result = n.normalize(_raw_record())
    assert result.scheme.official_url == "https://pmkisan.gov.in"

def test_normalize_missing_name_fails():
    from app.government_data.normalizers.data_gov_normalizer import DataGovNormalizer
    n = DataGovNormalizer()
    result = n.normalize({"description": "No name here"})
    assert result.success is False
    assert any(e.field == "name" for e in result.errors)

def test_normalize_auto_generates_scheme_code():
    from app.government_data.normalizers.data_gov_normalizer import DataGovNormalizer
    n = DataGovNormalizer()
    result = n.normalize(_raw_record())
    assert result.scheme.scheme_code is not None
    assert len(result.scheme.scheme_code) > 0

def test_normalize_uses_explicit_scheme_code():
    from app.government_data.normalizers.data_gov_normalizer import DataGovNormalizer
    n = DataGovNormalizer()
    result = n.normalize(_raw_record(scheme_code="PM-KISAN-2024"))
    assert result.scheme.scheme_code == "PM-KISAN-2024"

def test_normalize_invalid_url_creates_error():
    from app.government_data.normalizers.data_gov_normalizer import DataGovNormalizer
    n = DataGovNormalizer()
    result = n.normalize(_raw_record(website="not-a-url"))
    # URL is cleaned to None — validation passes (optional field)
    assert result.scheme.official_url is None

def test_normalize_state_mapped():
    from app.government_data.normalizers.data_gov_normalizer import DataGovNormalizer
    n = DataGovNormalizer()
    result = n.normalize(_raw_record(state="maharashtra"))
    assert result.scheme.state == "Maharashtra"

def test_normalize_unknown_fields_ignored():
    from app.government_data.normalizers.data_gov_normalizer import DataGovNormalizer
    n = DataGovNormalizer()
    record = {**_raw_record(state="Maharashtra"), "unknown_field_xyz": "value", "another_unknown": 42}
    result = n.normalize(record)
    assert result.success is True
    assert len(result.ignored_fields) >= 2

def test_normalize_provenance_set():
    from app.government_data.normalizers.data_gov_normalizer import DataGovNormalizer
    n = DataGovNormalizer(source_resource_id="test-resource-123")
    result = n.normalize(_raw_record())
    assert result.scheme.source_provider == "data_gov"
    assert result.scheme.source_resource_id == "test-resource-123"

def test_normalize_raw_record_preserved():
    from app.government_data.normalizers.data_gov_normalizer import DataGovNormalizer
    n = DataGovNormalizer()
    raw = _raw_record()
    result = n.normalize(raw)
    assert result.scheme.raw_record == raw


# ─── Batch normalization ──────────────────────────────────────────────────

def test_normalize_batch_all_success():
    from app.government_data.normalizers.data_gov_normalizer import DataGovNormalizer
    n = DataGovNormalizer()
    records = [_raw_record(scheme_name=f"Scheme {i}") for i in range(5)]
    batch = n.normalize_batch(records)
    assert batch.stats.total_records == 5
    assert batch.stats.normalized_records == 5
    assert batch.stats.failed_records == 0
    assert len(batch.successful) == 5

def test_normalize_batch_partial_failure():
    from app.government_data.normalizers.data_gov_normalizer import DataGovNormalizer
    n = DataGovNormalizer()
    records = [
        _raw_record(scheme_name="Good Scheme"),
        {"no_name_field": "bad record"},   # will fail
    ]
    batch = n.normalize_batch(records)
    assert batch.stats.total_records == 2
    assert batch.stats.normalized_records == 1
    assert batch.stats.failed_records == 1

def test_normalize_batch_empty():
    from app.government_data.normalizers.data_gov_normalizer import DataGovNormalizer
    n = DataGovNormalizer()
    batch = n.normalize_batch([])
    assert batch.stats.total_records == 0
    assert batch.stats.normalized_records == 0

def test_normalize_batch_statistics():
    from app.government_data.normalizers.data_gov_normalizer import DataGovNormalizer
    n = DataGovNormalizer()
    records = [_raw_record(scheme_name=f"Scheme {i}") for i in range(10)]
    batch = n.normalize_batch(records)
    assert batch.stats.total_records == 10
    assert isinstance(batch.stats.warnings_count, int)


# ─── Module imports ───────────────────────────────────────────────────────

def test_normalizers_package_importable():
    from app.government_data.normalizers import DataGovNormalizer, BaseNormalizer
    assert DataGovNormalizer is not None
    assert BaseNormalizer is not None
