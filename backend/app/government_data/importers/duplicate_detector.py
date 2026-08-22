"""
Duplicate Detector — Sahayak AI
==================================
Checks whether a normalized scheme already exists in the database.
Returns the existing Scheme if found so callers can decide update vs skip.
"""
from __future__ import annotations
from app.government_data.normalizers.schemas import NormalizedScheme
from app.models.scheme import Scheme
from app.repositories.scheme_repository import SchemeRepository
from app.government_data.logger import GovtDataLogger

_logger = GovtDataLogger(__name__)


class DuplicateDetector:
    """
    Detection priority (first match wins):
      1. scheme_code  — globally unique
      2. name + state — unique constraint
    """

    def __init__(self, repo: SchemeRepository) -> None:
        self._repo = repo

    async def find_existing(self, ns: NormalizedScheme) -> Scheme | None:
        # 1. Code match
        if ns.scheme_code:
            existing = await self._repo.get_by_code(ns.scheme_code)
            if existing:
                _logger.debug("Duplicate by code: %s", ns.scheme_code)
                return existing
        # 2. Name + state match
        if ns.name:
            existing = await self._repo.get_by_name(ns.name, ns.state)
            if existing:
                _logger.debug("Duplicate by name+state: %s / %s", ns.name, ns.state)
                return existing
        return None

    async def is_changed(self, ns: NormalizedScheme, existing: Scheme) -> bool:
        """Return True if any meaningful field differs — avoids no-op updates."""
        checks = [
            (ns.name, existing.name),
            (ns.full_description, existing.full_description),
            (ns.benefits, existing.benefits),
            (ns.ministry, existing.ministry),
            (ns.category, existing.category),
            (ns.state, existing.state),
            (ns.official_url, existing.official_url),
            (ns.is_active, existing.is_active),
        ]
        return any(a != b for a, b in checks)
