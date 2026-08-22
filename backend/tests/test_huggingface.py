"""
HuggingFace Client + Normalizer Tests — Sahayak AI
=====================================================
All HTTP calls mocked. No real HuggingFace API calls made.
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest
from app.government_data.config import GovtDataSettings


def _settings(**kw) -> GovtDataSettings:
    defaults = dict(
        GOVT_MAX_RETRIES=0,
        GOVT_BACKOFF_FACTOR=0.01,
        GOVT_REQUEST_TIMEOUT=10,
        HF_TOKEN="",
        HF_DATASET="smartduketech/indian-government-schemes-2025",
        HF_CONFIG="default",
        HF_SPLIT="train",
    )
    defaults.update(kw)
    return GovtDataSettings(**defaults)


def _mock_resp(status: int, body: dict | None = None) -> MagicMock:
    r = MagicMock(spec=httpx.Response)
    r.status_code = status
    r.headers = httpx.Headers({})
    r.json = MagicMock(return_value=body or {})
    return r


def _hf_rows_response(num_rows=4693, count=100, offset=0):
    rows = [
        {"row_idx": i + offset, "row": {
            "SchemeName": f"Scheme {i+offset}",
            "Ministry": "Ministry of Agriculture",
            "State": "Maharashtra",
            "Category": "Agriculture",
            "Description": "A sample scheme description.",
            "Benefits": "Direct income support",
            "OfficialWebsite": "https://example.gov.in",
        }, "truncated_cells": []}
        for i in range(count)
    ]
    return {"features": [], "rows": rows, "num_rows": num_rows, "offset": offset}


# ─── Response model parser ────────────────────────────────────────────────

def test_parse_hf_response_extracts_row_dicts():
    from app.government_data.clients.response_models import parse_huggingface_rows_response
    raw = _hf_rows_response(num_rows=4693, count=5, offset=0)
    result = parse_huggingface_rows_response(raw, dataset="test/dataset", offset=0, length=100)
    assert result.record_count == 5
    assert result.provider == "huggingface"
    assert result.pagination.total == 4693
    assert result.pagination.has_more is True
    # Each record should be the .row dict, not the wrapper
    assert "SchemeName" in result.records[0]


def test_parse_hf_response_empty_rows():
    from app.government_data.clients.response_models import parse_huggingface_rows_response
    raw = {"features": [], "rows": [], "num_rows": 0, "offset": 0}
    result = parse_huggingface_rows_response(raw, dataset="test", offset=0, length=100)
    assert result.record_count == 0
    assert result.records == []
    assert result.pagination.total == 0
    assert result.pagination.has_more is False


def test_parse_hf_response_invalid_type():
    from app.government_data.clients.response_models import parse_huggingface_rows_response
    from app.government_data.exceptions import InvalidResponseException
    with pytest.raises(InvalidResponseException):
        parse_huggingface_rows_response([1, 2, 3], dataset="test")  # type: ignore


def test_parse_hf_response_rows_not_list():
    from app.government_data.clients.response_models import parse_huggingface_rows_response
    from app.government_data.exceptions import InvalidResponseException
    with pytest.raises(InvalidResponseException):
        parse_huggingface_rows_response({"rows": "bad"}, dataset="test")


def test_parse_hf_pagination_last_page():
    from app.government_data.clients.response_models import parse_huggingface_rows_response
    raw = _hf_rows_response(num_rows=5, count=5, offset=0)
    result = parse_huggingface_rows_response(raw, dataset="test", offset=0, length=100)
    assert result.pagination.has_more is False
    assert result.pagination.next_offset is None


# ─── Query builder ────────────────────────────────────────────────────────

def test_hf_build_query_defaults():
    from app.government_data.clients.huggingface_client import HuggingFaceClient
    c = HuggingFaceClient(_settings())
    q = c.build_query(offset=0)
    assert q["dataset"] == "smartduketech/indian-government-schemes-2025"
    assert q["config"] == "default"
    assert q["split"] == "train"
    assert q["offset"] == 0
    assert q["length"] == 100


def test_hf_build_query_custom_offset():
    from app.government_data.clients.huggingface_client import HuggingFaceClient
    c = HuggingFaceClient(_settings())
    q = c.build_query(offset=200, length=50)
    assert q["offset"] == 200
    assert q["length"] == 50


def test_hf_build_query_caps_length_at_100():
    from app.government_data.clients.huggingface_client import HuggingFaceClient
    c = HuggingFaceClient(_settings())
    q = c.build_query(length=999)
    assert q["length"] == 100


def test_hf_no_auth_headers_without_token():
    from app.government_data.clients.huggingface_client import HuggingFaceClient
    c = HuggingFaceClient(_settings(HF_TOKEN=""))
    assert c._get_auth_headers() == {}


def test_hf_bearer_header_with_token():
    from app.government_data.clients.huggingface_client import HuggingFaceClient
    c = HuggingFaceClient(_settings(HF_TOKEN="hf_abc123"))
    headers = c._get_auth_headers()
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Bearer ")


# ─── get_dataset ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_hf_get_dataset_success():
    from app.government_data.clients.huggingface_client import HuggingFaceClient
    raw = _hf_rows_response(num_rows=4693, count=100, offset=0)
    mock_resp = _mock_resp(200, raw)

    async with HuggingFaceClient(_settings()) as client:
        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_resp
            result = await client.get_dataset(offset=0, length=100)

    assert result.record_count == 100
    assert result.pagination.total == 4693
    assert result.provider == "huggingface"
    assert "SchemeName" in result.records[0]


@pytest.mark.asyncio
async def test_hf_get_dataset_pagination_continues():
    from app.government_data.clients.huggingface_client import HuggingFaceClient
    raw = _hf_rows_response(num_rows=4693, count=100, offset=100)
    mock_resp = _mock_resp(200, raw)

    async with HuggingFaceClient(_settings()) as client:
        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_resp
            result = await client.get_dataset(offset=100, length=100)

    assert result.pagination.offset == 100
    assert result.pagination.has_more is True
    assert result.pagination.next_offset == 200


@pytest.mark.asyncio
async def test_hf_get_dataset_500_raises_unavailable():
    from app.government_data.clients.huggingface_client import HuggingFaceClient
    from app.government_data.exceptions import APIUnavailableException
    mock_resp = _mock_resp(500)

    async with HuggingFaceClient(_settings()) as client:
        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_resp
            with pytest.raises(APIUnavailableException):
                await client.get_dataset()


@pytest.mark.asyncio
async def test_hf_get_dataset_timeout():
    from app.government_data.clients.huggingface_client import HuggingFaceClient
    from app.government_data.exceptions import GovernmentAPIException

    async with HuggingFaceClient(_settings()) as client:
        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = httpx.TimeoutException("timeout")
            with pytest.raises(GovernmentAPIException):
                await client.get_dataset()


@pytest.mark.asyncio
async def test_hf_get_all_rows_stops_at_end():
    from app.government_data.clients.huggingface_client import HuggingFaceClient

    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _mock_resp(200, _hf_rows_response(num_rows=150, count=100, offset=0))
        else:
            return _mock_resp(200, _hf_rows_response(num_rows=150, count=50, offset=100))

    async with HuggingFaceClient(_settings()) as client:
        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = side_effect
            records = await client.get_all_rows()

    assert len(records) == 150
    assert call_count == 2


@pytest.mark.asyncio
async def test_hf_get_all_rows_max_records_cap():
    from app.government_data.clients.huggingface_client import HuggingFaceClient
    raw = _hf_rows_response(num_rows=4693, count=100, offset=0)
    mock_resp = _mock_resp(200, raw)

    async with HuggingFaceClient(_settings()) as client:
        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_resp
            records = await client.get_all_rows(max_records=100)

    assert len(records) == 100


# ─── Health check ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_hf_health_check_success():
    from app.government_data.clients.huggingface_client import HuggingFaceClient
    raw = _hf_rows_response(num_rows=4693, count=1, offset=0)
    mock_resp = _mock_resp(200, raw)

    async with HuggingFaceClient(_settings()) as client:
        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            result = await client.health_check()

    assert result.connected is True
    assert result.provider == "huggingface"
    assert result.latency_ms is not None
    assert "4,693" in result.message or "rows" in result.message


@pytest.mark.asyncio
async def test_hf_health_check_network_error():
    from app.government_data.clients.huggingface_client import HuggingFaceClient

    async with HuggingFaceClient(_settings()) as client:
        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.NetworkError("unreachable")
            result = await client.health_check()

    assert result.connected is False
    assert "NetworkError" in result.message or "Connection" in result.message


# ─── HuggingFace Normalizer ───────────────────────────────────────────────

def _hf_record(**kw):
    base = {
        "name": "PM Kisan Samman Nidhi",       # real field name
        "slug": "pm-kisan",
        "ministry": "Ministry of Agriculture",
        "eligibility_state": '["Maharashtra"]',  # real field — JSON array
        "category": "Agriculture",
        "description": "Direct income support to farmer families.",
        "benefits": "Rs 6000 per year",
        "official_url": "https://pmkisan.gov.in",
        "apply_url": "https://pmkisan.gov.in/apply",
    }
    base.update(kw)
    return base


def test_hf_normalizer_success():
    from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
    n = HuggingFaceNormalizer()
    result = n.normalize(_hf_record())
    assert result.success is True
    assert result.scheme.name == "PM Kisan Samman Nidhi"
    assert result.scheme.category == "agriculture"
    assert result.scheme.state == "Maharashtra"
    assert result.scheme.source_provider == "huggingface"
    assert result.scheme.scheme_code == "PM-KISAN"


def test_hf_normalizer_missing_name_fails():
    from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
    n = HuggingFaceNormalizer()
    result = n.normalize({"ministry": "Agri"})
    assert result.success is False


def test_hf_normalizer_scheme_code_auto_generated():
    from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
    n = HuggingFaceNormalizer()
    rec = _hf_record()
    del rec["slug"]
    result = n.normalize(rec)
    assert result.scheme.scheme_code is not None
    assert len(result.scheme.scheme_code) > 0


def test_hf_normalizer_official_url_mapped():
    from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
    n = HuggingFaceNormalizer()
    result = n.normalize(_hf_record())
    assert result.scheme.official_url == "https://pmkisan.gov.in"


def test_hf_normalizer_eligibility_state_parsed():
    from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
    n = HuggingFaceNormalizer()
    result = n.normalize(_hf_record(eligibility_state='["Maharashtra"]'))
    assert result.scheme.state == "Maharashtra"


def test_hf_normalizer_all_states_maps_to_none():
    from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
    n = HuggingFaceNormalizer()
    result = n.normalize(_hf_record(eligibility_state='["All States"]'))
    assert result.scheme.state is None


def test_hf_normalizer_batch():
    from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
    n = HuggingFaceNormalizer()
    records = [_hf_record(name=f"Scheme {i}", slug=f"scheme-{i}") for i in range(10)]
    batch = n.normalize_batch(records)
    assert batch.stats.total_records == 10
    assert batch.stats.normalized_records == 10
    assert batch.stats.failed_records == 0


def test_hf_normalizer_source_dataset_set():
    from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
    n = HuggingFaceNormalizer(source_dataset="smartduketech/indian-government-schemes-2025")
    result = n.normalize(_hf_record())
    assert result.scheme.source_resource_id == "smartduketech/indian-government-schemes-2025"


def test_hf_normalizer_import_in_package():
    from app.government_data.normalizers import HuggingFaceNormalizer
    assert HuggingFaceNormalizer is not None


def test_hf_client_import_in_package():
    from app.government_data.clients import HuggingFaceClient
    assert HuggingFaceClient is not None


# ─── Config ───────────────────────────────────────────────────────────────

def test_hf_config_defaults():
    s = _settings()
    assert s.HF_DATASET == "smartduketech/indian-government-schemes-2025"
    assert s.HF_CONFIG == "default"
    assert s.HF_SPLIT == "train"
    assert s.HF_TOKEN == ""


def test_hf_config_token_override():
    s = _settings(HF_TOKEN="hf_secret123")
    assert s.HF_TOKEN == "hf_secret123"
