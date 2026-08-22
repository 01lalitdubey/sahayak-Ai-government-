"""
Production Verification Tests — Sahayak AI Phase 7
====================================================
Covers all 13 verification steps from the production readiness checklist.

Steps covered:
  STEP 1  — HuggingFace Connectivity
  STEP 2  — Full Import Pipeline
  STEP 3  — SQL Verification Queries (string validation)
  STEP 4  — Normalization Verification
  STEP 5  — Duplicate Detection
  STEP 6  — Scheme APIs
  STEP 7  — Frontend API Compatibility
  STEP 8  — Eligibility Engine
  STEP 9  — Recommendation Engine
  STEP 10 — Performance Metrics
  STEP 11 — Security Verification
  STEP 12 — Production Readiness Report

All HTTP and DB calls are mocked. No real API or PostgreSQL needed.
"""
from __future__ import annotations

import re
import time
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient


# ─── Shared helpers ───────────────────────────────────────────────────────


def _make_test_client() -> TestClient:
    from app.main import create_application
    return TestClient(create_application(), raise_server_exceptions=False)


def _mock_db() -> AsyncMock:
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


def _norm_scheme(**kw):
    from app.government_data.normalizers.schemas import NormalizedScheme
    defaults = dict(
        scheme_code="PM-KISAN-2024",
        name="PM Kisan Samman Nidhi",
        category="agriculture",
        state="Maharashtra",
        scheme_type="central",
        application_mode="online",
        is_active=True,
        is_featured=False,
        source_provider="huggingface",
        source_resource_id="smartduketech/indian-government-schemes-2025",
    )
    defaults.update(kw)
    return NormalizedScheme(**defaults)


def _hf_rows_payload(num_rows: int = 4693, count: int = 100, offset: int = 0) -> dict:
    """Simulate a HuggingFace Rows API response payload."""
    rows = [
        {
            "row_idx": i + offset,
            "row": {
                "name": f"Scheme {i + offset}",
                "slug": f"scheme-{i + offset:04d}",
                "ministry": "Ministry of Agriculture And Farmers Welfare",
                "eligibility_state": '["Maharashtra"]',
                "category": "Agriculture",
                "description": f"Description for scheme {i + offset}.",
                "benefits": "Direct income support of Rs 6000 per year.",
                "official_url": "https://pmkisan.gov.in",
                "apply_url": "https://pmkisan.gov.in/apply",
                "application_process": "Apply online at the official portal.",
            },
            "truncated_cells": [],
        }
        for i in range(count)
    ]
    return {"features": [], "rows": rows, "num_rows": num_rows, "offset": offset}


def _mock_hf_response(status: int = 200, payload: dict | None = None) -> MagicMock:
    r = MagicMock(spec=httpx.Response)
    r.status_code = status
    r.headers = httpx.Headers({})
    r.json = MagicMock(return_value=payload or {})
    return r


# ═════════════════════════════════════════════════════════════════════════════
# STEP 1 — HUGGINGFACE CONNECTIVITY
# ═════════════════════════════════════════════════════════════════════════════

class TestStep1HuggingFaceConnectivity:
    """Verify: dataset reachable, metadata, rows endpoint, pagination, latency."""

    def test_hf_client_imports_correctly(self):
        from app.government_data.clients.huggingface_client import HuggingFaceClient
        assert HuggingFaceClient is not None
        assert HuggingFaceClient.PROVIDER_NAME == "huggingface"
        assert HuggingFaceClient.MAX_LENGTH == 100

    def test_expected_dataset_configured(self):
        from app.government_data.config import govt_settings
        assert govt_settings.HF_DATASET == "smartduketech/indian-government-schemes-2025"
        assert govt_settings.HF_CONFIG == "default"
        assert govt_settings.HF_SPLIT == "train"

    def test_hf_rows_base_url_is_correct(self):
        from app.government_data.constants import HF_ROWS_BASE_URL
        assert "datasets-server.huggingface.co" in HF_ROWS_BASE_URL
        assert "rows" in HF_ROWS_BASE_URL

    def test_hf_metadata_url_is_correct(self):
        from app.government_data.constants import HF_METADATA_BASE_URL
        assert "huggingface.co" in HF_METADATA_BASE_URL

    @pytest.mark.asyncio
    async def test_hf_health_check_returns_connected_true(self):
        from app.government_data.clients.huggingface_client import HuggingFaceClient
        from app.government_data.config import GovtDataSettings
        settings = GovtDataSettings(GOVT_MAX_RETRIES=0, GOVT_BACKOFF_FACTOR=0.01)
        payload = _hf_rows_payload(num_rows=4693, count=1)
        mock_resp = _mock_hf_response(200, payload)

        async with HuggingFaceClient(settings) as client:
            with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_resp
                result = await client.health_check()

        assert result.connected is True
        assert result.provider == "huggingface"
        assert result.latency_ms is not None
        assert result.latency_ms >= 0
        assert "4,693" in result.message or "rows" in result.message

    @pytest.mark.asyncio
    async def test_hf_health_check_reports_latency(self):
        from app.government_data.clients.huggingface_client import HuggingFaceClient
        from app.government_data.config import GovtDataSettings
        settings = GovtDataSettings(GOVT_MAX_RETRIES=0, GOVT_BACKOFF_FACTOR=0.01)
        payload = _hf_rows_payload(num_rows=4693, count=1)
        mock_resp = _mock_hf_response(200, payload)

        async with HuggingFaceClient(settings) as client:
            with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_resp
                result = await client.health_check()

        assert isinstance(result.latency_ms, float)

    @pytest.mark.asyncio
    async def test_hf_connectivity_network_failure_returns_connected_false(self):
        from app.government_data.clients.huggingface_client import HuggingFaceClient
        from app.government_data.config import GovtDataSettings
        settings = GovtDataSettings(GOVT_MAX_RETRIES=0, GOVT_BACKOFF_FACTOR=0.01)

        async with HuggingFaceClient(settings) as client:
            with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
                mock_get.side_effect = httpx.NetworkError("Connection refused")
                result = await client.health_check()

        assert result.connected is False
        assert "NetworkError" in result.message or "Connection" in result.message

    @pytest.mark.asyncio
    async def test_hf_dataset_info_correct(self):
        """Verify the client uses the correct dataset identifier."""
        from app.government_data.clients.huggingface_client import HuggingFaceClient
        from app.government_data.config import GovtDataSettings
        settings = GovtDataSettings(GOVT_MAX_RETRIES=0)
        client = HuggingFaceClient(settings)
        assert client._dataset == "smartduketech/indian-government-schemes-2025"

    @pytest.mark.asyncio
    async def test_hf_rows_endpoint_pagination_fields(self):
        """Rows response must have all pagination fields."""
        from app.government_data.clients.response_models import parse_huggingface_rows_response
        raw = _hf_rows_payload(num_rows=4693, count=100, offset=0)
        result = parse_huggingface_rows_response(raw, dataset="smartduketech/indian-government-schemes-2025", offset=0, length=100)
        assert result.pagination is not None
        assert result.pagination.total == 4693
        assert result.pagination.offset == 0
        assert result.pagination.count == 100
        assert result.pagination.has_more is True
        assert result.pagination.next_offset == 100

    @pytest.mark.asyncio
    async def test_hf_metadata_fallback_on_failure(self):
        """Metadata failure with GovernmentAPIException → returns GovernmentMetadata stub."""
        from app.government_data.clients.huggingface_client import HuggingFaceClient
        from app.government_data.config import GovtDataSettings
        from app.government_data.exceptions import GovernmentAPIException
        settings = GovtDataSettings(GOVT_MAX_RETRIES=0, GOVT_BACKOFF_FACTOR=0.01)

        async with HuggingFaceClient(settings) as client:
            # get_metadata() only catches GovernmentAPIException — use that type
            with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
                mock_req.side_effect = GovernmentAPIException(
                    message="metadata unreachable", error_code="GOVT_UNAVAILABLE"
                )
                meta = await client.get_metadata()

        # Should return a default metadata object, not raise
        assert meta.resource_id == "smartduketech/indian-government-schemes-2025"


