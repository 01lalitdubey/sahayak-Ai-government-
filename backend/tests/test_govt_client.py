"""
Government API Client Tests — Sahayak AI Phase 6.2
====================================================
All HTTP calls are mocked with pytest-anyio / unittest.mock.
NO real government API calls are made.

Tests:
  - Response models and parser
  - Retry logic
  - Base client request handling
  - DataGovClient methods
  - Query builder
  - Health check
  - Authentication
  - Error scenarios (timeout, 429, 500, 404, invalid JSON)
  - Pagination
  - Graceful shutdown
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import httpx
import pytest

from app.government_data.config import GovtDataSettings


# ─── Fixtures ─────────────────────────────────────────────────────────────

def _settings(**kwargs) -> GovtDataSettings:
    """Build settings with a fake API key by default."""
    defaults = {
        "DATA_GOV_API_KEY": "fakeapikey1234567890abcdef",
        "GOVT_MAX_RETRIES": 2,
        "GOVT_BACKOFF_FACTOR": 0.01,   # tiny backoff for fast tests
        "GOVT_REQUEST_TIMEOUT": 10,
    }
    defaults.update(kwargs)
    return GovtDataSettings(**defaults)


def _mock_response(status_code: int, json_data: dict | None = None, text: str = "") -> MagicMock:
    """Build a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.headers = httpx.Headers({})
    if json_data is not None:
        resp.json = MagicMock(return_value=json_data)
        resp.text = json.dumps(json_data)
    else:
        resp.json = MagicMock(side_effect=Exception("Not JSON"))
        resp.text = text
    return resp


DATA_GOV_SUCCESS = {
    "status": "ok",
    "total": 250,
    "count": 10,
    "limit": 10,
    "offset": 0,
    "records": [{"id": str(i), "name": f"Scheme {i}"} for i in range(10)],
    "field": [{"id": "id", "type": "integer"}, {"id": "name", "type": "string"}],
}


# ─── Response models ──────────────────────────────────────────────────────

def test_govt_pagination_has_more_true():
    from app.government_data.clients.response_models import GovernmentPagination
    p = GovernmentPagination(total=100, count=10, limit=10, offset=0)
    assert p.has_more is True
    assert p.next_offset == 10


def test_govt_pagination_has_more_false():
    from app.government_data.clients.response_models import GovernmentPagination
    p = GovernmentPagination(total=10, count=10, limit=10, offset=0)
    assert p.has_more is False
    assert p.next_offset is None


def test_govt_api_response_record_count():
    from app.government_data.clients.response_models import GovernmentAPIResponse
    resp = GovernmentAPIResponse(
        provider="data_gov",
        status="ok",
        records=[{"a": 1}, {"b": 2}],
    )
    assert resp.record_count == 2


def test_health_check_result():
    from app.government_data.clients.response_models import HealthCheckResult
    r = HealthCheckResult(provider="data_gov", connected=True, latency_ms=42.5)
    assert r.connected is True
    assert r.latency_ms == 42.5
    assert isinstance(r.checked_at, datetime)


def test_parse_data_gov_response_success():
    from app.government_data.clients.response_models import parse_data_gov_response
    result = parse_data_gov_response(DATA_GOV_SUCCESS, resource_id="test-id")
    assert result.provider == "data_gov"
    assert result.record_count == 10
    assert result.pagination is not None
    assert result.pagination.total == 250
    assert result.pagination.has_more is True


def test_parse_data_gov_response_no_pagination():
    from app.government_data.clients.response_models import parse_data_gov_response
    raw = {"status": "ok", "records": [{"a": 1}]}
    result = parse_data_gov_response(raw)
    assert result.record_count == 1


def test_parse_data_gov_response_invalid_type():
    from app.government_data.clients.response_models import parse_data_gov_response
    from app.government_data.exceptions import InvalidResponseException
    with pytest.raises(InvalidResponseException):
        parse_data_gov_response([1, 2, 3])  # type: ignore


def test_parse_data_gov_response_records_not_list():
    from app.government_data.clients.response_models import parse_data_gov_response
    from app.government_data.exceptions import InvalidResponseException
    with pytest.raises(InvalidResponseException):
        parse_data_gov_response({"status": "ok", "records": "not a list"})


# ─── Retry logic ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_retry_succeeds_on_second_attempt():
    from app.government_data.clients.retry import execute_with_retry
    from app.government_data.exceptions import APIUnavailableException

    call_count = 0

    async def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise APIUnavailableException()
        return "success"

    result = await execute_with_retry(flaky, max_retries=2, backoff_base=0.01)
    assert result == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausted_raises():
    from app.government_data.clients.retry import execute_with_retry
    from app.government_data.exceptions import APIUnavailableException

    async def always_fail():
        raise APIUnavailableException("always down")

    with pytest.raises(APIUnavailableException):
        await execute_with_retry(always_fail, max_retries=2, backoff_base=0.01)


