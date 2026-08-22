"""
Government Data Configuration — Sahayak AI
============================================
Pydantic v2 Settings for the Government Data module.
All values are loaded from environment variables / .env file.
Validated at module load time — startup fails fast on bad config.

Usage:
    from app.government_data.config import govt_settings
    print(govt_settings.DATA_GOV_BASE_URL)
"""

import re
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.government_data.constants import (
    DEFAULT_TIMEOUT,
    DEFAULT_RETRY_COUNT,
    DEFAULT_BACKOFF,
    DEFAULT_RATE_LIMIT,
    DEFAULT_PAGE_SIZE,
    DEFAULT_BATCH_SIZE,
    DEFAULT_SYNC_INTERVAL_HOURS,
    DATA_GOV_BASE_URL,
)
from app.government_data.exceptions import ConfigurationException

_URL_RE = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")


class GovtDataSettings(BaseSettings):
    """
    Configuration for the Government Data integration module.
    All fields can be overridden via environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── data.gov.in ───────────────────────────────────────────────────────
    DATA_GOV_API_KEY: str = Field(default="")
    DATA_GOV_BASE_URL: str = Field(default=DATA_GOV_BASE_URL)

    # ── HuggingFace ───────────────────────────────────────────────────────
    HF_TOKEN: str = Field(
        default="",
        description="Optional HuggingFace token for private datasets",
    )
    HF_DATASET: str = Field(
        default="smartduketech/indian-government-schemes-2025",
        description="HuggingFace dataset repository path",
    )
    HF_CONFIG: str = Field(default="default")
    HF_SPLIT: str = Field(default="train")

    # ── HTTP client ───────────────────────────────────────────────────────
    GOVT_REQUEST_TIMEOUT: int = Field(
        default=DEFAULT_TIMEOUT,
        ge=1,
        le=300,
        description="HTTP request timeout in seconds",
    )
    GOVT_MAX_RETRIES: int = Field(
        default=DEFAULT_RETRY_COUNT,
        ge=0,
        le=10,
        description="Maximum retry attempts per request",
    )
    GOVT_BACKOFF_FACTOR: float = Field(
        default=DEFAULT_BACKOFF,
        ge=0.0,
        le=60.0,
        description="Exponential backoff base in seconds",
    )

    # ── Rate limiting ─────────────────────────────────────────────────────
    GOVT_RATE_LIMIT_PER_MINUTE: int = Field(
        default=DEFAULT_RATE_LIMIT,
        ge=1,
        le=10000,
        description="Maximum requests per minute to government APIs",
    )

    # ── Feature flags ─────────────────────────────────────────────────────
    GOVT_ENABLE_SYNC: bool = Field(
        default=False,
        description="Enable automatic periodic scheme data sync",
    )
    GOVT_ENABLE_CACHE: bool = Field(
        default=True,
        description="Cache API responses to reduce rate limit consumption",
    )

    # ── Logging ───────────────────────────────────────────────────────────
    GOVT_LOG_LEVEL: str = Field(
        default="INFO",
        description="Log level for the Government Data module",
    )

    # ── Pagination & batching ─────────────────────────────────────────────
    GOVT_DEFAULT_PAGE_SIZE: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=1000,
        description="Records per page when fetching from APIs",
    )
    GOVT_DEFAULT_BATCH_SIZE: int = Field(
        default=DEFAULT_BATCH_SIZE,
        ge=1,
        le=5000,
        description="Records per database batch insert",
    )

    # ── Scheduler ─────────────────────────────────────────────────────────
    GOVT_SYNC_INTERVAL_HOURS: int = Field(
        default=DEFAULT_SYNC_INTERVAL_HOURS,
        ge=1,
        le=168,   # max 1 week
        description="Hours between automatic full syncs",
    )

    # ── Validators ────────────────────────────────────────────────────────

    @field_validator("DATA_GOV_BASE_URL")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        if v and not _URL_RE.match(v):
            raise ValueError(f"DATA_GOV_BASE_URL must be a valid http/https URL, got: {v!r}")
        return v.rstrip("/")

    @field_validator("GOVT_LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"GOVT_LOG_LEVEL must be one of {allowed}")
        return v.upper()

    # ── Derived properties ────────────────────────────────────────────────

    @property
    def has_data_gov_key(self) -> bool:
        """True if a data.gov.in API key is configured."""
        return bool(self.DATA_GOV_API_KEY.strip())

    @property
    def sync_enabled(self) -> bool:
        """True when both ENABLE_SYNC is on and a data.gov key is present."""
        return self.GOVT_ENABLE_SYNC and self.has_data_gov_key

    def validate_for_sync(self) -> None:
        """
        Raise ConfigurationException if syncing is enabled but required
        credentials are missing. Called before starting the scheduler.
        """
        if self.GOVT_ENABLE_SYNC and not self.has_data_gov_key:
            raise ConfigurationException(
                message="GOVT_ENABLE_SYNC is True but DATA_GOV_API_KEY is not set.",
                error_code="GOVT_CONFIG_ERROR",
                details={"missing_field": "DATA_GOV_API_KEY"},
            )


@lru_cache(maxsize=1)
def get_govt_settings() -> GovtDataSettings:
    """
    Cached singleton for government data settings.

    Usage:
        from app.government_data.config import govt_settings
    """
    return GovtDataSettings()


# Convenience alias — import this directly
govt_settings = get_govt_settings()