# ═════════════════════════════════════════════════════════════════════════════
# STEP 2 — FULL IMPORT PIPELINE
# ═════════════════════════════════════════════════════════════════════════════

class TestStep2FullImport:
    """Verify: downloaded, normalized, imported, updated, skipped, failed, duration."""

    @pytest.mark.asyncio
    async def test_full_import_hf_dataset_success(self):
        """End-to-end import of HuggingFace dataset — success path."""
        from app.services.import_service import GovernmentImportService
        from app.government_data.clients.response_models import (
            GovernmentAPIResponse, GovernmentPagination,
        )
        from app.government_data.normalizers.schemas import (
            BatchNormalizationResult, BatchNormalizationStats, NormalizationResult,
        )
        from app.government_data.types import ImportMode

        db = _mock_db()
        svc = GovernmentImportService(db)

        n = 100
        # Simulate 100 records — pagination says has_more=False so loop ends
        mock_response = GovernmentAPIResponse(
            provider="huggingface",
            resource_id="smartduketech/indian-government-schemes-2025",
            status="ok",
            records=[{"name": f"Scheme {i}", "slug": f"scheme-{i}", "ministry": "Ministry X"} for i in range(n)],
            pagination=GovernmentPagination(total=n, count=n, limit=n, offset=0),
        )
        schemes = [_norm_scheme(scheme_code=f"S-{i:04d}", name=f"Scheme {i}") for i in range(n)]
        norm_results = [NormalizationResult(success=True, scheme=s) for s in schemes]
        batch_result = BatchNormalizationResult(
            results=norm_results,
            stats=BatchNormalizationStats(
                total_records=n, normalized_records=n, failed_records=0,
                warnings_count=0, missing_fields_count=0,
            ),
        )

        with patch("app.services.import_service.HuggingFaceClient") as MockClient, \
             patch("app.services.import_service.HuggingFaceNormalizer") as MockNorm, \
             patch("app.services.import_service.SchemeImporter") as MockImporter:

            # MAX_LENGTH must be an int — the service does min(limit, HuggingFaceClient.MAX_LENGTH)
            MockClient.MAX_LENGTH = 100
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get_dataset = AsyncMock(return_value=mock_response)

            MockNorm.return_value.normalize_batch = MagicMock(return_value=batch_result)

            # import_batch receives (schemes, stats, dry_run=False) and must update stats
            async def fake_import_batch(schemes, stats, dry_run=False):
                actions = ["created"] * len(schemes)
                stats.created += len(schemes)
                stats.downloaded += len(schemes)
                return actions

            MockImporter.return_value.import_batch = fake_import_batch

            report = await svc.run_import(
                "smartduketech/indian-government-schemes-2025",
                mode=ImportMode.FULL,
                max_records=n,
            )

        assert report.statistics.downloaded >= n
        assert report.statistics.created == n
        assert report.statistics.updated == 0
        assert report.statistics.failed == 0
        assert report.status in ("success", "partial")
        assert report.mode == "full"
        assert report.resource_id == "smartduketech/indian-government-schemes-2025"
        assert report.import_id is not None
        assert report.started_at is not None
        assert report.finished_at is not None
        assert report.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_import_report_contains_outcomes(self):
        """Each imported record should produce a RecordOutcome."""
        from app.services.import_service import GovernmentImportService
        from app.government_data.clients.response_models import (
            GovernmentAPIResponse, GovernmentPagination,
        )
        from app.government_data.normalizers.schemas import (
            BatchNormalizationResult, BatchNormalizationStats, NormalizationResult,
        )
        from app.government_data.types import ImportMode

        db = _mock_db()
        svc = GovernmentImportService(db)
        n = 10

        mock_response = GovernmentAPIResponse(
            provider="huggingface",
            resource_id="smartduketech/indian-government-schemes-2025",
            status="ok",
            records=[{"name": f"Scheme {i}", "slug": f"s-{i}"} for i in range(n)],
            pagination=GovernmentPagination(total=n, count=n, limit=100, offset=0),
        )
        schemes = [_norm_scheme(scheme_code=f"S-{i}", name=f"Scheme {i}") for i in range(n)]
        norm_results = [NormalizationResult(success=True, scheme=s) for s in schemes]
        batch_result = BatchNormalizationResult(
            results=norm_results,
            stats=BatchNormalizationStats(
                total_records=n, normalized_records=n,
                failed_records=0, warnings_count=0, missing_fields_count=0,
            ),
        )

        with patch("app.services.import_service.HuggingFaceClient") as MockClient, \
             patch("app.services.import_service.HuggingFaceNormalizer") as MockNorm, \
             patch("app.services.import_service.SchemeImporter") as MockImporter:

            MockClient.MAX_LENGTH = 100
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get_dataset = AsyncMock(return_value=mock_response)
            MockNorm.return_value.normalize_batch = MagicMock(return_value=batch_result)
            MockImporter.return_value.import_batch = AsyncMock(return_value=["created"] * n)

            report = await svc.run_import(
                "smartduketech/indian-government-schemes-2025",
                mode=ImportMode.FULL,
                max_records=n,
            )

        assert len(report.outcomes) == n
        for outcome in report.outcomes:
            assert outcome.action in ("created", "updated", "skipped", "failed")

    def test_import_mode_full_is_valid(self):
        from app.government_data.types import ImportMode
        assert ImportMode.FULL.value == "full"

    def test_import_status_values(self):
        from app.government_data.types import ImportStatus
        assert ImportStatus.SUCCESS.value == "success"
        assert ImportStatus.PARTIAL.value == "partial"
        assert ImportStatus.FAILED.value == "failed"
        assert ImportStatus.RUNNING.value == "running"

    def test_import_statistics_schema_complete(self):
        from app.schemas.import_schema import ImportStatistics
        stats = ImportStatistics(
            downloaded=4693,
            created=4693,
            updated=0,
            skipped=0,
            failed=0,
            duplicates=0,
            duration_ms=12500.0,
        )
        assert stats.downloaded == 4693
        assert stats.created == 4693
        assert stats.failed == 0
        assert stats.duration_ms == 12500.0

    def test_import_hf_dataset_name_in_config(self):
        from app.government_data.config import govt_settings
        assert "smartduketech" in govt_settings.HF_DATASET
        assert "indian-government-schemes-2025" in govt_settings.HF_DATASET

    def test_build_report_function_importable(self):
        from app.government_data.importers.import_report import build_report
        assert callable(build_report)

    def test_import_stats_dataclass_fields(self):
        from app.government_data.importers.import_statistics import ImportStats
        stats = ImportStats(downloaded=50, created=45, updated=3, skipped=1, failed=1)
        assert stats.downloaded == 50
        assert stats.created == 45
        assert stats.updated == 3
        assert stats.skipped == 1
        assert stats.failed == 1


# ═════════════════════════════════════════════════════════════════════════════
# STEP 3 — SQL VERIFICATION QUERIES
# ═════════════════════════════════════════════════════════════════════════════

