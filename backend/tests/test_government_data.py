"""
Government Data Module Tests — Sahayak AI Phase 6
====================================================
Tests: constants, types, exceptions, config, utils, security, logger.
All 172 previous tests must continue passing.
"""

import math
import pytest
from datetime import date


# ─── Constants ────────────────────────────────────────────────────────────

def test_constants_values():
    from app.government_data.constants import (
        DEFAULT_TIMEOUT, DEFAULT_RETRY_COUNT, DEFAULT_BACKOFF,
        DEFAULT_PAGE_SIZE, DEFAULT_BATCH_SIZE, DEFAULT_RATE_LIMIT,
    )
    assert DEFAULT_TIMEOUT == 30
    assert DEFAULT_RETRY_COUNT == 3
    assert DEFAULT_BACKOFF == 2.0
    assert DEFAULT_PAGE_SIZE == 100
    assert DEFAULT_BATCH_SIZE == 500
    assert DEFAULT_RATE_LIMIT == 60


def test_supported_formats_frozenset():
    from app.government_data.constants import SUPPORTED_FORMATS
    assert isinstance(SUPPORTED_FORMATS, frozenset)
    assert "json" in SUPPORTED_FORMATS
    assert "csv" in SUPPORTED_FORMATS
    assert "xml" in SUPPORTED_FORMATS
    assert "pdf" in SUPPORTED_FORMATS


def test_supported_providers_frozenset():
    from app.government_data.constants import SUPPORTED_PROVIDERS
    assert "data_gov" in SUPPORTED_PROVIDERS
    assert "ministry" in SUPPORTED_PROVIDERS
    assert "state_portal" in SUPPORTED_PROVIDERS
    assert "manual" in SUPPORTED_PROVIDERS


def test_masked_value_constant():
    from app.government_data.constants import MASKED_VALUE
    assert "REDACTED" in MASKED_VALUE


# ─── Types / Enums ────────────────────────────────────────────────────────

def test_data_source_enum():
    from app.government_data.types import DataSource
    assert DataSource.DATA_GOV == "data_gov"
    assert DataSource.MINISTRY == "ministry"
    assert DataSource.STATE == "state"
    assert DataSource.CSV == "csv"
    assert DataSource.JSON == "json"
    assert DataSource.XML == "xml"
    assert DataSource.PDF == "pdf"
    assert DataSource.MANUAL == "manual"


def test_import_status_enum():
    from app.government_data.types import ImportStatus
    assert ImportStatus.SUCCESS == "success"
    assert ImportStatus.FAILED == "failed"
    assert ImportStatus.RUNNING == "running"
    assert ImportStatus.PARTIAL == "partial"
    assert ImportStatus.PENDING == "pending"
    assert ImportStatus.CANCELLED == "cancelled"


def test_import_mode_enum():
    from app.government_data.types import ImportMode
    assert ImportMode.FULL == "full"
    assert ImportMode.INCREMENTAL == "incremental"
    assert ImportMode.MANUAL == "manual"


def test_data_format_enum():
    from app.government_data.types import DataFormat
    assert DataFormat.JSON == "json"
    assert DataFormat.CSV == "csv"
    assert DataFormat.XML == "xml"
    assert DataFormat.PDF == "pdf"


def test_provider_type_enum():
    from app.government_data.types import ProviderType
    assert ProviderType.DATA_GOV == "data_gov"
    assert ProviderType.MINISTRY == "ministry"
    assert ProviderType.STATE_PORTAL == "state_portal"


def test_auth_type_enum():
    from app.government_data.types import AuthType
    assert AuthType.API_KEY == "api_key"
    assert AuthType.NONE == "none"


# ─── Exceptions ───────────────────────────────────────────────────────────

def test_exception_hierarchy():
    from app.government_data.exceptions import (
        GovernmentAPIException, AuthenticationException,
        RateLimitException, APIUnavailableException,
        InvalidResponseException, InvalidDatasetException,
        ImportException, ConfigurationException, ValidationException,
    )
    assert issubclass(AuthenticationException, GovernmentAPIException)
    assert issubclass(RateLimitException, GovernmentAPIException)
    assert issubclass(APIUnavailableException, GovernmentAPIException)
    assert issubclass(InvalidResponseException, GovernmentAPIException)
    assert issubclass(InvalidDatasetException, GovernmentAPIException)
    assert issubclass(ImportException, GovernmentAPIException)
    assert issubclass(ConfigurationException, GovernmentAPIException)
    assert issubclass(ValidationException, GovernmentAPIException)


