"""
Import Statistics — Sahayak AI
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field


@dataclass
class ImportStats:
    downloaded: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    duplicates: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    _start: float = field(default_factory=time.monotonic, repr=False)

    def duration_ms(self) -> float:
        return round((time.monotonic() - self._start) * 1000, 2)

    def to_dict(self) -> dict:
        return dict(
            downloaded=self.downloaded,
            created=self.created,
            updated=self.updated,
            skipped=self.skipped,
            failed=self.failed,
            duplicates=self.duplicates,
            duration_ms=self.duration_ms(),
        )