@pytest.mark.asyncio
async def test_retry_rate_limit_respects_retry_after():
    from app.government_data.clients.retry import execute_with_retry
    from app.government_data.exceptions import RateLimitException

    call_count = 0

    async def rate_limited_fn():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RateLimitException(retry_after=0)  # 0 seconds for fast test
        return "ok"

    result = await execute_with_retry(rate_limited_fn, max_retries=2, backoff_base=0.01)
    assert result == "ok"


@pytest.mark.asyncio
async def test_retry_network_error():
    from app.government_data.clients.retry import execute_with_retry
    from app.government_data.exceptions import GovernmentAPIException

    async def network_fail():
        raise httpx.NetworkError("connection refused")

    with pytest.raises(GovernmentAPIException):
        await execute_with_retry(network_fail, max_retries=1, backoff_base=0.01)


def test_should_retry_codes():
    from app.government_data.clients.retry import should_retry
    for code in (429, 500, 502, 503, 504):
        assert should_retry(code) is True
    for code in (200, 400, 401, 403, 404):
        assert should_retry(code) is False


def test_parse_retry_after_header():
    from app.government_data.clients.retry import parse_retry_after
    resp = MagicMock()
    resp.headers = httpx.Headers({"retry-after": "60"})
    assert parse_retry_after(resp) == 60


def test_parse_retry_after_missing():
    from app.government_data.clients.retry import parse_retry_after
    resp = MagicMock()
    resp.headers = httpx.Headers({})
    assert parse_retry_after(resp) is None


# ─── DataGovClient query builder ──────────────────────────────────────────

def test_build_query_basic():
    from app.government_data.clients.data_gov_client import DataGovClient
    settings = _settings()
    client = DataGovClient(settings)
    params = client.build_query("res-123", offset=0, limit=10)
    assert params["api-key"] == settings.DATA_GOV_API_KEY
    assert params["offset"] == 0
    assert params["limit"] == 10
    assert params["format"] == "json"


def test_build_query_with_filters():
    from app.government_data.clients.data_gov_client import DataGovClient
    client = DataGovClient(_settings())
    params = client.build_query("res-id", filters={"state": "Maharashtra"})
    assert params["filters[state]"] == "Maharashtra"


def test_build_query_with_sort_and_fields():
    from app.government_data.clients.data_gov_client import DataGovClient
    client = DataGovClient(_settings())
    params = client.build_query("res-id", sort="-created_at", fields=["name", "state"])
    assert params["sort[]"] == "-created_at"
    assert params["fields"] == "name,state"


def test_build_url():
    from app.government_data.clients.data_gov_client import DataGovClient
    client = DataGovClient(_settings())
    url = client.build_url("abc-123")
    assert "abc-123" in url
    assert url.startswith("https://")


def test_build_query_no_api_key_raises():
    from app.government_data.clients.data_gov_client import DataGovClient
    from app.government_data.exceptions import ConfigurationException
    client = DataGovClient(_settings(DATA_GOV_API_KEY=""))
    with pytest.raises(ConfigurationException):
        client.build_query("res-id")


# ─── DataGovClient HTTP methods ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_dataset_success():
    from app.government_data.clients.data_gov_client import DataGovClient

    mock_response = _mock_response(200, DATA_GOV_SUCCESS)

    async with DataGovClient(_settings()) as client:
        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            result = await client.get_dataset("test-resource-id")

    assert result.record_count == 10
    assert result.pagination.total == 250
    assert result.provider == "data_gov"


@pytest.mark.asyncio
async def test_get_dataset_404():
    from app.government_data.clients.data_gov_client import DataGovClient
    from app.government_data.exceptions import GovernmentAPIException

    mock_response = _mock_response(404)

    async with DataGovClient(_settings()) as client:
        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            with pytest.raises(GovernmentAPIException) as exc_info:
                await client.get_dataset("nonexistent")

    assert exc_info.value.error_code == "GOVT_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_dataset_401_raises_auth_error():
    from app.government_data.clients.data_gov_client import DataGovClient
    from app.government_data.exceptions import AuthenticationException

    mock_response = _mock_response(401)

    async with DataGovClient(_settings()) as client:
        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            with pytest.raises(AuthenticationException):
                await client.get_dataset("res-id")


