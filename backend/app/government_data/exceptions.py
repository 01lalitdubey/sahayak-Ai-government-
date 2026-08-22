"""
Government Data Exceptions — Sahayak AI
=========================================
Dedicated exception hierarchy for the Government Data module.
Isolated from app.core.exceptions to keep concerns separate.

Every exception includes:
  - message   : human-readable description
  - error_code: machine-readable identifier for monitoring/alerting
  - details   : optional dict with structured context
"""

from typing import Any


class GovernmentAPIException(Exception):
    """
    Base exception for all Government Data module errors.
    Catch this to handle any module-level failure uniformly.
    """
    error_code: str = "GOVT_API_ERROR"

    def __init__(
        self,
        message: str = "A government API error occurred.",
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code or self.__class__.error_code
        self.details: dict[str, Any] = details or {}
        super().__init__(self.message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.error_code!r}, msg={self.message!r})"


# ── Authentication & authorisation ────────────────────────────────────────

class AuthenticationException(GovernmentAPIException):
    """API key is missing, expired, or rejected by the provider."""
    error_code = "GOVT_AUTH_ERROR"

    def __init__(self, message: str = "Authentication failed with the government API.", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


# ── Rate limiting ─────────────────────────────────────────────────────────

class RateLimitException(GovernmentAPIException):
    """Provider returned HTTP 429 — too many requests."""
    error_code = "GOVT_RATE_LIMIT"

    def __init__(
        self,
        message: str = "Rate limit exceeded. Request will be retried after backoff.",
        retry_after: int | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if retry_after is not None:
            details["retry_after_seconds"] = retry_after
        super().__init__(message, details=details, **kwargs)
        self.retry_after = retry_after


# ── Availability ──────────────────────────────────────────────────────────

class APIUnavailableException(GovernmentAPIException):
    """Provider is unreachable or returned a 5xx error."""
    error_code = "GOVT_API_UNAVAILABLE"

    def __init__(self, message: str = "Government API is currently unavailable.", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


# ── Response integrity ────────────────────────────────────────────────────

class InvalidResponseException(GovernmentAPIException):
    """Response was received but its structure is unexpected or unparseable."""
    error_code = "GOVT_INVALID_RESPONSE"

    def __init__(self, message: str = "Invalid response received from government API.", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


# ── Dataset issues ────────────────────────────────────────────────────────

class InvalidDatasetException(GovernmentAPIException):
    """The dataset exists but fails schema or content validation."""
    error_code = "GOVT_INVALID_DATASET"

    def __init__(self, message: str = "Dataset validation failed.", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


# ── Import process ────────────────────────────────────────────────────────

class ImportException(GovernmentAPIException):
    """An error occurred during the data import pipeline."""
    error_code = "GOVT_IMPORT_ERROR"

    def __init__(self, message: str = "Data import failed.", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


# ── Configuration ─────────────────────────────────────────────────────────

class ConfigurationException(GovernmentAPIException):
    """
    Module configuration is invalid or incomplete.
    Raised during startup before any API calls are made.
    """
    error_code = "GOVT_CONFIG_ERROR"

    def __init__(self, message: str = "Government data module configuration is invalid.", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


# ── Validation ────────────────────────────────────────────────────────────

class ValidationException(GovernmentAPIException):
    """Input data failed validation before being persisted."""
    error_code = "GOVT_VALIDATION_ERROR"

    def __init__(self, message: str = "Validation failed.", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
