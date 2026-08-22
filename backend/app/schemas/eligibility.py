"""
Eligibility Engine Schemas — Sahayak AI
=========================================
All request/response contracts for the eligibility evaluation API.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import GenderEnum, OccupationEnum, CategoryEnum
from app.schemas.scheme import SchemeSummary


# ── Request ───────────────────────────────────────────────────────────────

class EligibilityCheckRequest(BaseModel):
    scheme_id: uuid.UUID


# ── Rule evaluation result ────────────────────────────────────────────────

class RuleResult(BaseModel):
    """Result of evaluating one single criterion."""
    criterion: str          # Human-readable criterion name e.g. "Age"
    requirement: str        # What the rule requires e.g. "18–60 years"
    user_value: str         # What the user has e.g. "35 years"
    passed: bool
    reason: str             # Full explanation e.g. "Age 35 is within 18–60"


# ── Single-scheme eligibility analysis ───────────────────────────────────

class EligibilityStatus(str):
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    INCOMPLETE_PROFILE = "incomplete_profile"
    NO_RULES = "no_rules"


class EligibilityCheckResponse(BaseModel):
    """
    Detailed eligibility result for one scheme.
    Returned by POST /eligibility/check and GET /eligibility/{scheme_id}.
    """
    scheme_id: uuid.UUID
    scheme_name: str
    scheme_code: str
    eligible: bool
    status: Literal["eligible", "not_eligible", "incomplete_profile", "no_rules"]
    score: float = Field(ge=0.0, le=100.0, description="0–100 percentage of rules passed")
    total_rules: int
    passed_count: int
    failed_count: int
    missing_count: int
    passed_rules: list[RuleResult]
    failed_rules: list[RuleResult]
    missing_information: list[str]
    recommendations: list[str]
    evaluated_at: datetime


# ── Summary (lightweight — used in bulk listing) ──────────────────────────

class EligibilitySummary(BaseModel):
    """Lightweight summary for GET /eligibility/my-schemes list view."""
    scheme_id: uuid.UUID
    scheme_name: str
    scheme_code: str
    scheme_type: str
    category: str | None
    ministry: str | None
    state: str | None
    eligible: bool
    status: Literal["eligible", "not_eligible", "incomplete_profile", "no_rules"]
    score: float
    total_rules: int
    passed_count: int


class MySchemeEligibilityResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    total_schemes: int
    eligible_count: int
    not_eligible_count: int
    incomplete_count: int
    profile_completion: float = Field(description="0–100 % of profile fields filled")
    data: list[EligibilitySummary]


# ── Admin rule management ─────────────────────────────────────────────────

class EligibilityRuleAdminCreate(BaseModel):
    """Admin creates a rule for a specific scheme."""
    scheme_id: uuid.UUID
    minimum_age: int | None = Field(default=None, ge=0, le=150)
    maximum_age: int | None = Field(default=None, ge=0, le=150)
    minimum_income: int | None = Field(default=None, ge=0)
    maximum_income: int | None = Field(default=None, ge=0)
    gender: GenderEnum | None = None
    occupation: OccupationEnum | None = None
    state: str | None = Field(default=None, max_length=100)
    category: CategoryEnum | None = None
    education: str | None = None
    require_farmer: bool | None = None
    require_disabled: bool | None = None


class EligibilityRuleAdminUpdate(BaseModel):
    """All fields optional — partial update."""
    minimum_age: int | None = Field(default=None, ge=0, le=150)
    maximum_age: int | None = Field(default=None, ge=0, le=150)
    minimum_income: int | None = Field(default=None, ge=0)
    maximum_income: int | None = Field(default=None, ge=0)
    gender: GenderEnum | None = None
    occupation: OccupationEnum | None = None
    state: str | None = None
    category: CategoryEnum | None = None
    education: str | None = None
    require_farmer: bool | None = None
    require_disabled: bool | None = None


class EligibilityRuleAdminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scheme_id: uuid.UUID
    minimum_age: int | None
    maximum_age: int | None
    maximum_income: int | None
    gender: GenderEnum | None
    occupation: OccupationEnum | None
    state: str | None
    category: CategoryEnum | None
    created_at: datetime
    updated_at: datetime


class EligibilityRuleAdminResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: EligibilityRuleAdminRead | None = None


class EligibilityRuleListResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: list[EligibilityRuleAdminRead]
    total: int
