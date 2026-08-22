"""
EligibilityRule Schemas — Sahayak AI
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, model_validator

from app.models.enums import GenderEnum, OccupationEnum, CategoryEnum


class EligibilityRuleBase(BaseModel):
    minimum_age: int | None = Field(default=None, ge=0, le=150)
    maximum_age: int | None = Field(default=None, ge=0, le=150)
    maximum_income: int | None = Field(default=None, ge=0)
    gender: GenderEnum | None = None
    occupation: OccupationEnum | None = None
    state: str | None = Field(default=None, max_length=100)
    category: CategoryEnum | None = None

    @model_validator(mode="after")
    def check_age_range(self) -> "EligibilityRuleBase":
        if (
            self.minimum_age is not None
            and self.maximum_age is not None
            and self.minimum_age > self.maximum_age
        ):
            raise ValueError("minimum_age cannot be greater than maximum_age")
        return self


class EligibilityRuleCreate(EligibilityRuleBase):
    scheme_id: uuid.UUID


class EligibilityRuleUpdate(BaseModel):
    minimum_age: int | None = Field(default=None, ge=0, le=150)
    maximum_age: int | None = Field(default=None, ge=0, le=150)
    maximum_income: int | None = Field(default=None, ge=0)
    gender: GenderEnum | None = None
    occupation: OccupationEnum | None = None
    state: str | None = None
    category: CategoryEnum | None = None


class EligibilityRuleRead(EligibilityRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scheme_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class EligibilityRuleResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: EligibilityRuleRead | None = None
