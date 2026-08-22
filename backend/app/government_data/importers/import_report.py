"""
Import Report Builder — Sahayak AI
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from app.government_data.importers.import_statistics import ImportStats
from app.government_data.types import ImportMode, ImportStatus
from app.schemas.import_schema import ImportReport, ImportStatistics, RecordOutcome


def build_report(
    resource_id: str,
    mode: ImportMode,
    stats: ImportStats,
    status: ImportStatus,
    started_at: datetime,
    outcomes: list[RecordOutcome] | None = None,
    dry_run: bool = False,
) -> ImportReport:
    finished_at = datetime.now(tz=timezone.utc)
    return ImportReport(
        import_id=str(uuid.uuid4()),
        resource_id=resource_id,
        mode=mode.value,
        status=status.value,
        statistics=ImportStatistics(**stats.to_dict()),
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=stats.duration_ms(),
        warnings=stats.warnings,
        errors=stats.errors,
        outcomes=outcomes or [],
        dry_run=dry_run,
    )