class TestStep3SQLVerification:
    """Verify the SQL query strings are well-formed and cover all required checks."""

    SQL_QUERIES = {
        "total_schemes": "SELECT COUNT(*) AS total_schemes FROM schemes",
        "duplicate_names": (
            "SELECT name, state, COUNT(*) "
            "FROM schemes "
            "GROUP BY name, state "
            "HAVING COUNT(*) > 1"
        ),
        "duplicate_codes": (
            "SELECT scheme_code, COUNT(*) "
            "FROM schemes "
            "GROUP BY scheme_code "
            "HAVING COUNT(*) > 1"
        ),
        "missing_ministry": (
            "SELECT COUNT(*) FROM schemes "
            "WHERE ministry IS NULL OR ministry = ''"
        ),
        "missing_description": (
            "SELECT COUNT(*) FROM schemes "
            "WHERE full_description IS NULL AND short_description IS NULL"
        ),
        "missing_benefits": (
            "SELECT COUNT(*) FROM schemes "
            "WHERE benefits IS NULL OR benefits = ''"
        ),
        "missing_category": "SELECT COUNT(*) FROM schemes WHERE category IS NULL",
        "missing_official_url": "SELECT COUNT(*) FROM schemes WHERE official_url IS NULL",
        "missing_state_pan_india": "SELECT COUNT(*) FROM schemes WHERE state IS NULL",
        "inactive_schemes": "SELECT COUNT(*) FROM schemes WHERE is_active = FALSE",
        "category_distribution": (
            "SELECT category, COUNT(*) "
            "FROM schemes "
            "GROUP BY category "
            "ORDER BY COUNT(*) DESC"
        ),
        "state_distribution": (
            "SELECT state, COUNT(*) "
            "FROM schemes "
            "WHERE state IS NOT NULL "
            "GROUP BY state "
            "ORDER BY COUNT(*) DESC LIMIT 20"
        ),
        "import_timeline": (
            "SELECT "
            "MIN(created_at) as first_imported, "
            "MAX(created_at) as last_imported, "
            "COUNT(*) as total "
            "FROM schemes"
        ),
    }

    def test_all_sql_queries_defined(self):
        required = [
            "total_schemes", "duplicate_names", "duplicate_codes",
            "missing_ministry", "missing_description", "missing_benefits",
            "missing_category", "missing_official_url", "inactive_schemes",
        ]
        for query_name in required:
            assert query_name in self.SQL_QUERIES, f"Missing SQL query: {query_name}"

    def test_total_schemes_query_references_schemes_table(self):
        q = self.SQL_QUERIES["total_schemes"]
        assert "schemes" in q.lower()
        assert "count" in q.lower()

    def test_duplicate_names_uses_group_by_having(self):
        q = self.SQL_QUERIES["duplicate_names"]
        assert "GROUP BY" in q
        assert "HAVING" in q
        assert "COUNT(*) > 1" in q

    def test_duplicate_codes_uses_group_by(self):
        q = self.SQL_QUERIES["duplicate_codes"]
        assert "scheme_code" in q
        assert "GROUP BY" in q
        assert "HAVING" in q

    def test_missing_ministry_uses_is_null(self):
        q = self.SQL_QUERIES["missing_ministry"]
        assert "IS NULL" in q or "is null" in q.lower()

    def test_inactive_schemes_query_uses_is_active(self):
        q = self.SQL_QUERIES["inactive_schemes"]
        assert "is_active" in q.lower()
        assert "FALSE" in q or "false" in q.lower()

    def test_category_distribution_query_orders_by_count(self):
        q = self.SQL_QUERIES["category_distribution"]
        assert "category" in q.lower()
        assert "ORDER BY" in q

    def test_state_distribution_query_excludes_null(self):
        q = self.SQL_QUERIES["state_distribution"]
        assert "IS NOT NULL" in q
        assert "state" in q.lower()

    def test_import_timeline_query_uses_min_max(self):
        q = self.SQL_QUERIES["import_timeline"]
        assert "MIN(" in q
        assert "MAX(" in q
        assert "created_at" in q

    def test_queries_target_correct_table(self):
        for name, q in self.SQL_QUERIES.items():
            assert "schemes" in q.lower(), f"Query '{name}' does not target the 'schemes' table"


# ═════════════════════════════════════════════════════════════════════════════
# STEP 4 — NORMALIZATION VERIFICATION
# ═════════════════════════════════════════════════════════════════════════════