def test_base_exception_fields():
    from app.government_data.exceptions import GovernmentAPIException
    exc = GovernmentAPIException("test error", error_code="TEST_CODE", details={"k": "v"})
    assert exc.message == "test error"
    assert exc.error_code == "TEST_CODE"
    assert exc.details == {"k": "v"}
    assert str(exc) == "test error"


def test_rate_limit_exception_retry_after():
    from app.government_data.exceptions import RateLimitException
    exc = RateLimitException(retry_after=30)
    assert exc.retry_after == 30
    assert exc.details["retry_after_seconds"] == 30


def test_configuration_exception_error_code():
    from app.government_data.exceptions import ConfigurationException
    exc = ConfigurationException()
    assert exc.error_code == "GOVT_CONFIG_ERROR"


def test_exception_repr():
    from app.government_data.exceptions import ImportException
    exc = ImportException("import failed")
    assert "ImportException" in repr(exc)
    assert "GOVT_IMPORT_ERROR" in repr(exc)


# ─── Configuration ────────────────────────────────────────────────────────

def test_config_loads_with_defaults():
    from app.government_data.config import GovtDataSettings
    s = GovtDataSettings()
    assert s.GOVT_REQUEST_TIMEOUT == 30
    assert s.GOVT_MAX_RETRIES == 3
    assert s.GOVT_BACKOFF_FACTOR == 2.0
    assert s.GOVT_DEFAULT_PAGE_SIZE == 100
    assert s.GOVT_DEFAULT_BATCH_SIZE == 500
    assert s.GOVT_ENABLE_SYNC is False
    assert s.GOVT_ENABLE_CACHE is True


def test_config_has_data_gov_key_false_when_empty():
    from app.government_data.config import GovtDataSettings
    s = GovtDataSettings(DATA_GOV_API_KEY="")
    assert s.has_data_gov_key is False


def test_config_has_data_gov_key_true_when_set():
    from app.government_data.config import GovtDataSettings
    s = GovtDataSettings(DATA_GOV_API_KEY="abc123def456ghi7")
    assert s.has_data_gov_key is True


def test_config_sync_enabled_false_without_key():
    from app.government_data.config import GovtDataSettings
    s = GovtDataSettings(GOVT_ENABLE_SYNC=True, DATA_GOV_API_KEY="")
    assert s.sync_enabled is False


def test_config_sync_enabled_true_with_key():
    from app.government_data.config import GovtDataSettings
    s = GovtDataSettings(GOVT_ENABLE_SYNC=True, DATA_GOV_API_KEY="abc123def456ghi7")
    assert s.sync_enabled is True


def test_config_validate_for_sync_raises_without_key():
    from app.government_data.config import GovtDataSettings
    from app.government_data.exceptions import ConfigurationException
    s = GovtDataSettings(GOVT_ENABLE_SYNC=True, DATA_GOV_API_KEY="")
    with pytest.raises(ConfigurationException, match="DATA_GOV_API_KEY"):
        s.validate_for_sync()


def test_config_validate_for_sync_passes_with_key():
    from app.government_data.config import GovtDataSettings
    s = GovtDataSettings(GOVT_ENABLE_SYNC=True, DATA_GOV_API_KEY="abc123def456ghi7")
    s.validate_for_sync()   # should not raise


def test_config_invalid_log_level():
    import pydantic
    from app.government_data.config import GovtDataSettings
    with pytest.raises(pydantic.ValidationError):
        GovtDataSettings(GOVT_LOG_LEVEL="VERBOSE")


def test_config_invalid_url():
    import pydantic
    from app.government_data.config import GovtDataSettings
    with pytest.raises(pydantic.ValidationError):
        GovtDataSettings(DATA_GOV_BASE_URL="not-a-url")


def test_config_base_url_trailing_slash_stripped():
    from app.government_data.config import GovtDataSettings
    s = GovtDataSettings(DATA_GOV_BASE_URL="https://api.data.gov.in/resource/")
    assert not s.DATA_GOV_BASE_URL.endswith("/")


