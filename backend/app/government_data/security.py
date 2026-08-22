"""
Government Data Security — Sahayak AI
========================================
Secure handling of API credentials and sensitive configuration.

Responsibilities:
  - Mask API keys in log output
  - Validate that required credentials exist before any API call
  - Provide a safe representation of config for status endpoints
  - Prevent accidental exposure of secrets in responses or logs
  - Scaffold for future OAuth2 token management
"""

import re
from typing import Any

from app.government_data.constants import MASKED_VALUE, API_KEY_VISIBLE_CHARS
from app.government_data.exceptions import AuthenticationException, ConfigurationException
from app.government_data.logger import GovtDataLogger

_logger = GovtDataLogger(__name__)

_LOOKS_LIKE_KEY = re.compile(r"[A-Za-z0-9\-_]{16,}")


def mask_api_key(key: str | None) -> str:
    """
    Return a safely masked version of an API key.

    Rules:
      - None or empty  → MASKED_VALUE
      - ≤ 4 chars      → MASKED_VALUE  (too short to show anything)
      - > 4 chars      → MASKED_VALUE + last 4 characters

    Example:
        mask_api_key("abc123xyz789abcd") → "***REDACTED***abcd"
    """
    if not key:
        return MASKED_VALUE
    if len(key) <= API_KEY_VISIBLE_CHARS:
        return MASKED_VALUE
    return f"{MASKED_VALUE}{key[-API_KEY_VISIBLE_CHARS:]}"


def validate_api_key(key: str | None, provider: str = "unknown") -> str:
    """
    Assert that an API key is present and looks structurally valid.

    Args:
        key:      The raw API key string
        provider: Human-readable provider name for error messages

    Returns:
        The key unchanged if valid.

    Raises:
        AuthenticationException: key is missing
        ConfigurationException:  key exists but is structurally invalid
    """
    if not key or not key.strip():
        _logger.auth_failed(provider)
        raise AuthenticationException(
            message=f"API key for provider '{provider}' is not configured.",
            details={"provider": provider, "hint": "Set the corresponding env var in .env"},
        )

    stripped = key.strip()
    if not _LOOKS_LIKE_KEY.match(stripped):
        raise ConfigurationException(
            message=f"API key for provider '{provider}' appears invalid (too short or bad format).",
            details={"provider": provider, "key_preview": mask_api_key(stripped)},
        )

    _logger.debug(
        "API key validated for provider=%s key_preview=%s",
        provider,
        mask_api_key(stripped),
    )
    return stripped


def validate_base_url(url: str | None, provider: str = "unknown") -> str:
    """
    Assert that a base URL is present and starts with https://.

    Raises:
        ConfigurationException: URL is missing or uses plain http in production intent.
    """
    if not url or not url.strip():
        raise ConfigurationException(
            message=f"Base URL for provider '{provider}' is not configured.",
            details={"provider": provider},
        )
    stripped = url.strip().rstrip("/")
    if not stripped.startswith(("http://", "https://")):
        raise ConfigurationException(
            message=f"Base URL for provider '{provider}' must start with http:// or https://.",
            details={"provider": provider, "url": stripped},
        )
    return stripped


def safe_config_repr(config_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Return a sanitised copy of a config dictionary safe for logging or
    status API responses. Redacts any value whose key contains common
    sensitive keywords.

    Example:
        safe_config_repr({"DATA_GOV_API_KEY": "secret", "TIMEOUT": 30})
        → {"DATA_GOV_API_KEY": "***REDACTED***cret", "TIMEOUT": 30}
    """
    _SENSITIVE_KEYS = frozenset({
        "api_key", "apikey", "secret", "password", "token",
        "credential", "auth", "private",
    })

    result: dict[str, Any] = {}
    for k, v in config_dict.items():
        key_lower = k.lower()
        if any(sensitive in key_lower for sensitive in _SENSITIVE_KEYS):
            result[k] = mask_api_key(str(v)) if v else MASKED_VALUE
        else:
            result[k] = v
    return result


def get_auth_headers(api_key: str, header_name: str = "api-key") -> dict[str, str]:
    """
    Build the HTTP headers dict for API key authentication.
    The key value is used directly — never log the returned dict.

    Args:
        api_key:     Validated API key string
        header_name: Header name expected by the provider (default: "api-key")

    Returns:
        Dict suitable for use in httpx/requests headers parameter.
    """
    return {header_name: api_key}