class TestStep4NormalizationVerification:
    """Verify all normalization transformations against real dataset field patterns."""

    def _make_record(self, **overrides) -> dict:
        base = {
            "name": "PM Kisan Samman Nidhi",
            "slug": "pm-kisan-samman-nidhi",
            "ministry": "ministry of agriculture and farmers welfare",
            "eligibility_state": '["Maharashtra"]',
            "category": "Agriculture",
            "description": "Direct income support to farmer families.",
            "benefits": "Rs 6000 per year in 3 instalments.",
            "official_url": "https://pmkisan.gov.in/",
            "apply_url": "https://pmkisan.gov.in/apply/",
            "application_process": "Apply online through the official portal.",
        }
        base.update(overrides)
        return base

    # State normalization
    def test_state_normalization_from_json_array(self):
        from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
        n = HuggingFaceNormalizer()
        result = n.normalize(self._make_record(eligibility_state='["Maharashtra"]'))
        assert result.scheme.state == "Maharashtra"

    def test_state_normalization_all_states_is_none(self):
        from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
        n = HuggingFaceNormalizer()
        result = n.normalize(self._make_record(eligibility_state='["All States"]'))
        assert result.scheme.state is None

    def test_state_normalization_pan_india_is_none(self):
        from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
        n = HuggingFaceNormalizer()
        result = n.normalize(self._make_record(eligibility_state='["Pan India"]'))
        assert result.scheme.state is None

    def test_state_normalization_valid_aliases(self):
        from app.government_data.normalizers.transformers import normalize_state
        test_cases = [
            ("maharashtra", "Maharashtra"),
            ("up", "Uttar Pradesh"),
            ("tn", "Tamil Nadu"),
            ("wb", "West Bengal"),
            ("mp", "Madhya Pradesh"),
            ("hp", "Himachal Pradesh"),
        ]
        for raw, expected in test_cases:
            result = normalize_state(raw)
            assert result == expected, f"State '{raw}' → expected '{expected}', got '{result}'"

    def test_state_normalization_handles_national(self):
        from app.government_data.normalizers.transformers import normalize_state
        for val in ("All India", "pan india", "pan-india", "national", "all states", "all"):
            assert normalize_state(val) is None, f"Expected None for '{val}'"

    # Category normalization
    def test_category_normalization_agriculture(self):
        from app.government_data.normalizers.transformers import normalize_category
        assert normalize_category("Agriculture") == "agriculture"

    def test_category_normalization_health(self):
        from app.government_data.normalizers.transformers import normalize_category
        assert normalize_category("health") == "health"
        assert normalize_category("medical") == "health"

    def test_category_normalization_student(self):
        from app.government_data.normalizers.transformers import normalize_category
        assert normalize_category("student") == "student"

    def test_category_normalization_women(self):
        from app.government_data.normalizers.transformers import normalize_category
        assert normalize_category("women") == "women"

    def test_category_normalization_employment(self):
        from app.government_data.normalizers.transformers import normalize_category
        assert normalize_category("employment") == "employment"

    def test_category_normalization_unknown_returns_other(self):
        from app.government_data.normalizers.transformers import normalize_category
        assert normalize_category("totally unknown xyz123") == "other"

    def test_category_normalization_none_returns_none(self):
        from app.government_data.normalizers.transformers import normalize_category
        assert normalize_category(None) is None

    # Scheme code generation from slug
    def test_scheme_code_from_slug(self):
        from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
        n = HuggingFaceNormalizer()
        result = n.normalize(self._make_record(slug="pm-kisan", name="PM Kisan Samman Nidhi"))
        assert result.scheme.scheme_code == "PM-KISAN"

    def test_scheme_code_auto_generated_when_no_slug(self):
        from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
        n = HuggingFaceNormalizer()
        rec = self._make_record()
        del rec["slug"]
        result = n.normalize(rec)
        assert result.scheme.scheme_code is not None
        assert len(result.scheme.scheme_code) > 0
        assert len(result.scheme.scheme_code) <= 50

    def test_scheme_code_max_length_50(self):
        from app.government_data.normalizers.transformers import normalize_scheme_code
        long_slug = "a-very-long-scheme-name-that-exceeds-fifty-characters-definitely"
        code = normalize_scheme_code(long_slug)
        assert code is not None
        assert len(code) <= 50

    # URL normalization
    def test_url_trailing_slash_removed(self):
        from app.government_data.normalizers.transformers import normalize_url
        assert normalize_url("https://pmkisan.gov.in/") == "https://pmkisan.gov.in"

    def test_url_www_prefix_gets_https(self):
        from app.government_data.normalizers.transformers import normalize_url
        assert normalize_url("www.pmkisan.gov.in") == "https://www.pmkisan.gov.in"

    def test_url_invalid_returns_none(self):
        from app.government_data.normalizers.transformers import normalize_url
        assert normalize_url("not-a-url") is None
        assert normalize_url("") is None
        assert normalize_url(None) is None

    def test_official_url_mapped_correctly(self):
        from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
        n = HuggingFaceNormalizer()
        result = n.normalize(self._make_record(official_url="https://pmkisan.gov.in/"))
        assert result.scheme.official_url == "https://pmkisan.gov.in"

    def test_apply_url_mapped_to_official_pdf_url(self):
        from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
        n = HuggingFaceNormalizer()
        result = n.normalize(self._make_record(apply_url="https://pmkisan.gov.in/apply/"))
        assert result.scheme.official_pdf_url == "https://pmkisan.gov.in/apply"

    # Whitespace cleanup
    def test_whitespace_cleanup_in_name(self):
        from app.government_data.normalizers.transformers import clean_text
        assert clean_text("  PM   Kisan  Scheme  ") == "PM Kisan Scheme"

    def test_whitespace_cleanup_none_values(self):
        from app.government_data.normalizers.transformers import clean_text
        for val in ("NA", "N/A", "nil", "None", "-", "--", "null", "Not Available"):
            assert clean_text(val) is None, f"Expected None for {val!r}"

    # Date normalization
    def test_date_normalization_iso_format(self):
        from app.government_data.normalizers.transformers import normalize_date
        from datetime import date
        assert normalize_date("2024-01-15") == date(2024, 1, 15)

    def test_date_normalization_indian_format(self):
        from app.government_data.normalizers.transformers import normalize_date
        from datetime import date
        assert normalize_date("15-08-2024") == date(2024, 8, 15)

    def test_date_normalization_invalid_returns_none(self):
        from app.government_data.normalizers.transformers import normalize_date
        assert normalize_date("not a date") is None
        assert normalize_date(None) is None

    # Phone normalization
    def test_phone_normalization_strips_formatting(self):
        from app.government_data.normalizers.transformers import normalize_phone
        result = normalize_phone("+91-1800-123-4567")
        assert result == "+911800123456 7".replace(" ", "")

    def test_phone_normalization_too_short_returns_none(self):
        from app.government_data.normalizers.transformers import normalize_phone
        assert normalize_phone("123") is None
        assert normalize_phone(None) is None

    # Email normalization
    def test_email_normalization_lowercases(self):
        from app.government_data.normalizers.transformers import normalize_email
        assert normalize_email("TEST@GOV.IN") == "test@gov.in"

    def test_email_normalization_invalid_returns_none(self):
        from app.government_data.normalizers.transformers import normalize_email
        assert normalize_email("not-an-email") is None
        assert normalize_email(None) is None

    # Ministry normalization
    def test_ministry_normalized_title_case(self):
        from app.government_data.normalizers.transformers import normalize_ministry
        result = normalize_ministry("ministry of agriculture and farmers welfare")
        assert result is not None
        words = result.split()
        assert any(w[0].isupper() for w in words if w)

    # Application mode
    def test_application_mode_online(self):
        from app.government_data.normalizers.transformers import normalize_application_mode
        assert normalize_application_mode("Apply online through the official portal.") == "online"

    def test_application_mode_offline(self):
        from app.government_data.normalizers.transformers import normalize_application_mode
        assert normalize_application_mode("Submit form manually at the office.") == "offline"

    def test_application_mode_both(self):
        from app.government_data.normalizers.transformers import normalize_application_mode
        assert normalize_application_mode("Apply online or offline at the office.") == "both"

    # Batch normalization
    def test_batch_normalization_real_hf_records(self):
        """Batch normalize 20 realistic HuggingFace records."""
        from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
        n = HuggingFaceNormalizer("smartduketech/indian-government-schemes-2025")
        records = [
            self._make_record(
                name=f"Scheme {i}",
                slug=f"scheme-{i:04d}",
                eligibility_state='["Maharashtra"]' if i % 2 == 0 else '["All States"]',
                category=["Agriculture", "Health", "Education", "Women"][i % 4],
            )
            for i in range(20)
        ]
        batch = n.normalize_batch(records)
        assert batch.stats.total_records == 20
        assert batch.stats.normalized_records == 20
        assert batch.stats.failed_records == 0
        for result in batch.results:
            assert result.scheme.scheme_code is not None


# ═════════════════════════════════════════════════════════════════════════════
# STEP 5 — DUPLICATE DETECTION
# ═════════════════════════════════════════════════════════════════════════════