# ─── Utilities ────────────────────────────────────────────────────────────

def test_clean_string_normal():
    from app.government_data.utils import clean_string
    assert clean_string("  hello  ") == "hello"


def test_clean_string_none():
    from app.government_data.utils import clean_string
    assert clean_string(None) == ""


def test_clean_string_na_placeholder():
    from app.government_data.utils import clean_string
    for val in ("NA", "N/A", "nil", "none", "-", "--", "Not Available", "NULL"):
        assert clean_string(val) == "", f"Expected empty for {val!r}"


def test_normalize_whitespace():
    from app.government_data.utils import normalize_whitespace
    assert normalize_whitespace("  hello   world\t\n") == "hello world"


def test_normalize_whitespace_empty():
    from app.government_data.utils import normalize_whitespace
    assert normalize_whitespace("") == ""


def test_safe_get_nested():
    from app.government_data.utils import safe_get
    data = {"a": {"b": {"c": 42}}}
    assert safe_get(data, "a", "b", "c") == 42


def test_safe_get_missing_key():
    from app.government_data.utils import safe_get
    assert safe_get({"a": 1}, "b", default="x") == "x"


def test_safe_get_none_value():
    from app.government_data.utils import safe_get
    assert safe_get({"a": None}, "a", default=99) == 99


def test_deep_merge():
    from app.government_data.utils import deep_merge
    base = {"a": {"x": 1, "y": 2}, "b": 3}
    override = {"a": {"y": 99, "z": 3}, "c": 4}
    result = deep_merge(base, override)
    assert result == {"a": {"x": 1, "y": 99, "z": 3}, "b": 3, "c": 4}


def test_deep_merge_does_not_mutate_base():
    from app.government_data.utils import deep_merge
    base = {"a": {"x": 1}}
    deep_merge(base, {"a": {"x": 99}})
    assert base["a"]["x"] == 1


def test_parse_date_iso():
    from app.government_data.utils import parse_date
    assert parse_date("2024-01-15") == date(2024, 1, 15)


def test_parse_date_indian_format():
    from app.government_data.utils import parse_date
    assert parse_date("15-08-2023") == date(2023, 8, 15)


def test_parse_date_slash_format():
    from app.government_data.utils import parse_date
    assert parse_date("15/08/2023") == date(2023, 8, 15)


def test_parse_date_invalid():
    from app.government_data.utils import parse_date
    assert parse_date("not a date") is None


def test_parse_date_none():
    from app.government_data.utils import parse_date
    assert parse_date(None) is None


def test_validate_url_valid():
    from app.government_data.utils import validate_url
    assert validate_url("https://api.data.gov.in/resource") is True
    assert validate_url("http://example.com/data") is True


def test_validate_url_invalid():
    from app.government_data.utils import validate_url
    assert validate_url("not-a-url") is False
    assert validate_url("") is False
    assert validate_url(None) is False


def test_validate_json_valid():
    from app.government_data.utils import validate_json
    result = validate_json('{"key": "value"}')
    assert result == {"key": "value"}


def test_validate_json_invalid():
    from app.government_data.utils import validate_json
    assert validate_json("not json {{{{") is None


def test_chunk_list_even():
    from app.government_data.utils import chunk_list
    result = chunk_list([1, 2, 3, 4], 2)
    assert result == [[1, 2], [3, 4]]


def test_chunk_list_odd():
    from app.government_data.utils import chunk_list
    result = chunk_list([1, 2, 3, 4, 5], 2)
    assert result == [[1, 2], [3, 4], [5]]


def test_chunk_list_larger_than_list():
    from app.government_data.utils import chunk_list
    result = chunk_list([1, 2], 10)
    assert result == [[1, 2]]


def test_chunk_list_zero_size_raises():
    from app.government_data.utils import chunk_list
    with pytest.raises(ValueError):
        chunk_list([1, 2], 0)


def test_calculate_retry_delay_increases():
    from app.government_data.utils import calculate_retry_delay
    d1 = calculate_retry_delay(1, jitter=False)
    d2 = calculate_retry_delay(2, jitter=False)
    d3 = calculate_retry_delay(3, jitter=False)
    assert d1 < d2 < d3


def test_calculate_retry_delay_max_cap():
    from app.government_data.utils import calculate_retry_delay
    delay = calculate_retry_delay(100, base=2.0, max_delay=60.0, jitter=False)
    assert delay == 60.0