@pytest.mark.asyncio
async def test_get_dataset_500_raises_unavailable():
    from app.government_data.clients.data_gov_client import DataGovClient
    from app.government_data.exceptions import APIUnavailableException

    mock_response = _mock_response(500)

    # With retries=0 so test is fast
    settings = _settings(GOVT_MAX_RETRIES=0)
    async with DataGovClient(settings) as client:
        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            with pytest.raises(APIUnavailableException):
                await client.get_dataset("res-id")


@pytest.mark.asyncio
async def test_get_dataset_invalid_json():
    from app.government_data.clients.data_gov_client import DataGovClient
    from app.government_data.exceptions import InvalidResponseException

    mock_response = _mock_response(200, text="not json at all")

    settings = _settings(GOVT_MAX_RETRIES=0)
    async with DataGovClient(settings) as client:
        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            with pytest.raises(InvalidResponseException):
                await client.get_dataset("res-id")


@pytest.mark.asyncio
async def test_get_dataset_timeout():
    from app.government_data.clients.data_gov_client import DataGovClient
    from app.government_data.exceptions import GovernmentAPIException

    settings = _settings(GOVT_MAX_RETRIES=0)
    async with DataGovClient(settings) as client:
        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = httpx.TimeoutException("timeout")
            with pytest.raises(GovernmentAPIException):
                await client.get_dataset("res-id")


@pytest.mark.asyncio
async def test_get_dataset_rate_limit_retries():
    from app.government_data.clients.data_gov_client import DataGovClient

    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _mock_response(429)
        return _mock_response(200, DATA_GOV_SUCCESS)

    settings = _settings(GOVT_MAX_RETRIES=2, GOVT_BACKOFF_FACTOR=0.01)
    async with DataGovClient(settings) as client:
        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = side_effect
            result = await client.get_dataset("res-id")

    assert result.record_count == 10
    assert call_count == 2


@pytest.mark.asyncio
async def test_get_dataset_pagination():
    from app.government_data.clients.data_gov_client import DataGovClient

    raw = {**DATA_GOV_SUCCESS, "offset": 10, "count": 10, "total": 30}
    mock_response = _mock_response(200, raw)

    async with DataGovClient(_settings()) as client:
        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            result = await client.get_dataset("res-id", offset=10, limit=10)

    assert result.pagination.offset == 10
    assert result.pagination.has_more is True
    assert result.pagination.next_offset == 20


# ─── Health check ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check_success():
    from app.government_data.clients.data_gov_client import DataGovClient

    mock_response = _mock_response(200, {"status": "ok", "records": []})
    mock_response.status_code = 200

    async with DataGovClient(_settings()) as client:
        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await client.health_check()

    assert result.connected is True
    assert result.latency_ms is not None
    assert result.provider == "data_gov"


@pytest.mark.asyncio
async def test_health_check_no_api_key():
    from app.government_data.clients.data_gov_client import DataGovClient

    client = DataGovClient(_settings(DATA_GOV_API_KEY=""))
    result = await client.health_check()
    assert result.connected is False
    assert "Configuration" in result.message


@pytest.mark.asyncio
async def test_health_check_network_error():
    from app.government_data.clients.data_gov_client import DataGovClient

    async with DataGovClient(_settings()) as client:
        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.NetworkError("unreachable")
            result = await client.health_check()

    assert result.connected is False
    assert "NetworkError" in result.message or "Connection" in result.message


# ─── Connection management ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_client_context_manager_opens_and_closes():
    from app.government_data.clients.data_gov_client import DataGovClient

    client = DataGovClient(_settings())
    async with client as c:
        assert c._client is not None
        assert not c._client.is_closed
    # After exit, client should be closed
    assert client._client is None


@pytest.mark.asyncio
async def test_client_close_idempotent():
    from app.government_data.clients.data_gov_client import DataGovClient

    client = DataGovClient(_settings())
    await client.close()   # should not raise even without opening
    await client.close()   # second close also safe


def test_client_provider_name():
    from app.government_data.clients.data_gov_client import DataGovClient
    c = DataGovClient(_settings())
    assert c.PROVIDER_NAME == "data_gov"


def test_get_auth_headers_returns_empty():
    """data.gov.in uses query param auth, not headers."""
    from app.government_data.clients.data_gov_client import DataGovClient
    c = DataGovClient(_settings())
    assert c._get_auth_headers() == {}


# ─── Module imports ───────────────────────────────────────────────────────

def test_clients_package_importable():
    from app.government_data.clients import DataGovClient, BaseGovernmentClient
    assert DataGovClient is not None
    assert BaseGovernmentClient is not None
