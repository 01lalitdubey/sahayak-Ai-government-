"""
Application Exception Hierarchy — Sahayak AI
==============================================
Custom exceptions keep error handling explicit and testable.
Every exception maps to a specific HTTP status code.
Route handlers catch these and convert them to clean JSON responses
via the exception handlers registered in main.py.
"""


class SahayakBaseException(Exception):
    """Root exception — all custom exceptions inherit from here."""
    status_code: int = 500
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.message
        super().__init__(self.message)


# ── 400 Bad Request ────────────────────────────────────────────────────────
class ValidationException(SahayakBaseException):
    status_code = 400
    message = "Validation failed."


class DuplicateEmailException(SahayakBaseException):
    status_code = 409
    message = "An account with this email already exists."


class DuplicateResourceException(SahayakBaseException):
    status_code = 409
    message = "This resource already exists."


class IntegrityException(SahayakBaseException):
    """Raised when a DB IntegrityError is caught (FK, unique, not-null)."""
    status_code = 409
    message = "Data integrity constraint violated."


# ── 404 Not Found ──────────────────────────────────────────────────────────
class NotFoundException(SahayakBaseException):
    status_code = 404
    message = "Resource not found."


class UserNotFoundException(NotFoundException):
    message = "User not found."


class ProfileNotFoundException(NotFoundException):
    message = "Profile not found."


class SchemeNotFoundException(NotFoundException):
    message = "Scheme not found."


# ── 503 Service Unavailable ───────────────────────────────────────────────
class DatabaseUnavailableException(SahayakBaseException):
    status_code = 503
    message = "Database is currently unavailable. Please try again later."


class ConnectionTimeoutException(SahayakBaseException):
    status_code = 504
    message = "Database connection timed out."


# ── 401 Unauthorised ──────────────────────────────────────────────────────
class UnauthorisedException(SahayakBaseException):
    status_code = 401
    message = "Authentication required."


class InvalidCredentialsException(SahayakBaseException):
    status_code = 401
    message = "Invalid email or password."


class InvalidTokenException(SahayakBaseException):
    status_code = 401
    message = "Invalid or malformed token."


class ExpiredTokenException(SahayakBaseException):
    status_code = 401
    message = "Token has expired. Please log in again."


class TokenMissingException(SahayakBaseException):
    status_code = 401
    message = "Authentication token is missing."


# ── 403 Forbidden ─────────────────────────────────────────────────────────
class ForbiddenException(SahayakBaseException):
    status_code = 403
    message = "You do not have permission to perform this action."


class InactiveUserException(SahayakBaseException):
    status_code = 403
    message = "This account is inactive. Please contact support."


# ── Scheme-specific ───────────────────────────────────────────────────────
class DuplicateSchemeNameException(SahayakBaseException):
    status_code = 409
    message = "A scheme with this name already exists in the same scope."


class DuplicateSchemeCodeException(SahayakBaseException):
    status_code = 409
    message = "A scheme with this code already exists."


class SchemeInactiveException(SahayakBaseException):
    status_code = 400
    message = "This scheme is inactive."


# ── RAG / Voice assistant ────────────────────────────────────────────────
class RagDisabledException(SahayakBaseException):
    status_code = 503
    message = "The AI assistant is not configured. Set GROQ_API_KEY on the server."


class RagServiceException(SahayakBaseException):
    status_code = 502
    message = "The AI assistant is temporarily unavailable. Please try again."


class RagIndexEmptyException(SahayakBaseException):
    status_code = 409
    message = "No scheme data has been indexed yet. Run POST /api/v1/rag/ingest first."


class UnsupportedLanguageException(SahayakBaseException):
    status_code = 400
    message = "Unsupported language. Use one of the 13 supported codes or 'auto'."


# ── Eligibility-specific ──────────────────────────────────────────────────
class ProfileIncompleteException(SahayakBaseException):
    status_code = 422
    message = "Your profile is incomplete. Please complete your profile before checking eligibility."


class NoEligibilityRulesException(SahayakBaseException):
    status_code = 404
    message = "No eligibility rules are defined for this scheme."
