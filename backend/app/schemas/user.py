"""
User Schemas — Sahayak AI
==========================
Pydantic v2 request/response contracts for the User domain.
password_hash is NEVER exposed in any response schema.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator
import re

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


# ── Base ──────────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    email: str = Field(max_length=255)
    full_name: str = Field(min_length=2, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        v = v.lower().strip()
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address format.")
        return v


# ── Create ────────────────────────────────────────────────────────────────
class UserCreate(UserBase):
    """
    Used when registering a new user (Phase 2 auth).
    password field will be hashed before persisting.
    """
    password: str = Field(min_length=8, max_length=128)


# ── Update ────────────────────────────────────────────────────────────────
class UserUpdate(BaseModel):
    """Partial update — all fields optional."""
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    is_active: bool | None = None
    is_verified: bool | None = None


# ── DB → Read ─────────────────────────────────────────────────────────────
class UserRead(UserBase):
    """
    Safe public representation of a user.
    password_hash is intentionally excluded.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


# ── Response envelope ─────────────────────────────────────────────────────
class UserResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: UserRead | None = None
