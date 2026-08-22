"""
Response Helpers — Sahayak AI
Factory functions that build consistent API response envelopes.
Routes import these instead of constructing dicts manually.
"""

from typing import Any
from app.schemas.common import SuccessResponse, ErrorResponse, ErrorDetail


def ok(data: Any = None, message: str = "OK") -> SuccessResponse:
    return SuccessResponse(success=True, message=message, data=data)


def error(message: str, status_code: int = 400, errors: list[ErrorDetail] | None = None) -> ErrorResponse:
    return ErrorResponse(
        success=False,
        message=message,
        status_code=status_code,
        errors=errors or [],
    )
