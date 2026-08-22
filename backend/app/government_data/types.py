"""
Government Data Types — Sahayak AI
=====================================
Enums and typed aliases for the Government Data module.
Designed to be future-proof — add new values without breaking existing code.
"""

import enum


class DataSource(str, enum.Enum):
    """
    Origin of government scheme data.
    Used to track provenance and apply source-specific parsing logic.
    """
    DATA_GOV = "data_gov"          # data.gov.in — primary open data portal
    MINISTRY = "ministry"          # Direct Ministry / Department APIs
    STATE = "state"                # State Government portals
    CSV = "csv"                    # Manually uploaded CSV file
    JSON = "json"                  # Manually uploaded JSON file
    XML = "xml"                    # Manually uploaded XML file
    PDF = "pdf"                    # PDF document (extracted text)
    MANUAL = "manual"              # Human-entered via admin panel


class ImportStatus(str, enum.Enum):
    """
    Lifecycle state of a data import job.
    Stored in the database to allow monitoring and resumption.
    """
    PENDING = "pending"        # Queued but not yet started
    RUNNING = "running"        # Actively being processed
    SUCCESS = "success"        # Completed without errors
    PARTIAL = "partial"        # Completed with some record-level errors
    FAILED = "failed"          # Aborted due to fatal error
    CANCELLED = "cancelled"    # Manually stopped by admin


class ImportMode(str, enum.Enum):
    """
    Strategy for a data import operation.
    """
    FULL = "full"                  # Replace all existing data from this source
    INCREMENTAL = "incremental"    # Add only new/changed records
    MANUAL = "manual"              # Admin-triggered one-off import


class DataFormat(str, enum.Enum):
    """
    Wire format of the incoming data payload.
    """
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    PDF = "pdf"


class ProviderType(str, enum.Enum):
    """
    Category of government data provider.
    Used to select the appropriate parser and authentication strategy.
    """
    DATA_GOV = "data_gov"
    MINISTRY = "ministry"
    STATE_PORTAL = "state_portal"
    MANUAL = "manual"


class AuthType(str, enum.Enum):
    """
    Authentication mechanism used by a provider.
    """
    API_KEY = "api_key"
    OAUTH2 = "oauth2"           # Future
    BEARER_TOKEN = "bearer"     # Future
    NONE = "none"               # Public endpoints
