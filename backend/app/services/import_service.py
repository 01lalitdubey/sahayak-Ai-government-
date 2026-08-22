"""
Government Import Service — Sahayak AI
=========================================
Orchestrates the full pipeline:
  DataGovClient → Normalizer → SchemeImporter → ImportReport
"""
from __future__ import annotations
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.government_data.clients.data_gov_client import DataGovClient
from app.government_data.clients.huggingface_client import HuggingFaceClient
from app.government_data.config import govt_settings
from app.government_data.importers.import_report import build_report
from app.government_data.importers.import_statistics import ImportStats
from app.government_data.importers.scheme_importer import SchemeImporter
from app.government_data.logger import GovtDataLogger
from app.government_data.normalizers.data_gov_normalizer import DataGovNormalizer
from app.government_data.normalizers.huggingface_normalizer import HuggingFaceNormalizer
from app.government_data.types import ImportMode, ImportStatus
from app.schemas.import_schema import (
    ImportReport, PreviewRecord, PreviewResult, RecordOutcome,
)

_logger = GovtDataLogger("import_service")

# In-memory store for current/recent imports (Phase 7 will move to DB)
_import_history: list[ImportReport] = []
_current_import: ImportReport | None = None


class GovernmentImportService:

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Main import entry point ───────────────────────────────────────────

    async def run_import(
        self,
        resource_id: str,
        mode: ImportMode = ImportMode.MANUAL,
        max_records: int | None = None,
        dry_run: bool = False,
    ) -> ImportReport:
        global _current_import

        started_at = datetime.now(tz=timezone.utc)
        stats = ImportStats()
        outcomes: list[RecordOutcome] = []
        batch_size = govt_settings.GOVT_DEFAULT_BATCH_SIZE

        _logger.import_started(resource_id, mode.value)

        status = ImportStatus.RUNNING
        _current_import = build_report(resource_id, mode, stats, status, started_at, dry_run=dry_run)

        try:
            # Auto-detect provider: HuggingFace paths contain "/"
            is_hf = "/" in resource_id

            if is_hf:
                normalizer = HuggingFaceNormalizer(source_dataset=resource_id)
                client_cls = HuggingFaceClient
            else:
                normalizer = DataGovNormalizer(source_resource_id=resource_id)
                client_cls = DataGovClient

            importer = SchemeImporter(self._db)

            async with client_cls(govt_settings) as client:
                offset = 0
                limit = min(batch_size, max_records or batch_size)
                total_available = None

                while True:
                    if is_hf:
                        response = await client.get_dataset(
                            offset=offset,
                            length=min(limit, HuggingFaceClient.MAX_LENGTH),
                        )
                    else:
                        response = await client.get_dataset(
                            resource_id, offset=offset, limit=limit
                        )

                    if total_available is None and response.pagination:
                        total_available = response.pagination.total
                        _logger.info("Total available records: %d", total_available)

                    if not response.records:
                        break

                    stats.downloaded += len(response.records)

                    # Normalize batch
                    batch_result = normalizer.normalize_batch(response.records)
                    valid_schemes = batch_result.successful
                    stats.warnings.extend(
                        w for r in batch_result.results for w in r.warnings
                    )

                    # Import batch
                    actions = await importer.import_batch(valid_schemes, stats, dry_run=dry_run)

                    for ns, action in zip(valid_schemes, actions):
                        outcomes.append(RecordOutcome(
                            action=action,
                            scheme_code=ns.scheme_code,
                            scheme_name=ns.name,
                        ))

                    # Check if we've fetched all
                    offset += len(response.records)
                    if max_records and stats.downloaded >= max_records:
                        break
                    if response.pagination and not response.pagination.has_more:
                        break

            status = (
                ImportStatus.SUCCESS if stats.failed == 0
                else ImportStatus.PARTIAL
            )

        except Exception as exc:
            _logger.error("Import failed: %s", exc)
            stats.errors.append(str(exc))
            status = ImportStatus.FAILED

        report = build_report(resource_id, mode, stats, status, started_at, outcomes, dry_run=dry_run)
        _import_history.append(report)
        _current_import = None

        _logger.import_finished(
            resource_id,
            inserted=stats.created,
            updated=stats.updated,
            failed=stats.failed,
        )
        return report

    # ── Preview ───────────────────────────────────────────────────────────

    async def preview(self, resource_id: str, limit: int = 20) -> PreviewResult:
        """Fetch, normalize, and check duplicates — without writing anything."""
        from app.government_data.importers.duplicate_detector import DuplicateDetector
        from app.repositories.scheme_repository import SchemeRepository

        is_hf = "/" in resource_id
        if is_hf:
            from app.government_data.clients.huggingface_client import HuggingFaceClient
            normalizer = HuggingFaceNormalizer(source_dataset=resource_id)
            client_cls = HuggingFaceClient
        else:
            from app.government_data.clients.data_gov_client import DataGovClient
            normalizer = DataGovNormalizer(source_resource_id=resource_id)
            client_cls = DataGovClient

        repo = SchemeRepository(self._db)
        detector = DuplicateDetector(repo)
        preview_records: list[PreviewRecord] = []
        to_create = to_update = to_skip = 0

        async with client_cls(govt_settings) as client:
            if is_hf:
                response = await client.get_dataset(offset=0, length=min(limit, 100))
            else:
                response = await client.get_dataset(resource_id, offset=0, limit=limit)

        batch = normalizer.normalize_batch(response.records)

        for result in batch.results:
            if not result.success or not result.scheme:
                preview_records.append(PreviewRecord(
                    action="skip",
                    scheme_code=None,
                    name=None,
                    category=None,
                    state=None,
                    validation_errors=[e.reason for e in result.errors],
                    warnings=result.warnings,
                ))
                to_skip += 1
                continue

            ns = result.scheme
            existing = await detector.find_existing(ns)

            if existing:
                changed = await detector.is_changed(ns, existing)
                action = "update" if changed else "skip"
                if changed:
                    to_update += 1
                else:
                    to_skip += 1
            else:
                action = "create"
                to_create += 1

            preview_records.append(PreviewRecord(
                action=action,
                scheme_code=ns.scheme_code,
                name=ns.name,
                category=ns.category,
                state=ns.state,
                validation_errors=[e.reason for e in result.errors],
                warnings=result.warnings,
                mapped_fields=result.mapped_fields,
                ignored_fields=result.ignored_fields,
            ))

        return PreviewResult(
            resource_id=resource_id,
            total_fetched=len(response.records),
            to_create=to_create,
            to_update=to_update,
            to_skip=to_skip,
            records=preview_records,
        )

    # ── Status / history ──────────────────────────────────────────────────

    @staticmethod
    def get_status() -> dict[str, Any]:
        return {
            "is_running": _current_import is not None,
            "current_import": _current_import,
        }

    @staticmethod
    def get_history() -> list[ImportReport]:
        return list(reversed(_import_history[-50:]))  # last 50

    @staticmethod
    def get_report(import_id: str) -> ImportReport | None:
        return next((r for r in _import_history if r.import_id == import_id), None)
