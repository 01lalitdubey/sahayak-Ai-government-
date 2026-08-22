"""
Common Pydantic v2 Schemas — reusable response wrappers.
These envelope all API responses in a consistent shape so the
frontend always knows where to find data, errors, and metadata.
"""

from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Generic success envelope used by all endpoints."""

    success: bool = True
    message: str = "OK"
    data: T | None = None


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    """Standard error envelope — mirrors RFC 7807 Problem Details."""

    success: bool = False
    message: str
    errors: list[ErrorDetail] = Field(default_factory=list)
    status_code: int


class PaginationMeta(BaseModel):
    """Pagination metadata for list endpoints."""

    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list wrapper."""

    success: bool = True
    data: list[T]
    meta: PaginationMeta
