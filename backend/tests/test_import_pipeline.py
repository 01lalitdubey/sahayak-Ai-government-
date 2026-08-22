"""
Government Data Import Pipeline Tests — Sahayak AI Phase 6.4
==============================================================
All HTTP and DB calls are mocked. No real API or PostgreSQL needed.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.government_data.types import ImportMode, ImportStatus


# ─── Helpers ──────────────────────────────────────────────────────────────

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
        source_provider="data_gov",
    )
    defaults.update(kw)
    return NormalizedScheme(**defaults)


def _mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


# ─── ImportStats ──────────────────────────────────────────────────────────

def test_import_stats_defaults():
    from app.government_data.importers.import_statistics import ImportStats
    s = ImportStats()
    assert s.downloaded == 0
    assert s.created == 0
    assert s.failed == 0
    assert isinstance(s.duration_ms(), float)


def test_import_stats_to_dict():
    from app.government_data.importers.import_statistics import ImportStats
    s = ImportStats(created=10, updated=5, failed=1)
    d = s.to_dict()
    assert d["created"] == 10
    assert d["updated"] == 5
    assert d["failed"] == 1
    assert "duration_ms" in d


# ─── ImportReport ─────────────────────────────────────────────────────────

def test_build_report():
    from app.government_data.importers.import_report import build_report
    from app.government_data.importers.import_statistics import ImportStats
    stats = ImportStats(created=5, updated=2, failed=0)
    started = datetime.now(tz=timezone.utc)
    report = build_report("res-123", ImportMode.MANUAL, stats, ImportStatus.SUCCESS, started)
    assert report.resource_id == "res-123"
    assert report.status == "success"
    assert report.statistics.created == 5
    assert report.import_id is not None
    assert report.finished_at is not None


def test_build_report_dry_run():
    from app.government_data.importers.import_report import build_report
    from app.government_data.importers.import_statistics import ImportStats
    stats = ImportStats()
    report = build_report("r", ImportMode.MANUAL, stats, ImportStatus.SUCCESS,
                          datetime.now(tz=timezone.utc), dry_run=True)
    assert report.dry_run is True


# ─── DuplicateDetector ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_duplicate_detector_finds_by_code():
    from app.government_data.importers.duplicate_detector import DuplicateDetector
    mock_repo = AsyncMock()
    existing = MagicMock()
    mock_repo.get_by_code = AsyncMock(return_value=existing)
    mock_repo.get_by_name = AsyncMock(return_value=None)

    detector = DuplicateDetector(mock_repo)
    ns = _norm_scheme(scheme_code="PM-KISAN-2024")
    result = await detector.find_existing(ns)
    assert result is existing
    mock_repo.get_by_code.assert_called_once_with("PM-KISAN-2024")


@pytest.mark.asyncio
async def test_duplicate_detector_finds_by_name():
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
async def test_duplicate_detector_not_found():
    from app.government_data.importers.duplicate_detector import DuplicateDetector
    mock_repo = AsyncMock()
    mock_repo.get_by_code = AsyncMock(return_value=None)
    mock_repo.get_by_name = AsyncMock(return_value=None)

    detector = DuplicateDetector(mock_repo)
    result = await detector.find_existing(_norm_scheme())
    assert result is None


@pytest.mark.asyncio
async def test_duplicate_detector_is_changed_true():
    from app.government_data.importers.duplicate_detector import DuplicateDetector
    mock_repo = AsyncMock()
    detector = DuplicateDetector(mock_repo)

    ns = _norm_scheme(name="Updated Name")
    existing = MagicMock()
    existing.name = "Old Name"
    existing.full_description = None
    existing.benefits = None
    existing.ministry = None
    existing.category = None
    existing.state = None
    existing.official_url = None
    existing.is_active = True

    changed = await detector.is_changed(ns, existing)
    assert changed is True


@pytest.mark.asyncio
async def test_duplicate_detector_is_changed_false():
    from app.government_data.importers.duplicate_detector import DuplicateDetector
    mock_repo = AsyncMock()
    detector = DuplicateDetector(mock_repo)

    ns = _norm_scheme(name="Same Name", category="agriculture")
    existing = MagicMock()
    existing.name = "Same Name"
    existing.full_description = None
    existing.benefits = None
    existing.ministry = None
    existing.category = "agriculture"
    existing.state = "Maharashtra"
    existing.official_url = None
    existing.is_active = True

    changed = await detector.is_changed(ns, existing)
    assert changed is False


# ─── SchemeImporter ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scheme_importer_creates_new():
    from app.government_data.importers.scheme_importer import SchemeImporter
    from app.government_data.importers.import_statistics import ImportStats

    db = _mock_db()
    importer = SchemeImporter(db)

    with patch.object(importer._detector, "find_existing", return_value=None), \
         patch.object(importer._repo, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = MagicMock()
        stats = ImportStats()
        action = await importer.import_scheme(_norm_scheme(), stats)

    assert action == "created"
    assert stats.created == 1
    assert stats.updated == 0
    assert stats.failed == 0


@pytest.mark.asyncio
async def test_scheme_importer_updates_existing():
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
        action = await importer.import_scheme(_norm_scheme(), stats)

    assert action == "updated"
    assert stats.updated == 1
    assert stats.duplicates == 1


@pytest.mark.asyncio
async def test_scheme_importer_skips_unchanged():
    from app.government_data.importers.scheme_importer import SchemeImporter
    from app.government_data.importers.import_statistics import ImportStats

    db = _mock_db()
    importer = SchemeImporter(db)
    existing = MagicMock()

    with patch.object(importer._detector, "find_existing", return_value=existing), \
         patch.object(importer._detector, "is_changed", return_value=False):
        stats = ImportStats()
        action = await importer.import_scheme(_norm_scheme(), stats)

    assert action == "skipped"
    assert stats.skipped == 1


@pytest.mark.asyncio
async def test_scheme_importer_handles_error():
    from app.government_data.importers.scheme_importer import SchemeImporter
    from app.government_data.importers.import_statistics import ImportStats

    db = _mock_db()
    importer = SchemeImporter(db)

    with patch.object(importer._detector, "find_existing", side_effect=Exception("DB error")):
        stats = ImportStats()
        action = await importer.import_scheme(_norm_scheme(), stats)

    assert action == "failed"
    assert stats.failed == 1
    assert len(stats.errors) == 1


@pytest.mark.asyncio
async def test_scheme_importer_dry_run_no_db_write():
    from app.government_data.importers.scheme_importer import SchemeImporter
    from app.government_data.importers.import_statistics import ImportStats

    db = _mock_db()
    importer = SchemeImporter(db)

    with patch.object(importer._detector, "find_existing", return_value=None), \
         patch.object(importer._repo, "create", new_callable=AsyncMock) as mock_create:
        stats = ImportStats()
        action = await importer.import_scheme(_norm_scheme(), stats, dry_run=True)

    assert action == "created"
    mock_create.assert_not_called()  # dry_run skips DB write


@pytest.mark.asyncio
async def test_scheme_importer_batch_success():
    from app.government_data.importers.scheme_importer import SchemeImporter
    from app.government_data.importers.import_statistics import ImportStats

    db = _mock_db()
    importer = SchemeImporter(db)
    schemes = [_norm_scheme(scheme_code=f"S-{i:03d}", name=f"Scheme {i}") for i in range(5)]

    with patch.object(importer, "import_scheme", new_callable=AsyncMock) as mock_import:
        mock_import.return_value = "created"
        stats = ImportStats()
        actions = await importer.import_batch(schemes, stats)

    assert len(actions) == 5
    assert all(a == "created" for a in actions)
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_scheme_importer_batch_rollback_on_error():
    from app.government_data.importers.scheme_importer import SchemeImporter
    from app.government_data.importers.import_statistics import ImportStats

    db = _mock_db()
    importer = SchemeImporter(db)
    schemes = [_norm_scheme() for _ in range(3)]

    with patch.object(importer, "import_scheme", side_effect=Exception("TX error")):
        stats = ImportStats()
        actions = await importer.import_batch(schemes, stats)

    db.rollback.assert_called_once()
    assert stats.errors


@pytest.mark.asyncio
async def test_scheme_importer_batch_dry_run_no_commit():
    from app.government_data.importers.scheme_importer import SchemeImporter
    from app.government_data.importers.import_statistics import ImportStats

    db = _mock_db()
    importer = SchemeImporter(db)
    schemes = [_norm_scheme()]

    with patch.object(importer, "import_scheme", new_callable=AsyncMock) as mock_import:
        mock_import.return_value = "created"
        stats = ImportStats()
        await importer.import_batch(schemes, stats, dry_run=True)

    db.commit.assert_not_called()


# ─── ImportService ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_import_service_run_import_success():
    from app.services.import_service import GovernmentImportService
    from app.government_data.clients.response_models import (
        GovernmentAPIResponse, GovernmentPagination
    )
    from app.government_data.normalizers.schemas import (
        BatchNormalizationResult, BatchNormalizationStats, NormalizationResult
    )

    db = _mock_db()
    svc = GovernmentImportService(db)

    mock_response = GovernmentAPIResponse(
        provider="data_gov",
        resource_id="res-123",
        status="ok",
        records=[{"scheme_name": f"Scheme {i}", "state": "Maharashtra"} for i in range(5)],
        pagination=GovernmentPagination(total=5, count=5, limit=100, offset=0),
    )
    norm_results = [
        NormalizationResult(success=True, scheme=_norm_scheme(scheme_code=f"S-{i}", name=f"Scheme {i}"))
        for i in range(5)
    ]
    batch_result = BatchNormalizationResult(
        results=norm_results,
        stats=BatchNormalizationStats(total_records=5, normalized_records=5, failed_records=0,
                                      warnings_count=0, missing_fields_count=0),
    )

    with patch("app.services.import_service.DataGovClient") as MockClient, \
         patch("app.services.import_service.DataGovNormalizer") as MockNorm, \
         patch("app.services.import_service.SchemeImporter") as MockImporter:

        instance = MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value.get_dataset = AsyncMock(return_value=mock_response)

        MockNorm.return_value.normalize_batch = MagicMock(return_value=batch_result)
        MockImporter.return_value.import_batch = AsyncMock(return_value=["created"] * 5)

        report = await svc.run_import("res-123", ImportMode.MANUAL)

    assert report.statistics.downloaded == 5
    assert report.resource_id == "res-123"


def test_import_service_get_status_not_running():
    from app.services.import_service import GovernmentImportService
    import app.services.import_service as svc_module
    svc_module._current_import = None
    s = GovernmentImportService.get_status()
    assert s["is_running"] is False


def test_import_service_get_history():
    from app.services.import_service import GovernmentImportService
    history = GovernmentImportService.get_history()
    assert isinstance(history, list)


def test_import_service_get_report_missing():
    from app.services.import_service import GovernmentImportService
    result = GovernmentImportService.get_report("nonexistent-id")
    assert result is None


# ─── API endpoint security ────────────────────────────────────────────────

def _client():
    from app.main import create_application
    from fastapi.testclient import TestClient
    return TestClient(create_application(), raise_server_exceptions=False)


def test_import_endpoint_requires_admin():
    c = _client()
    resp = c.post("/api/v1/admin/government/import", json={"resource_id": "test"})
    assert resp.status_code == 401


def test_preview_endpoint_requires_admin():
    c = _client()
    resp = c.post("/api/v1/admin/government/import/preview", json={"resource_id": "test"})
    assert resp.status_code == 401


def test_status_endpoint_requires_admin():
    c = _client()
    resp = c.get("/api/v1/admin/government/import/status")
    assert resp.status_code == 401


def test_history_endpoint_requires_admin():
    c = _client()
    resp = c.get("/api/v1/admin/government/import/history")
    assert resp.status_code == 401


def test_import_routes_in_openapi():
    c = _client()
    paths = c.get("/openapi.json").json()["paths"]
    assert "/api/v1/admin/government/import" in paths
    assert "/api/v1/admin/government/import/preview" in paths
    assert "/api/v1/admin/government/import/status" in paths
    assert "/api/v1/admin/government/import/history" in paths


# ─── Schema tests ─────────────────────────────────────────────────────────

def test_import_request_schema():
    from app.schemas.import_schema import ImportRequest
    r = ImportRequest(resource_id="abc-123")
    assert r.resource_id == "abc-123"
    assert r.mode == ImportMode.MANUAL
    assert r.dry_run is False


def test_import_statistics_schema():
    from app.schemas.import_schema import ImportStatistics
    s = ImportStatistics(created=10, updated=5, failed=0, duration_ms=500.0)
    assert s.created == 10


def test_preview_request_default_limit():
    from app.schemas.import_schema import PreviewRequest
    r = PreviewRequest(resource_id="test")
    assert r.limit == 20