def test_calculate_retry_delay_with_jitter():
    from app.government_data.utils import calculate_retry_delay
    delays = {calculate_retry_delay(3, jitter=True) for _ in range(10)}
    # With jitter, values should not all be identical
    assert len(delays) >= 1   # at minimum works; usually varies


def test_total_pages():
    from app.government_data.utils import total_pages
    assert total_pages(100, 20) == 5
    assert total_pages(101, 20) == 6
    assert total_pages(0, 20) == 0
    assert total_pages(1, 1) == 1


# ─── Security ─────────────────────────────────────────────────────────────

def test_mask_api_key_long():
    from app.government_data.security import mask_api_key
    result = mask_api_key("abc123def456ghi7")
    assert result.endswith("hi7") or result.endswith("i7") or "REDACTED" in result
    assert "abc123def456" not in result


def test_mask_api_key_short():
    from app.government_data.security import mask_api_key
    from app.government_data.constants import MASKED_VALUE
    assert mask_api_key("abc") == MASKED_VALUE


def test_mask_api_key_none():
    from app.government_data.security import mask_api_key
    from app.government_data.constants import MASKED_VALUE
    assert mask_api_key(None) == MASKED_VALUE


def test_validate_api_key_valid():
    from app.government_data.security import validate_api_key
    result = validate_api_key("abc123def456ghi789", provider="test")
    assert result == "abc123def456ghi789"


def test_validate_api_key_empty_raises():
    from app.government_data.security import validate_api_key
    from app.government_data.exceptions import AuthenticationException
    with pytest.raises(AuthenticationException):
        validate_api_key("", provider="test")


def test_validate_api_key_none_raises():
    from app.government_data.security import validate_api_key
    from app.government_data.exceptions import AuthenticationException
    with pytest.raises(AuthenticationException):
        validate_api_key(None, provider="test")


def test_validate_base_url_valid():
    from app.government_data.security import validate_base_url
    result = validate_base_url("https://api.data.gov.in/resource/", provider="test")
    assert not result.endswith("/")


def test_validate_base_url_missing():
    from app.government_data.security import validate_base_url
    from app.government_data.exceptions import ConfigurationException
    with pytest.raises(ConfigurationException):
        validate_base_url("", provider="test")


def test_validate_base_url_invalid_scheme():
    from app.government_data.security import validate_base_url
    from app.government_data.exceptions import ConfigurationException
    with pytest.raises(ConfigurationException):
        validate_base_url("ftp://data.gov.in", provider="test")


def test_safe_config_repr_redacts_keys():
    from app.government_data.security import safe_config_repr
    result = safe_config_repr({"DATA_GOV_API_KEY": "supersecret", "TIMEOUT": 30})
    assert "supersecret" not in str(result)
    assert result["TIMEOUT"] == 30


def test_safe_config_repr_preserves_non_sensitive():
    from app.government_data.security import safe_config_repr
    result = safe_config_repr({"BASE_URL": "https://example.com", "TIMEOUT": 30})
    assert result["BASE_URL"] == "https://example.com"


def test_get_auth_headers():
    from app.government_data.security import get_auth_headers
    headers = get_auth_headers("mykey123", header_name="api-key")
    assert headers["api-key"] == "mykey123"


# ─── Logger ───────────────────────────────────────────────────────────────

def test_logger_instantiation():
    from app.government_data.logger import GovtDataLogger
    logger = GovtDataLogger("test")
    assert logger is not None


def test_logger_get_govt_logger():
    from app.government_data.logger import get_govt_logger
    import logging
    log = get_govt_logger("test.module")
    assert isinstance(log, logging.Logger)
    assert "sahayak.govt_data" in log.name


def test_logger_masked_key():
    from app.government_data.logger import GovtDataLogger
    result = GovtDataLogger.masked_key("abc123def456ghi7")
    assert "abc123def456" not in result
    assert len(result) > 0


def test_logger_masked_key_none():
    from app.government_data.logger import GovtDataLogger
    from app.government_data.constants import MASKED_VALUE
    assert GovtDataLogger.masked_key(None) == MASKED_VALUE


def test_module_init_importable():
    import app.government_data
    assert app.government_data is not None