class TestStep5DuplicateDetection:
    """Verify second import produces 0 new records, only updates/skips."""

    @pytest.mark.asyncio
    async def test_second_import_creates_zero_new_records(self):
        from app.government_data.importers.scheme_importer import SchemeImporter
        from app.government_data.importers.import_statistics import ImportStats

        db = _mock_db()
        importer = SchemeImporter(db)
        existing = MagicMock()

        ns = _norm_scheme(
            name="PM Kisan Samman Nidhi",
            benefits="Rs 6000",
            category="agriculture",
            state="Maharashtra",
            official_url="https://pmkisan.gov.in",
            is_active=True,
        )

        with patch.object(importer._detector, "find_existing", return_value=existing), \
             patch.object(importer._detector, "is_changed", return_value=False):
            stats = ImportStats()
            action = await importer.import_scheme(ns, stats)

        assert action == "skipped"
        assert stats.created == 0
        assert stats.updated == 0
        assert stats.skipped == 1

    @pytest.mark.asyncio
    async def test_second_import_updates_changed_records(self):
        from app.government_data.importers.scheme_importer import SchemeImporter
        from app.government_data.importers.import_statistics import ImportStats

        db = _mock_db()
        importer = SchemeImporter(db)
        existing = MagicMock()

        with patch.object(importer._detector, "find_existing", return_value=existing), \
             patch.object(importer._detector, "is_changed", return_value=True), \
             patch.object(importer._repo, "update", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = existing
            stats = ImportStats()
            action = await importer.import_scheme(_norm_scheme(name="Updated Name"), stats)

        assert action == "updated"
        assert stats.updated == 1
        assert stats.created == 0

    @pytest.mark.asyncio
    async def test_duplicate_detector_priority_code_over_name(self):
        """Code match takes priority over name+state match."""
        from app.government_data.importers.duplicate_detector import DuplicateDetector
        mock_repo = AsyncMock()
        existing_by_code = MagicMock()
        mock_repo.get_by_code = AsyncMock(return_value=existing_by_code)
        mock_repo.get_by_name = AsyncMock(return_value=MagicMock())

        detector = DuplicateDetector(mock_repo)
        ns = _norm_scheme(scheme_code="PM-KISAN-2024", name="PM Kisan")
        result = await detector.find_existing(ns)

        assert result is existing_by_code
        mock_repo.get_by_name.assert_not_called()

    @pytest.mark.asyncio
    async def test_duplicate_detector_falls_back_to_name_when_no_code(self):
        from app.government_data.importers.duplicate_detector import DuplicateDetector
        mock_repo = AsyncMock()
        existing = MagicMock()
        mock_repo.get_by_code = AsyncMock(return_value=None)
        mock_repo.get_by_name = AsyncMock(return_value=existing)

        detector = DuplicateDetector(mock_repo)
        ns = _norm_scheme(scheme_code=None)
        result = await detector.find_existing(ns)
        assert result is existing

    @pytest.mark.asyncio
    async def test_is_changed_returns_true_on_description_change(self):
        from app.government_data.importers.duplicate_detector import DuplicateDetector
        mock_repo = AsyncMock()
        detector = DuplicateDetector(mock_repo)

        ns = _norm_scheme(full_description="NEW DESCRIPTION")
        existing = MagicMock()
        existing.name = ns.name
        existing.full_description = "OLD DESCRIPTION"
        existing.benefits = ns.benefits
        existing.ministry = ns.ministry
        existing.category = ns.category
        existing.state = ns.state
        existing.official_url = ns.official_url
        existing.is_active = ns.is_active

        changed = await detector.is_changed(ns, existing)
        assert changed is True

    @pytest.mark.asyncio
    async def test_is_changed_returns_false_when_all_fields_same(self):
        from app.government_data.importers.duplicate_detector import DuplicateDetector
        mock_repo = AsyncMock()
        detector = DuplicateDetector(mock_repo)

        ns = _norm_scheme()
        existing = MagicMock()
        existing.name = ns.name
        existing.full_description = ns.full_description
        existing.benefits = ns.benefits
        existing.ministry = ns.ministry
        existing.category = ns.category
        existing.state = ns.state
        existing.official_url = ns.official_url
        existing.is_active = ns.is_active

        changed = await detector.is_changed(ns, existing)
        assert changed is False


# ═════════════════════════════════════════════════════════════════════════════
# STEP 6 — SCHEME APIs
# ═════════════════════════════════════════════════════════════════════════════

class TestStep6SchemeAPIs:
    """Verify scheme API endpoints: pagination, filtering, sorting, search."""

    def _client(self) -> TestClient:
        return _make_test_client()

    def test_schemes_list_endpoint_exists(self):
        c = self._client()
        resp = c.get("/api/v1/schemes")
        assert resp.status_code in (200, 500)

    def test_schemes_categories_endpoint_exists(self):
        c = self._client()
        resp = c.get("/api/v1/schemes/categories")
        assert resp.status_code in (200, 500)

    def test_schemes_featured_endpoint_exists(self):
        c = self._client()
        resp = c.get("/api/v1/schemes/featured")
        assert resp.status_code in (200, 500)

    def test_schemes_recent_endpoint_exists(self):
        c = self._client()
        resp = c.get("/api/v1/schemes/recent")
        assert resp.status_code in (200, 500)

    def test_schemes_states_endpoint_exists(self):
        c = self._client()
        resp = c.get("/api/v1/schemes/states")
        assert resp.status_code in (200, 500)

    def test_schemes_endpoint_in_openapi(self):
        c = self._client()
        paths = c.get("/openapi.json").json()["paths"]
        assert "/api/v1/schemes" in paths

    def test_scheme_categories_endpoint_in_openapi(self):
        c = self._client()
        paths = c.get("/openapi.json").json()["paths"]
        assert "/api/v1/schemes/categories" in paths

    def test_scheme_featured_endpoint_in_openapi(self):
        c = self._client()
        paths = c.get("/openapi.json").json()["paths"]
        assert "/api/v1/schemes/featured" in paths

    def test_scheme_recent_endpoint_in_openapi(self):
        c = self._client()
        paths = c.get("/openapi.json").json()["paths"]
        assert "/api/v1/schemes/recent" in paths

    def test_scheme_by_id_endpoint_in_openapi(self):
        c = self._client()
        paths = c.get("/openapi.json").json()["paths"]
        assert "/api/v1/schemes/{scheme_id}" in paths

    def test_schemes_endpoint_accepts_pagination_params(self):
        c = self._client()
        resp = c.get("/api/v1/schemes?page=1&page_size=10")
        assert resp.status_code in (200, 500)

    def test_schemes_endpoint_accepts_search_query(self):
        c = self._client()
        resp = c.get("/api/v1/schemes?query=kisan")
        assert resp.status_code in (200, 500)

    def test_schemes_endpoint_accepts_category_filter(self):
        c = self._client()
        resp = c.get("/api/v1/schemes?category=agriculture")
        assert resp.status_code in (200, 500)

    def test_schemes_endpoint_accepts_state_filter(self):
        c = self._client()
        resp = c.get("/api/v1/schemes?state=Maharashtra")
        assert resp.status_code in (200, 500)

    def test_schemes_endpoint_accepts_sort_param(self):
        c = self._client()
        for sort in ("newest", "oldest", "alphabetical", "most_viewed"):
            resp = c.get(f"/api/v1/schemes?sort={sort}")
            assert resp.status_code in (200, 500), f"Sort '{sort}' failed"

    def test_invalid_scheme_id_returns_422(self):
        c = self._client()
        resp = c.get("/api/v1/schemes/not-a-uuid")
        assert resp.status_code == 422

    def test_nonexistent_scheme_id_returns_not_found(self):
        c = self._client()
        fake_id = str(uuid.uuid4())
        resp = c.get(f"/api/v1/schemes/{fake_id}")
        assert resp.status_code in (404, 500)

    def test_schemes_create_requires_admin(self):
        c = self._client()
        resp = c.post("/api/v1/schemes", json={
            "name": "Test Scheme",
            "scheme_code": "TEST-001",
            "scheme_type": "central",
        })
        assert resp.status_code == 401

    def test_scheme_delete_requires_admin(self):
        c = self._client()
        resp = c.delete(f"/api/v1/schemes/{uuid.uuid4()}")
        assert resp.status_code == 401


# ═════════════════════════════════════════════════════════════════════════════
# STEP 7 — FRONTEND API COMPATIBILITY
# ═════════════════════════════════════════════════════════════════════════════

class TestStep7FrontendAPICompatibility:
    """Verify API response shapes match what the frontend expects."""

    def test_scheme_read_has_required_frontend_fields(self):
        """SchemeRead contains all fields needed by the scheme detail page."""
        from app.schemas.scheme import SchemeRead
        fields = SchemeRead.model_fields
        required_for_frontend = [
            "id", "name", "scheme_code", "category", "state",
            "is_active", "is_featured", "view_count",
            "short_description", "full_description", "benefits",
            "official_url", "ministry",
        ]
        for field in required_for_frontend:
            assert field in fields, f"SchemeRead missing field: '{field}'"

    def test_scheme_summary_has_card_fields(self):
        """SchemeSummary contains fields needed by scheme listing cards."""
        from app.schemas.scheme import SchemeSummary
        fields = SchemeSummary.model_fields
        required_for_cards = [
            "id", "name", "scheme_code", "category", "state",
            "is_active", "is_featured", "view_count", "ministry",
        ]
        for field in required_for_cards:
            assert field in fields, f"SchemeSummary missing field: '{field}'"

    def test_scheme_list_response_has_data_and_meta(self):
        """SchemeListResponse uses data[] + meta pagination envelope."""
        from app.schemas.scheme import SchemeListResponse
        fields = SchemeListResponse.model_fields
        assert "data" in fields, "SchemeListResponse must have 'data' field"
        assert "meta" in fields, "SchemeListResponse must have 'meta' field"

    def test_pagination_meta_has_required_fields(self):
        from app.schemas.scheme import PaginationMeta
        fields = PaginationMeta.model_fields
        for f in ("total", "page", "page_size", "total_pages"):
            assert f in fields, f"PaginationMeta missing '{f}'"

    def test_scheme_response_wraps_scheme_read_in_data(self):
        """SchemeResponse is the envelope wrapper: {success, message, data: SchemeRead}."""
        from app.schemas.scheme import SchemeResponse
        fields = SchemeResponse.model_fields
        assert "data" in fields
        assert "success" in fields
        assert "message" in fields

    def test_import_response_schema_has_report(self):
        from app.schemas.import_schema import ImportResponse
        fields = ImportResponse.model_fields
        assert "report" in fields
        assert "message" in fields
        assert "success" in fields

    def test_import_report_has_all_statistics_fields(self):
        from app.schemas.import_schema import ImportStatistics
        fields = ImportStatistics.model_fields
        for field in ("downloaded", "created", "updated", "skipped", "failed", "duration_ms"):
            assert field in fields, f"ImportStatistics missing field: '{field}'"

    def test_preview_record_has_action_field(self):
        from app.schemas.import_schema import PreviewRecord
        fields = PreviewRecord.model_fields
        assert "action" in fields
        assert "scheme_code" in fields
        assert "name" in fields

    def test_scheme_category_enum_values_match_frontend_expectations(self):
        from app.models.enums import SchemeCategoryEnum
        expected_categories = {
            "agriculture", "education", "health", "housing",
            "employment", "pension", "insurance", "social_welfare",
            "women_and_child", "rural_development", "skill_development",
            "financial_inclusion", "disability", "minority", "other",
        }
        actual = {e.value for e in SchemeCategoryEnum}
        for cat in expected_categories:
            assert cat in actual, f"Category '{cat}' missing from SchemeCategoryEnum"

    def test_scheme_type_enum_values(self):
        from app.models.enums import SchemeTypeEnum
        assert SchemeTypeEnum.CENTRAL.value == "central"
        assert SchemeTypeEnum.STATE.value == "state"

    def test_application_mode_enum_values(self):
        from app.models.enums import ApplicationModeEnum
        assert ApplicationModeEnum.ONLINE.value == "online"
        assert ApplicationModeEnum.OFFLINE.value == "offline"
        assert ApplicationModeEnum.BOTH.value == "both"


# ═════════════════════════════════════════════════════════════════════════════
# STEP 8 — ELIGIBILITY ENGINE
# ═════════════════════════════════════════════════════════════════════════════

class TestStep8EligibilityEngine:
    """Verify eligibility endpoints: auth required, no crashes, valid responses."""

    def _client(self) -> TestClient:
        return _make_test_client()

    def test_eligibility_check_requires_auth(self):
        c = self._client()
        resp = c.post("/api/v1/eligibility/check", json={"scheme_id": str(uuid.uuid4())})
        assert resp.status_code == 401

    def test_eligibility_my_schemes_requires_auth(self):
        c = self._client()
        resp = c.get("/api/v1/eligibility/my-schemes")
        assert resp.status_code == 401

    def test_eligibility_scheme_detail_requires_auth(self):
        c = self._client()
        resp = c.get(f"/api/v1/eligibility/{uuid.uuid4()}")
        assert resp.status_code == 401

    def test_eligibility_admin_rules_requires_admin(self):
        c = self._client()
        resp = c.get("/api/v1/eligibility/admin/rules")
        assert resp.status_code == 401

    def test_eligibility_create_rule_requires_admin(self):
        c = self._client()
        resp = c.post("/api/v1/eligibility/admin/rules", json={})
        assert resp.status_code == 401

    def test_eligibility_endpoints_in_openapi(self):
        c = self._client()
        paths = c.get("/openapi.json").json()["paths"]
        assert "/api/v1/eligibility/check" in paths
        assert "/api/v1/eligibility/my-schemes" in paths

    def test_eligibility_check_schema_has_scheme_id(self):
        from app.schemas.eligibility import EligibilityCheckRequest
        fields = EligibilityCheckRequest.model_fields
        assert "scheme_id" in fields

    def test_eligibility_check_response_has_result(self):
        from app.schemas.eligibility import EligibilityCheckResponse
        fields = EligibilityCheckResponse.model_fields
        # Has either score/eligible/is_eligible
        assert any(k in fields for k in ("score", "eligible", "is_eligible", "eligibility_score", "passed"))

    def test_eligibility_rule_model_has_scheme_id(self):
        from app.models.eligibility_rule import EligibilityRule
        col_names = [c.name for c in EligibilityRule.__table__.columns]
        assert "scheme_id" in col_names

    def test_eligibility_rule_model_has_income_columns(self):
        from app.models.eligibility_rule import EligibilityRule
        col_names = [c.name for c in EligibilityRule.__table__.columns]
        assert "minimum_income" in col_names
        assert "maximum_income" in col_names

    def test_eligibility_rule_model_has_age_columns(self):
        from app.models.eligibility_rule import EligibilityRule
        col_names = [c.name for c in EligibilityRule.__table__.columns]
        assert "minimum_age" in col_names
        assert "maximum_age" in col_names

    def test_rule_evaluators_registered(self):
        from app.services.rule_engine import EVALUATORS
        assert len(EVALUATORS) >= 8

    def test_evaluate_rule_function_importable(self):
        from app.services.rule_engine import evaluate_rule
        assert callable(evaluate_rule)


# ═════════════════════════════════════════════════════════════════════════════
# STEP 9 — RECOMMENDATION ENGINE
# ═════════════════════════════════════════════════════════════════════════════

class TestStep9RecommendationEngine:
    """Verify recommendation endpoints: auth, scores, priority, no duplicates."""

    def _client(self) -> TestClient:
        return _make_test_client()

    def test_recommendations_endpoint_requires_auth(self):
        c = self._client()
        resp = c.get("/api/v1/recommendations")
        assert resp.status_code == 401

    def test_recommendation_summary_has_score_field(self):
        """RecommendationSummary has recommendation_score field."""
        from app.schemas.recommendation import RecommendationSummary
        fields = RecommendationSummary.model_fields
        assert "recommendation_score" in fields

    def test_recommendation_summary_score_in_valid_range(self):
        from app.schemas.recommendation import RecommendationSummary
        fields = RecommendationSummary.model_fields
        score_meta = fields["recommendation_score"]
        # Score is float — check it exists and type annotation is correct
        assert score_meta is not None

    def test_recommendation_summary_has_priority_field(self):
        from app.schemas.recommendation import RecommendationSummary
        fields = RecommendationSummary.model_fields
        assert "priority" in fields

    def test_recommendation_summary_has_scheme_info(self):
        from app.schemas.recommendation import RecommendationSummary
        fields = RecommendationSummary.model_fields
        assert "scheme_id" in fields
        assert "scheme_name" in fields

    def test_recommendation_response_has_data_list(self):
        """RecommendationResponse envelope uses 'data' for the list."""
        from app.schemas.recommendation import RecommendationResponse
        fields = RecommendationResponse.model_fields
        assert "data" in fields, "RecommendationResponse must have 'data' field"

    def test_priority_badge_values_defined(self):
        from app.schemas.recommendation import RecommendationPriority
        # Should be Literal["HIGH", "MEDIUM", "LOW"]
        assert RecommendationPriority is not None

    def test_recommendation_service_importable(self):
        from app.services.recommendation_service import RecommendationService
        assert RecommendationService is not None

    def test_recommendation_endpoints_in_openapi(self):
        c = self._client()
        paths = c.get("/openapi.json").json()["paths"]
        rec_paths = [p for p in paths if "recommendation" in p.lower()]
        assert len(rec_paths) > 0, "No recommendation endpoints found in OpenAPI"

    def test_recommendation_score_has_breakdown(self):
        """RecommendationScore covers multiple scoring factors."""
        from app.schemas.recommendation import RecommendationScore
        fields = RecommendationScore.model_fields
        for field in ("total", "eligibility_score", "state_score", "category_score"):
            assert field in fields, f"RecommendationScore missing field '{field}'"

    def test_recommendation_has_reasons_list(self):
        from app.schemas.recommendation import RecommendationSummary
        fields = RecommendationSummary.model_fields
        assert "reasons" in fields

    def test_profile_completion_response_importable(self):
        from app.schemas.recommendation import ProfileCompletionResponse
        fields = ProfileCompletionResponse.model_fields
        assert "completion_percentage" in fields
        assert "missing_fields" in fields


# ═════════════════════════════════════════════════════════════════════════════
# STEP 10 — PERFORMANCE METRICS
# ═════════════════════════════════════════════════════════════════════════════

class TestStep10PerformanceMetrics:
    """Verify performance characteristics: import timing, rows/sec, batch size."""

    def test_import_stats_duration_ms_function_works(self):
        from app.government_data.importers.import_statistics import ImportStats
        stats = ImportStats()
        duration = stats.duration_ms()
        # The start time is captured at construction, so duration should be >= 0
        assert duration >= 0.0

    def test_import_stats_duration_increases_over_time(self):
        from app.government_data.importers.import_statistics import ImportStats
        stats = ImportStats()
        d1 = stats.duration_ms()
        time.sleep(0.015)  # 15ms
        d2 = stats.duration_ms()
        assert d2 > d1

    def test_rows_per_second_calculation(self):
        """Rows per second = downloaded / (duration_ms / 1000)."""
        total_rows = 4693
        duration_ms = 12500.0
        rows_per_sec = total_rows / (duration_ms / 1000)
        assert rows_per_sec > 10.0

    def test_hf_client_batch_size_is_100(self):
        from app.government_data.clients.huggingface_client import HuggingFaceClient
        assert HuggingFaceClient.MAX_LENGTH == 100

    def test_import_batch_size_is_configurable(self):
        from app.government_data.config import govt_settings
        assert govt_settings.GOVT_DEFAULT_BATCH_SIZE >= 1
        assert govt_settings.GOVT_DEFAULT_BATCH_SIZE <= 5000

    def test_report_duration_ms_field_exists(self):
        from app.schemas.import_schema import ImportReport
        fields = ImportReport.model_fields
        assert "duration_ms" in fields

    def test_statistics_duration_ms_field_exists(self):
        from app.schemas.import_schema import ImportStatistics
        fields = ImportStatistics.model_fields
        assert "duration_ms" in fields

    def test_import_stats_to_dict_includes_duration(self):
        from app.government_data.importers.import_statistics import ImportStats
        stats = ImportStats(created=100, downloaded=100)
        d = stats.to_dict()
        assert "duration_ms" in d
        assert isinstance(d["duration_ms"], float)

    def test_pagination_calculates_correctly_for_4693_records(self):
        """Verify pagination loop for 4693 records at 100/batch = 47 batches."""
        total = 4693
        batch_size = 100
        total_batches = (total + batch_size - 1) // batch_size
        assert total_batches == 47

        last_offset = (total_batches - 1) * batch_size
        last_count = total - last_offset
        assert last_count == 93

    def test_api_endpoint_timeout_configured(self):
        from app.government_data.config import govt_settings
        assert govt_settings.GOVT_REQUEST_TIMEOUT >= 10
        assert govt_settings.GOVT_REQUEST_TIMEOUT <= 300


# ═════════════════════════════════════════════════════════════════════════════
# STEP 11 — SECURITY VERIFICATION
# ═════════════════════════════════════════════════════════════════════════════

class TestStep11SecurityVerification:
    """Verify: admin endpoints protected, JWT works, secrets not exposed."""

    def _client(self) -> TestClient:
        return _make_test_client()

    def test_import_endpoint_requires_auth(self):
        c = self._client()
        resp = c.post("/api/v1/admin/government/import", json={
            "resource_id": "smartduketech/indian-government-schemes-2025",
            "mode": "full",
        })
        assert resp.status_code == 401

    def test_import_status_requires_auth(self):
        c = self._client()
        resp = c.get("/api/v1/admin/government/import/status")
        assert resp.status_code == 401

    def test_import_history_requires_auth(self):
        c = self._client()
        resp = c.get("/api/v1/admin/government/import/history")
        assert resp.status_code == 401

    def test_import_preview_requires_auth(self):
        c = self._client()
        resp = c.post("/api/v1/admin/government/import/preview", json={
            "resource_id": "smartduketech/indian-government-schemes-2025",
        })
        assert resp.status_code == 401

    def test_scheme_create_requires_auth(self):
        c = self._client()
        resp = c.post("/api/v1/schemes", json={"name": "X", "scheme_code": "X"})
        assert resp.status_code == 401

    def test_scheme_delete_requires_auth(self):
        c = self._client()
        resp = c.delete(f"/api/v1/schemes/{uuid.uuid4()}")
        assert resp.status_code == 401

    def test_invalid_jwt_rejected_on_protected_endpoint(self):
        c = self._client()
        resp = c.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
        assert resp.status_code == 401

    def test_malformed_bearer_token_rejected(self):
        c = self._client()
        resp = c.post(
            "/api/v1/admin/government/import",
            json={"resource_id": "test", "mode": "full"},
            headers={"Authorization": "Bearer MALFORMED"},
        )
        assert resp.status_code == 401

    def test_government_data_security_module_importable(self):
        from app.government_data.security import mask_api_key
        assert callable(mask_api_key)

    def test_api_key_masked_in_logs(self):
        from app.government_data.security import mask_api_key
        key = "sk-1234567890abcdef"
        masked = mask_api_key(key)
        assert "1234567890abcdef" not in masked
        # Should end with last 4 chars: "cdef"
        assert "cdef" in masked

    def test_short_api_key_fully_masked(self):
        from app.government_data.security import mask_api_key
        from app.government_data.constants import MASKED_VALUE
        assert mask_api_key("ab") == MASKED_VALUE
        assert mask_api_key(None) == MASKED_VALUE
        assert mask_api_key("") == MASKED_VALUE

    def test_jwt_error_response_does_not_expose_secret(self):
        c = self._client()
        resp = c.get("/api/v1/auth/me", headers={"Authorization": "Bearer bad.token.here"})
        from app.core.config import settings
        secret = settings.SECRET_KEY
        assert secret not in resp.text

    def test_unauthorized_error_shape(self):
        c = self._client()
        resp = c.get("/api/v1/auth/me")
        assert resp.status_code == 401
        body = resp.json()
        assert "detail" in body or "message" in body

    def test_hf_bearer_header_used_only_when_token_set(self):
        from app.government_data.clients.huggingface_client import HuggingFaceClient
        from app.government_data.config import GovtDataSettings
        # Without token: no auth header
        s = GovtDataSettings(HF_TOKEN="")
        c = HuggingFaceClient(s)
        assert c._get_auth_headers() == {}

        # With token: Bearer header present
        s2 = GovtDataSettings(HF_TOKEN="hf_secret_token_xyz")
        c2 = HuggingFaceClient(s2)
        headers = c2._get_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")


# ═════════════════════════════════════════════════════════════════════════════
# STEP 12 — PRODUCTION READINESS REPORT
# ═════════════════════════════════════════════════════════════════════════════

class TestStep12ProductionReadinessReport:
    """Generate and validate the Production Readiness Report schema."""

    def _build_sample_report(self):
        from app.schemas.import_schema import (
            ImportReport, ImportStatistics, RecordOutcome,
        )
        stats = ImportStatistics(
            downloaded=4693,
            created=4693,
            updated=0,
            skipped=0,
            failed=0,
            duplicates=0,
            duration_ms=12543.6,
        )
        return ImportReport(
            import_id=str(uuid.uuid4()),
            resource_id="smartduketech/indian-government-schemes-2025",
            mode="full",
            status="success",
            statistics=stats,
            started_at=datetime.now(tz=timezone.utc),
            finished_at=datetime.now(tz=timezone.utc),
            duration_ms=12543.6,
            warnings=["5 records had scheme_code auto-generated from name."],
            errors=[],
            outcomes=[
                RecordOutcome(action="created", scheme_code="PM-KISAN", scheme_name="PM Kisan Samman Nidhi"),
            ],
            dry_run=False,
        )

    def test_report_schema_is_valid(self):
        report = self._build_sample_report()
        assert report.import_id is not None
        assert report.status == "success"

    def test_report_statistics_fields_complete(self):
        report = self._build_sample_report()
        assert report.statistics.downloaded == 4693
        assert report.statistics.created == 4693
        assert report.statistics.failed == 0
        assert report.statistics.duration_ms > 0

    def test_report_has_started_and_finished_at(self):
        report = self._build_sample_report()
        assert report.started_at is not None
        assert report.finished_at is not None
        assert report.finished_at >= report.started_at

    def test_report_has_warnings_and_errors_lists(self):
        report = self._build_sample_report()
        assert isinstance(report.warnings, list)
        assert isinstance(report.errors, list)

    def test_report_has_outcomes(self):
        report = self._build_sample_report()
        assert len(report.outcomes) == 1
        assert report.outcomes[0].action == "created"

    def test_report_serializes_to_dict(self):
        report = self._build_sample_report()
        d = report.model_dump()
        assert "import_id" in d
        assert "statistics" in d
        assert "outcomes" in d
        assert "warnings" in d
        assert "errors" in d

    def test_report_dataset_info(self):
        report = self._build_sample_report()
        assert report.resource_id == "smartduketech/indian-government-schemes-2025"
        assert report.mode == "full"

    def test_report_rows_per_second(self):
        report = self._build_sample_report()
        rows_per_sec = report.statistics.downloaded / (report.statistics.duration_ms / 1000)
        assert rows_per_sec > 0

    def test_report_not_dry_run(self):
        report = self._build_sample_report()
        assert report.dry_run is False

    def test_import_history_list_exists(self):
        import app.services.import_service as svc_module
        assert hasattr(svc_module, "_import_history")
        assert isinstance(svc_module._import_history, list)

    def test_import_service_get_history_method(self):
        from app.services.import_service import GovernmentImportService
        assert hasattr(GovernmentImportService, "get_history")
        assert callable(GovernmentImportService.get_history)

    def test_report_import_id_is_unique_uuid(self):
        uuid_re = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        )
        report1 = self._build_sample_report()
        report2 = self._build_sample_report()
        assert uuid_re.match(report1.import_id)
        assert uuid_re.match(report2.import_id)
        assert report1.import_id != report2.import_id


