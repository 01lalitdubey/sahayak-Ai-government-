"""
Scheme Importer — Sahayak AI
================================
Writes NormalizedScheme objects into the schemes table.
Uses upsert strategy: create new, update changed, skip unchanged.
Processes in configurable batches with per-batch transactions.
"""
from __future__ import annotations
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.government_data.importers.base_importer import BaseImporter
from app.government_data.importers.duplicate_detector import DuplicateDetector
from app.government_data.importers.import_statistics import ImportStats
from app.government_data.normalizers.schemas import NormalizedScheme
from app.models.scheme import Scheme
from app.models.enums import SchemeCategoryEnum, SchemeTypeEnum, ApplicationModeEnum
from app.repositories.scheme_repository import SchemeRepository


def _to_orm_dict(ns: NormalizedScheme) -> dict[str, Any]:
    """Map NormalizedScheme fields to Scheme ORM column names."""
    def _cat(v: str | None):
        if not v:
            return None
        try:
            return SchemeCategoryEnum(v.lower())
        except ValueError:
            return None

    def _type(v: str) -> SchemeTypeEnum:
        try:
            return SchemeTypeEnum(v.lower())
        except ValueError:
            return SchemeTypeEnum.CENTRAL

    def _mode(v: str) -> ApplicationModeEnum:
        try:
            return ApplicationModeEnum(v.lower())
        except ValueError:
            return ApplicationModeEnum.ONLINE

    return {
        "scheme_code": ns.scheme_code or f"AUTO-{str(uuid.uuid4())[:8].upper()}",
        "name": ns.name or "Unnamed Scheme",
        "short_description": ns.short_description,
        "full_description": ns.full_description,
        "benefits": ns.benefits,
        "scheme_type": _type(ns.scheme_type),
        "category": _cat(ns.category),
        "ministry": ns.ministry,
        "department": ns.department,
        "state": ns.state,
        "district": ns.district,
        "application_mode": _mode(ns.application_mode),
        "application_start_date": ns.application_start_date,
        "application_end_date": ns.application_end_date,
        "official_url": ns.official_url,
        "official_pdf_url": ns.official_pdf_url,
        "contact_email": ns.contact_email,
        "contact_phone": ns.contact_phone,
        "is_active": ns.is_active,
        "is_featured": ns.is_featured,
    }


class SchemeImporter(BaseImporter):
    PROVIDER_NAME = "scheme_importer"

    def __init__(self, db: AsyncSession) -> None:
        super().__init__()
        self._db = db
        self._repo = SchemeRepository(db)
        self._detector = DuplicateDetector(self._repo)

    async def import_scheme(
        self,
        ns: NormalizedScheme,
        stats: ImportStats,
        dry_run: bool = False,
    ) -> str:
        """
        Upsert one NormalizedScheme.
        Returns: "created" | "updated" | "skipped" | "failed"
        """
        try:
            existing = await self._detector.find_existing(ns)

            if existing:
                stats.duplicates += 1
                if not await self._detector.is_changed(ns, existing):
                    stats.skipped += 1
                    return "skipped"

                # Update changed fields
                if not dry_run:
                    update_data = _to_orm_dict(ns)
                    await self._repo.update(existing, update_data)
                stats.updated += 1
                self._logger.info("Updated scheme: %s", ns.scheme_code or ns.name)
                return "updated"

            # Create new scheme
            if not dry_run:
                orm_dict = _to_orm_dict(ns)
                new_scheme = Scheme(**orm_dict)
                await self._repo.create(new_scheme)
            stats.created += 1
            self._logger.info("Created scheme: %s", ns.scheme_code or ns.name)
            return "created"

        except Exception as exc:
            stats.failed += 1
            stats.errors.append(f"Failed {ns.name or 'unknown'}: {exc}")
            self._logger.error("Import error for %s: %s", ns.name, exc)
            return "failed"

    async def import_batch(
        self,
        schemes: list[NormalizedScheme],
        stats: ImportStats,
        dry_run: bool = False,
    ) -> list[str]:
        """
        Import a batch with a single transaction.
        On batch-level exception, rolls back and marks all as failed.
        """
        actions: list[str] = []
        self._logger.info("Batch started — size=%d dry_run=%s", len(schemes), dry_run)

        try:
            for ns in schemes:
                action = await self.import_scheme(ns, stats, dry_run=dry_run)
                actions.append(action)

            if not dry_run:
                await self._db.commit()

            self._logger.info(
                "Batch finished — created=%d updated=%d skipped=%d failed=%d",
                actions.count("created"), actions.count("updated"),
                actions.count("skipped"), actions.count("failed"),
            )
        except Exception as exc:
            await self._db.rollback()
            fail_count = len(schemes) - len(actions)
            for _ in range(fail_count):
                stats.failed += 1
                actions.append("failed")
            stats.errors.append(f"Batch rollback: {exc}")
            self._logger.error("Batch rollback: %s", exc)

        return actions
