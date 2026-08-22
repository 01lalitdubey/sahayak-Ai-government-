"""
Government Data Logger — Sahayak AI
======================================
Dedicated logger for the Government Data module.
Provides structured, prefixed log methods so module events
are easy to filter and grep in production log aggregators.

Security rule: API keys and credentials are NEVER logged.
Use govt_logger.masked_key() before including key material.
"""

import logging
from typing import Any

from app.government_data.constants import (
    LOG_PREFIX_IMPORT,
    LOG_PREFIX_SYNC,
    LOG_PREFIX_AUTH,
    LOG_PREFIX_RATE,
    LOG_PREFIX_RETRY,
    LOG_PREFIX_CONFIG,
    MASKED_VALUE,
    API_KEY_VISIBLE_CHARS,
)

_MODULE_LOGGER_NAME = "sahayak.govt_data"


def get_govt_logger(name: str | None = None) -> logging.Logger:
    """
    Return a named child logger under the govt_data namespace.

    Usage:
        logger = get_govt_logger(__name__)
        logger.info("Sync started")
    """
    logger_name = f"{_MODULE_LOGGER_NAME}.{name}" if name else _MODULE_LOGGER_NAME
    return logging.getLogger(logger_name)


class GovtDataLogger:
    """
    Wrapper around stdlib Logger with domain-specific helpers.
    Instantiate once per module:
        logger = GovtDataLogger(__name__)
    """

    def __init__(self, name: str | None = None) -> None:
        self._log = get_govt_logger(name)

    # ── Passthrough stdlib methods ────────────────────────────────────────

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.critical(msg, *args, **kwargs)

    # ── Domain-specific helpers ───────────────────────────────────────────

    def config_loaded(self, provider: str) -> None:
        self._log.info("%s Configuration loaded for provider: %s", LOG_PREFIX_CONFIG, provider)

    def config_invalid(self, field: str, reason: str) -> None:
        self._log.error(
            "%s Invalid configuration — field=%r reason=%s",
            LOG_PREFIX_CONFIG, field, reason,
        )

    def auth_failed(self, provider: str, status_code: int | None = None) -> None:
        self._log.error(
            "%s Authentication failed — provider=%s status=%s",
            LOG_PREFIX_AUTH, provider, status_code or "unknown",
        )

    def rate_limited(self, provider: str, retry_after: int | None = None) -> None:
        self._log.warning(
            "%s Rate limit hit — provider=%s retry_after=%ss",
            LOG_PREFIX_RATE, provider, retry_after or "unknown",
        )

    def retry_scheduled(
        self, attempt: int, max_attempts: int, delay: float, reason: str
    ) -> None:
        self._log.warning(
            "%s Retry %d/%d scheduled in %.1fs — reason: %s",
            LOG_PREFIX_RETRY, attempt, max_attempts, delay, reason,
        )

    def import_started(self, source: str, mode: str) -> None:
        self._log.info(
            "%s Import started — source=%s mode=%s",
            LOG_PREFIX_IMPORT, source, mode,
        )

    def import_finished(
        self, source: str, inserted: int, updated: int, failed: int
    ) -> None:
        self._log.info(
            "%s Import finished — source=%s inserted=%d updated=%d failed=%d",
            LOG_PREFIX_IMPORT, source, inserted, updated, failed,
        )

    def import_failed(self, source: str, reason: str) -> None:
        self._log.error(
            "%s Import failed — source=%s reason=%s",
            LOG_PREFIX_IMPORT, source, reason,
        )

    def sync_started(self) -> None:
        self._log.info("%s Scheduled sync started", LOG_PREFIX_SYNC)

    def sync_finished(self, total_schemes: int) -> None:
        self._log.info(
            "%s Sync completed — total_schemes=%d",
            LOG_PREFIX_SYNC, total_schemes,
        )

    # ── Security helper ───────────────────────────────────────────────────

    @staticmethod
    def masked_key(key: str | None) -> str:
        """
        Return a safely masked version of an API key for log output.
        Example: "abc123xyz" → "***REDACTED***xyz"
        """
        if not key or len(key) <= API_KEY_VISIBLE_CHARS:
            return MASKED_VALUE
        return f"{MASKED_VALUE}{key[-API_KEY_VISIBLE_CHARS:]}"
