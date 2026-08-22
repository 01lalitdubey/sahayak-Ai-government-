"""
Global Exception Handlers — Sahayak AI
========================================
Registered in main.py — convert every exception type into a
consistent JSON error envelope using the ErrorResponse schema.
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, TimeoutError

from app.core.exceptions import (
    SahayakBaseException,
    DuplicateEmailException,
    IntegrityException,
    DatabaseUnavailableException,
    ConnectionTimeoutException,
)

logger = logging.getLogger(__name__)


def _error(status: int, message: str, field: str | None = None) -> JSONResponse:
    content: dict = {"success": False, "message": message, "status_code": status}
    if field:
        content["errors"] = [{"field": field, "message": message}]
    return JSONResponse(status_code=status, content=content)


async def sahayak_exception_handler(
    request: Request, exc: SahayakBaseException
) -> JSONResponse:
    """Handles all custom application exceptions."""
    logger.warning(
        "Application exception on %s %s: [%d] %s",
        request.method, request.url.path, exc.status_code, exc.message,
    )
    return _error(exc.status_code, exc.message)


async def sqlalchemy_integrity_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    """
    Catches SQLAlchemy IntegrityError (unique violations, FK failures, etc.)
    Inspects the error message to return a human-readable message.
    """
    logger.error("IntegrityError on %s: %s", request.url.path, exc.orig)
    orig = str(exc.orig).lower()
    if "unique" in orig and "email" in orig:
        return _error(409, "An account with this email already exists.", "email")
    if "unique" in orig:
        return _error(409, "A record with these values already exists.")
    if "foreign key" in orig or "violates foreign key" in orig:
        return _error(422, "Referenced resource does not exist.")
    if "not null" in orig or "null value" in orig:
        return _error(422, "A required field is missing.")
    return _error(409, "Data integrity constraint violated.")


async def sqlalchemy_operational_handler(
    request: Request, exc: OperationalError
) -> JSONResponse:
    """Catches DB connectivity failures."""
    logger.error("OperationalError on %s: %s", request.url.path, exc)
    return _error(503, "Database is currently unavailable. Please try again later.")


async def sqlalchemy_timeout_handler(
    request: Request, exc: TimeoutError
) -> JSONResponse:
    """Catches DB connection/query timeouts."""
    logger.error("Database TimeoutError on %s: %s", request.url.path, exc)
    return _error(504, "Database connection timed out.")


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all for any exception not handled above."""
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method, request.url.path, exc,
        exc_info=True,
    )
    return _error(500, "An unexpected error occurred. Please try again later.")
