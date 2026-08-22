"""
Base Normalizer — Sahayak AI
==============================
Abstract base class for all provider-specific normalizers.
Defines the normalization contract: validate → transform → map → result.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.government_data.normalizers.schemas import (
    BatchNormalizationResult,
    BatchNormalizationStats,
    NormalizationResult,
    NormalizedScheme,
)
from app.government_data.logger import GovtDataLogger


class BaseNormalizer(ABC):
    """
    Abstract base for all government data normalizers.

    Subclass and implement normalize() for each provider.
    normalize_batch() is provided and reuses normalize().

    Usage:
        normalizer = DataGovNormalizer()
        result = normalizer.normalize(raw_record)
        if result.success:
            scheme = result.scheme
    """

    PROVIDER_NAME: str = "base"

    def __init__(self) -> None:
        self._logger = GovtDataLogger(f"normalizer.{self.PROVIDER_NAME}")

    @abstractmethod
    def normalize(self, record: dict[str, Any]) -> NormalizationResult:
        """
        Normalize one raw API record into a NormalizedScheme.
        Never raises — always returns a NormalizationResult.
        """
        ...

    def normalize_batch(
        self, records: list[dict[str, Any]]
    ) -> BatchNormalizationResult:
        """
        Normalize a list of raw records.
        Each record is processed independently — failures don't stop the batch.

        Returns BatchNormalizationResult with per-record results + aggregate stats.
        """
        self._logger.import_started(self.PROVIDER_NAME, "batch")

        results: list[NormalizationResult] = []
        warnings_count = 0
        missing_fields_count = 0

        for i, record in enumerate(records):
            try:
                result = self.normalize(record)
                results.append(result)
                warnings_count += len(result.warnings)
                if not result.success:
                    missing_fields_count += len(result.errors)
            except Exception as exc:
                # Catch-all so one bad record never stops the batch
                self._logger.error(
                    "Unexpected error normalizing record %d: %s", i, exc
                )
                results.append(NormalizationResult(
                    success=False,
                    errors=[],
                    warnings=[f"Unexpected error: {type(exc).__name__}: {exc}"],
                ))

        normalized = sum(1 for r in results if r.success)
        failed = len(results) - normalized

        stats = BatchNormalizationStats(
            total_records=len(records),
            normalized_records=normalized,
            failed_records=failed,
            warnings_count=warnings_count,
            missing_fields_count=missing_fields_count,
        )

        self._logger.import_finished(
            self.PROVIDER_NAME,
            inserted=normalized,
            updated=0,
            failed=failed,
        )

        return BatchNormalizationResult(results=results, stats=stats)
