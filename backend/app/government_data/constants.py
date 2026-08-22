"""
Government Data Constants — Sahayak AI
========================================
All module-level constants are defined here.
Never import raw literals from other modules — import from here.
"""

from typing import Final


# ── Timeout & retry defaults ──────────────────────────────────────────────
DEFAULT_TIMEOUT: Final[int] = 30          # seconds per HTTP request
DEFAULT_RETRY_COUNT: Final[int] = 3       # maximum retry attempts
DEFAULT_BACKOFF: Final[float] = 2.0       # exponential backoff base (seconds)
DEFAULT_RATE_LIMIT: Final[int] = 60       # requests per minute per provider

# ── Pagination defaults ───────────────────────────────────────────────────
DEFAULT_PAGE_SIZE: Final[int] = 100       # records per API page
DEFAULT_BATCH_SIZE: Final[int] = 500      # records per DB insert batch
MAX_PAGE_SIZE: Final[int] = 1000          # safety cap on page size

# ── Sync defaults ─────────────────────────────────────────────────────────
DEFAULT_SYNC_INTERVAL_HOURS: Final[int] = 24   # full sync every 24 hours

# ── Supported data formats ────────────────────────────────────────────────
SUPPORTED_FORMATS: Final[frozenset[str]] = frozenset({"json", "csv", "xml", "pdf"})

# ── Supported data providers ──────────────────────────────────────────────
SUPPORTED_PROVIDERS: Final[frozenset[str]] = frozenset({
    "data_gov",      # data.gov.in — Indian Open Government Data
    "ministry",      # Central Ministry APIs
    "state_portal",  # State Government Portals
    "manual",        # Manually uploaded datasets
})

# ── data.gov.in specifics ─────────────────────────────────────────────────
DATA_GOV_BASE_URL: Final[str] = "https://api.data.gov.in/resource"
DATA_GOV_CATALOG_URL: Final[str] = "https://api.data.gov.in/catalog"
DATA_GOV_API_KEY_HEADER: Final[str] = "api-key"

# ── HuggingFace Datasets Server ───────────────────────────────────────────
HF_ROWS_BASE_URL: Final[str] = "https://datasets-server.huggingface.co/rows"
HF_METADATA_BASE_URL: Final[str] = "https://huggingface.co/api/datasets"
HF_DEFAULT_DATASET: Final[str] = "smartduketech/indian-government-schemes-2025"
HF_DEFAULT_CONFIG: Final[str] = "default"
HF_DEFAULT_SPLIT: Final[str] = "train"
HF_MAX_LENGTH: Final[int] = 100   # max records per HF Rows API request
HF_TOKEN_HEADER: Final[str] = "Authorization"

# ── HTTP headers ──────────────────────────────────────────────────────────
ACCEPT_JSON: Final[str] = "application/json"
ACCEPT_CSV: Final[str] = "text/csv"
ACCEPT_XML: Final[str] = "application/xml"

# ── Logging prefixes (for structured log filtering) ───────────────────────
LOG_PREFIX_IMPORT: Final[str] = "[IMPORT]"
LOG_PREFIX_SYNC: Final[str] = "[SYNC]"
LOG_PREFIX_AUTH: Final[str] = "[AUTH]"
LOG_PREFIX_RATE: Final[str] = "[RATE_LIMIT]"
LOG_PREFIX_RETRY: Final[str] = "[RETRY]"
LOG_PREFIX_CONFIG: Final[str] = "[CONFIG]"

# ── Masked value placeholder ──────────────────────────────────────────────
MASKED_VALUE: Final[str] = "***REDACTED***"
API_KEY_VISIBLE_CHARS: Final[int] = 4    # show last N chars of key in logs
