"""
Data Transformers — Sahayak AI
================================
Pure transformation functions. No side effects, no I/O, fully testable.
Each function takes a raw value and returns a clean Python value.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from typing import Any


# ── Text ──────────────────────────────────────────────────────────────────

def clean_text(value: Any) -> str | None:
    """Strip, normalise Unicode, collapse whitespace. Returns None for empty."""
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() in {"na", "n/a", "nil", "none", "-", "--", "null", "not available"}:
        return None
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def truncate(value: str | None, max_len: int) -> str | None:
    """Truncate a string to max_len characters."""
    if not value:
        return value
    return value[:max_len] if len(value) > max_len else value


# ── URL ───────────────────────────────────────────────────────────────────

_URL_SCHEME_RE = re.compile(r"^https?://", re.IGNORECASE)


def normalize_url(value: Any) -> str | None:
    """Clean a URL string. Returns None if not a valid http/https URL."""
    s = clean_text(value)
    if not s:
        return None
    # Add https:// if missing scheme
    if not _URL_SCHEME_RE.match(s):
        if s.startswith("www."):
            s = "https://" + s
        else:
            return None
    # Remove trailing slash for consistency
    return s.rstrip("/")


# ── Email ─────────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def normalize_email(value: Any) -> str | None:
    """Lowercase and validate an email address."""
    s = clean_text(value)
    if not s:
        return None
    s = s.lower()
    return s if _EMAIL_RE.match(s) else None


# ── Phone ─────────────────────────────────────────────────────────────────

_NON_DIGIT_RE = re.compile(r"[^\d+]")


def normalize_phone(value: Any) -> str | None:
    """Strip formatting from a phone number, keep digits and leading +."""
    s = clean_text(value)
    if not s:
        return None
    # Keep leading + for international format
    prefix = "+" if s.startswith("+") else ""
    digits = re.sub(r"\D", "", s)
    if len(digits) < 7:
        return None
    return prefix + digits


# ── Date ──────────────────────────────────────────────────────────────────

_DATE_FORMATS = [
    "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
    "%Y/%m/%d", "%d %b %Y", "%d %B %Y", "%B %d, %Y",
    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ",
]


def normalize_date(value: Any) -> date | None:
    """Parse a date from various string formats. Returns None on failure."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    s = clean_text(str(value))
    if not s:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


# ── Boolean ───────────────────────────────────────────────────────────────

_TRUE_VALS = frozenset({"true", "yes", "1", "active", "enabled", "y", "on"})
_FALSE_VALS = frozenset({"false", "no", "0", "inactive", "disabled", "n", "off"})


def normalize_bool(value: Any, default: bool = True) -> bool:
    """Coerce a value to boolean. Returns default if unrecognised."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    s = clean_text(str(value))
    if not s:
        return default
    low = s.lower()
    if low in _TRUE_VALS:
        return True
    if low in _FALSE_VALS:
        return False
    return default


# ── State names ───────────────────────────────────────────────────────────

_STATE_ALIASES: dict[str, str] = {
    "ap": "Andhra Pradesh",
    "andhra": "Andhra Pradesh",
    "arunachal": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal": "Himachal Pradesh",
    "hp": "Himachal Pradesh",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "mp": "Madhya Pradesh",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "orissa": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tn": "Tamil Nadu",
    "tamil nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "up": "Uttar Pradesh",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "wb": "West Bengal",
    "west bengal": "West Bengal",
    "delhi": "Delhi",
    "j&k": "Jammu and Kashmir",
    "jammu": "Jammu and Kashmir",
    "kashmir": "Jammu and Kashmir",
    "ladakh": "Ladakh",
    "chandigarh": "Chandigarh",
    "puducherry": "Puducherry",
    "pondicherry": "Puducherry",
}


def normalize_state(value: Any) -> str | None:
    """Normalise a state name to its canonical Indian state name."""
    s = clean_text(value)
    if not s:
        return None
    low = s.lower().strip()
    # "All India" / "pan-india" → NULL (central scheme, no state restriction)
    if low in {"all india", "pan india", "pan-india", "national", "all states", "all"}:
        return None
    return _STATE_ALIASES.get(low) or s.title()


# ── Ministry names ────────────────────────────────────────────────────────

_MINISTRY_PREFIXES = (
    "ministry of ", "dept. of ", "department of ",
    "ministry ", "department ", "govt. of ",
)


def normalize_ministry(value: Any) -> str | None:
    """Title-case a ministry name and clean common variations."""
    s = clean_text(value)
    if not s:
        return None
    # Title case preserving acronyms
    words = s.split()
    return " ".join(w if w.isupper() and len(w) <= 4 else w.title() for w in words)


# ── Category ──────────────────────────────────────────────────────────────

_CATEGORY_MAP: dict[str, str] = {
    "farmer": "farmer", "agriculture": "agriculture", "agri": "agriculture",
    "education": "education", "school": "education", "student": "student",
    "health": "health", "healthcare": "healthcare", "medical": "health",
    "housing": "housing", "shelter": "housing", "home": "housing",
    "women": "women", "woman": "women", "gender": "women",
    "employment": "employment", "jobs": "employment", "job": "employment",
    "social": "social_welfare", "welfare": "social_welfare",
    "pension": "pension", "retirement": "pension",
    "disability": "disability", "disabled": "disability",
    "minority": "minority", "minorities": "minority",
    "tribal": "tribal", "st": "tribal",
    "skill": "skill_development", "training": "skill_development",
    "finance": "finance", "financial": "financial_inclusion",
    "business": "business", "msme": "business", "entrepreneur": "business",
    "transport": "transport",
    "insurance": "insurance",
    "rural": "rural_development",
}


def normalize_category(value: Any) -> str | None:
    """Map external category names to internal SchemeCategoryEnum values."""
    s = clean_text(value)
    if not s:
        return None
    low = s.lower().strip()
    # Exact match first
    if low in _CATEGORY_MAP:
        return _CATEGORY_MAP[low]
    # Partial match
    for key, mapped in _CATEGORY_MAP.items():
        if key in low:
            return mapped
    return "other"


# ── Scheme type ───────────────────────────────────────────────────────────

def normalize_scheme_type(value: Any) -> str:
    """Return 'central' or 'state'. Defaults to 'central'."""
    s = clean_text(value)
    if not s:
        return "central"
    low = s.lower()
    return "state" if any(k in low for k in ("state", "provincial", "local")) else "central"


# ── Application mode ──────────────────────────────────────────────────────

def normalize_application_mode(value: Any) -> str:
    """Return 'online', 'offline', or 'both'. Defaults to 'online'."""
    s = clean_text(value)
    if not s:
        return "online"
    low = s.lower()
    if "both" in low or ("online" in low and "offline" in low):
        return "both"
    if "offline" in low or "manual" in low or "physical" in low:
        return "offline"
    return "online"


# ── Scheme code ───────────────────────────────────────────────────────────

_NON_ALNUM_RE = re.compile(r"[^A-Z0-9\-]")


def normalize_scheme_code(value: Any, fallback: str | None = None) -> str | None:
    """
    Generate a normalised scheme code from a raw value.
    Example: "pm kisan samman nidhi 2024" → "PM-KISAN-SAMMAN-NIDHI-2024"
    """
    s = clean_text(value)
    if not s:
        return fallback
    code = s.upper().replace(" ", "-")
    code = _NON_ALNUM_RE.sub("", code)
    # Collapse multiple dashes
    code = re.sub(r"-{2,}", "-", code).strip("-")
    return code[:50] if code else fallback
