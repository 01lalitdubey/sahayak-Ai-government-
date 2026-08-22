"""
Government Data Utilities — Sahayak AI
=========================================
Pure helper functions — no side effects, no DB calls, no HTTP.
Every function is independently testable.
"""

import json
import math
import re
import unicodedata
from datetime import date, datetime
from typing import Any, TypeVar
from urllib.parse import urlparse

T = TypeVar("T")

# ── String helpers ────────────────────────────────────────────────────────

def clean_string(value: Any) -> str:
    """
    Convert any value to a clean stripped string.
    Returns empty string for None, NaN-like floats, etc.
    """
    if value is None:
        return ""
    s = str(value).strip()
    # Remove common "not available" placeholders from government datasets
    if s.lower() in {"na", "n/a", "nil", "none", "-", "--", "not available", "null"}:
        return ""
    return s


def normalize_whitespace(text: str) -> str:
    """
    Replace all runs of whitespace (including tabs, newlines) with a single space.
    Also normalises Unicode whitespace characters.
    """
    if not text:
        return ""
    # Normalize Unicode to NFC form first
    normalized = unicodedata.normalize("NFC", text)
    return re.sub(r"\s+", " ", normalized).strip()


def safe_get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    Traverse a nested dict safely using a sequence of keys.
    Returns default if any key is missing or value is None.

    Example:
        safe_get({"a": {"b": 42}}, "a", "b")  → 42
        safe_get({"a": {}}, "a", "b", default="x")  → "x"
    """
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively merge override into base.
    Override values take precedence. Nested dicts are merged, not replaced.

    Example:
        deep_merge({"a": {"x": 1, "y": 2}}, {"a": {"y": 99, "z": 3}})
        → {"a": {"x": 1, "y": 99, "z": 3}}
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


# ── Date helpers ──────────────────────────────────────────────────────────

_DATE_FORMATS = [
    "%Y-%m-%d",       # ISO 8601
    "%d-%m-%Y",       # Indian government common format
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y/%m/%d",
    "%d %b %Y",       # e.g. "15 Aug 2023"
    "%d %B %Y",       # e.g. "15 August 2023"
    "%B %d, %Y",      # e.g. "August 15, 2023"
]


def parse_date(value: Any) -> date | None:
    """
    Try to parse a date from various string formats used in government datasets.
    Returns None if parsing fails — never raises.
    """
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    s = clean_string(str(value))
    if not s:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


# ── URL helpers ───────────────────────────────────────────────────────────

def validate_url(url: str | None) -> bool:
    """
    Return True if url is a well-formed http/https URL with a hostname.
    Does NOT make a network request.
    """
    if not url:
        return False
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


# ── JSON helpers ──────────────────────────────────────────────────────────

def validate_json(raw: str | bytes) -> dict[str, Any] | list[Any] | None:
    """
    Parse a JSON string/bytes. Returns the parsed object on success,
    None on failure — never raises.
    """
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


# ── Pagination helpers ────────────────────────────────────────────────────

def chunk_list(items: list[T], size: int) -> list[list[T]]:
    """
    Split a list into consecutive sub-lists of at most `size` elements.

    Example:
        chunk_list([1,2,3,4,5], 2) → [[1,2],[3,4],[5]]
    """
    if size <= 0:
        raise ValueError(f"chunk size must be > 0, got {size}")
    return [items[i: i + size] for i in range(0, len(items), size)]


# ── Retry helpers ─────────────────────────────────────────────────────────

def calculate_retry_delay(
    attempt: int,
    base: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
) -> float:
    """
    Calculate exponential backoff delay for retry attempt N.

    Formula: min(base ** attempt, max_delay)
    With jitter (recommended for distributed systems): delay * random(0.5, 1.0)

    Args:
        attempt:   Retry number (1-indexed)
        base:      Backoff base in seconds (default 2.0)
        max_delay: Maximum delay cap in seconds (default 60.0)
        jitter:    Add random jitter to spread retries (default True)

    Returns:
        Delay in seconds as a float.
    """
    import random
    delay = min(base ** attempt, max_delay)
    if jitter:
        delay *= random.uniform(0.5, 1.0)
    return round(delay, 3)


def total_pages(total_records: int, page_size: int) -> int:
    """Return the number of pages needed for total_records at page_size per page."""
    if page_size <= 0:
        raise ValueError(f"page_size must be > 0, got {page_size}")
    return math.ceil(total_records / page_size) if total_records > 0 else 0
