"""
Profile Schemas — Sahayak AI
==============================
Pydantic v2 contracts for the citizen demographic profile.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.enums import (
    GenderEnum,
    OccupationEnum,
    EducationEnum,
    CategoryEnum,
)

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]


class ProfileBase(BaseModel):
    age: int | None = Field(default=None, ge=0, le=150)
    gender: GenderEnum | None = None
    occupation: OccupationEnum | None = None
    annual_income: int | None = Field(
        default=None, ge=0, description="Annual household income in INR"
    )
    state: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    education: EducationEnum | None = None
    category: CategoryEnum | None = None
    is_farmer: bool = False
    is_disabled: bool = False

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str | None) -> str | None:
        if v is not None and v not in INDIAN_STATES:
            raise ValueError(f"'{v}' is not a recognised Indian state or UT.")
        return v


class ProfileCreate(ProfileBase):
    """Create profile for a specific user (user_id supplied by service layer)."""
    pass


class ProfileUpdate(BaseModel):
    """Partial update — all fields optional."""
    age: int | None = Field(default=None, ge=0, le=150)
    gender: GenderEnum | None = None
    occupation: OccupationEnum | None = None
    annual_income: int | None = Field(default=None, ge=0)
    state: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    education: EducationEnum | None = None
    category: CategoryEnum | None = None
    is_farmer: bool | None = None
    is_disabled: bool | None = None


class ProfileRead(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ProfileResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: ProfileRead | None = None
