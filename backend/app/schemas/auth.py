"""
Auth Schemas — Sahayak AI
==========================
All request/response contracts for the authentication endpoints.
password_hash is NEVER included in any response schema.
"""

import uuid
import re
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from app.models.enums import UserRole

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


# ── Register ──────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: str = Field(max_length=255)
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.lower().strip()
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address format.")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class RegisterResponse(BaseModel):
    success: bool = True
    message: str = "Registration successful."
    data: "AuthUserData"
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ── Login ─────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(max_length=128)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower().strip()


class LoginResponse(BaseModel):
    success: bool = True
    message: str = "Login successful."
    data: "AuthUserData"
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ── Token ─────────────────────────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    success: bool = True
    message: str = "Token refreshed."
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ── Current user ──────────────────────────────────────────────────────────
class AuthUserData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class CurrentUserResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: AuthUserData


# ── Logout ────────────────────────────────────────────────────────────────
class LogoutResponse(BaseModel):
    success: bool = True
    message: str = "Logged out successfully."


# resolve forward refs
RegisterResponse.model_rebuild()
LoginResponse.model_rebuild()