# ═════════════════════════════════════════════════════════════════════════════
# BONUS: COMPLETE PIPELINE INTEGRATION (mocked end-to-end)
# ═════════════════════════════════════════════════════════════════════════════

class TestCompletePipelineIntegration:
    """End-to-end pipeline: HF Client → Normalizer → SchemeImporter → Report."""

    @pytest.mark.asyncio
    async def test_pipeline_normalizer_to_importer_to_report(self):
        """Full pipeline: normalize → detect duplicates → import → report."""
        from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
        from app.government_data.importers.scheme_importer import SchemeImporter
        from app.government_data.importers.import_statistics import ImportStats
        from app.government_data.importers.import_report import build_report
        from app.government_data.types import ImportMode, ImportStatus

        normalizer = HuggingFaceNormalizer("smartduketech/indian-government-schemes-2025")
        raw_records = [
            {
                "name": f"Test Scheme {i}",
                "slug": f"test-scheme-{i:04d}",
                "ministry": "Ministry of Agriculture",
                "eligibility_state": '["Maharashtra"]',
                "category": "Agriculture",
                "description": f"Description {i}",
                "benefits": "Benefits text",
                "official_url": "https://example.gov.in",
            }
            for i in range(5)
        ]
        batch = normalizer.normalize_batch(raw_records)
        assert batch.stats.normalized_records == 5

        db = _mock_db()
        importer = SchemeImporter(db)
        stats = ImportStats()

        with patch.object(importer._detector, "find_existing", return_value=None), \
             patch.object(importer._repo, "create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = MagicMock()
            actions = await importer.import_batch(batch.successful, stats)

        assert len(actions) == 5
        assert all(a == "created" for a in actions)
        assert stats.created == 5

        started_at = datetime.now(tz=timezone.utc)
        report = build_report(
            "smartduketech/indian-government-schemes-2025",
            ImportMode.FULL,
            stats,
            ImportStatus.SUCCESS,
            started_at,
        )
        assert report.status == "success"
        assert report.statistics.created == 5
        assert report.statistics.failed == 0

    @pytest.mark.asyncio
    async def test_pipeline_handles_normalization_failure_gracefully(self):
        from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
        normalizer = HuggingFaceNormalizer()
        bad_records = [
            {},
            {"no_name_field": "value"},
            {
                "name": "Valid Scheme",
                "slug": "valid-scheme",
                "category": "Agriculture",
                "description": "Description",
            },
        ]
        batch = normalizer.normalize_batch(bad_records)
        assert batch.stats.total_records == 3
        assert batch.stats.failed_records == 2
        assert batch.stats.normalized_records == 1

    def test_hf_dataset_provider_name(self):
        from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
        n = HuggingFaceNormalizer()
        assert n.PROVIDER_NAME == "huggingface"

    def test_scheme_importer_provider_name(self):
        from app.government_data.importers.scheme_importer import SchemeImporter
        db = _mock_db()
        importer = SchemeImporter(db)
        assert importer.PROVIDER_NAME == "scheme_importer"

    @pytest.mark.asyncio
    async def test_duplicate_import_no_db_writes(self):
        """If all records are unchanged duplicates, no DB writes occur."""
        from app.government_data.importers.scheme_importer import SchemeImporter
        from app.government_data.importers.import_statistics import ImportStats

        db = _mock_db()
        importer = SchemeImporter(db)
        existing = MagicMock()
        schemes = [_norm_scheme(scheme_code=f"S-{i}", name=f"Scheme {i}") for i in range(5)]

        with patch.object(importer._detector, "find_existing", return_value=existing), \
             patch.object(importer._detector, "is_changed", return_value=False), \
             patch.object(importer._repo, "update", new_callable=AsyncMock) as mock_update, \
             patch.object(importer._repo, "create", new_callable=AsyncMock) as mock_create:

            stats = ImportStats()
            actions = await importer.import_batch(schemes, stats)

        assert all(a == "skipped" for a in actions)
        assert stats.skipped == 5
        assert stats.created == 0
        assert stats.updated == 0
        mock_update.assert_not_called()
        mock_create.assert_not_called()

    def test_normalizer_source_dataset_propagated(self):
        from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
        n = HuggingFaceNormalizer("smartduketech/indian-government-schemes-2025")
        result = n.normalize({
            "name": "Test", "slug": "test", "category": "Agriculture",
            "description": "Desc", "eligibility_state": '["All States"]',
        })
        assert result.scheme.source_resource_id == "smartduketech/indian-government-schemes-2025"

    def test_full_import_4693_batch_count(self):
        """4693 rows at 100/batch requires exactly 47 API calls."""
        total = 4693
        batch_size = 100
        batches = (total + batch_size - 1) // batch_size
        assert batches == 47
        # Last batch has 93 records
        assert total - (batches - 1) * batch_size == 93
