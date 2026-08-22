"""
Base Importer — Sahayak AI
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from app.government_data.normalizers.schemas import NormalizedScheme
from app.government_data.importers.import_statistics import ImportStats
from app.government_data.logger import GovtDataLogger


class BaseImporter(ABC):
    PROVIDER_NAME: str = "base"

    def __init__(self) -> None:
        self._logger = GovtDataLogger(f"importer.{self.PROVIDER_NAME}")

    @abstractmethod
    async def import_scheme(self, ns: NormalizedScheme, stats: ImportStats) -> str:
        """
        Persist one normalized scheme. Returns action string:
        "created" | "updated" | "skipped" | "failed"
        """
        ...

    @abstractmethod
    async def import_batch(
        self,
        schemes: list[NormalizedScheme],
        stats: ImportStats,
        dry_run: bool = False,
    ) -> list[str]:
        """Import a batch. Returns list of action strings."""
        ...
