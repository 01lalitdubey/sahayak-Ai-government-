"""
Recommendation Engine Schemas — Sahayak AI (Phase 5)
=====================================================
All Pydantic request/response contracts for the recommendation layer.

Schema hierarchy:
    RecommendationReason       — one human-readable reason line
    RecommendationScore        — per-factor score breakdown
    RecommendationSummary      — lightweight card (list views)
    RecommendationDetail       — full detail (single scheme view)
    RecommendationResponse     — paginated list envelope
    RecommendationRefreshResponse — POST /refresh response
    ProfileCompletionResponse  — profile completion status
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── Priority levels ───────────────────────────────────────────────────────

RecommendationPriority = Literal["HIGH", "MEDIUM", "LOW"]


# ── Reason ────────────────────────────────────────────────────────────────

class RecommendationReason(BaseModel):
    """
    A single human-readable reason explaining why a scheme was recommended.
    'reason_type' allows the frontend to apply distinct icons per type.
    """
    reason_type: Literal[
        "eligibility",
        "occupation",
        "income",
        "state",
        "category",
        "featured",
        "general",
    ]
    text: str


# ── Score breakdown ───────────────────────────────────────────────────────

class RecommendationScore(BaseModel):
    """
    Weighted per-factor score components.
    All individual scores are 0.0–max_weight; total is 0.0–100.0.
    """
    total: float = Field(ge=0.0, le=100.0, description="Aggregate recommendation score 0–100")
    eligibility_score: float = Field(ge=0.0, le=40.0, description="Score from eligibility rules (max 40)")
    occupation_score: float = Field(ge=0.0, le=20.0, description="Occupation match bonus (max 20)")
    income_score: float = Field(ge=0.0, le=15.0, description="Income range match bonus (max 15)")
    state_score: float = Field(ge=0.0, le=10.0, description="State match bonus (max 10)")
    category_score: float = Field(ge=0.0, le=10.0, description="Category match bonus (max 10)")
    featured_score: float = Field(ge=0.0, le=5.0, description="Featured scheme bonus (max 5)")


# ── Summary (used in list/grid views) ─────────────────────────────────────

class RecommendationSummary(BaseModel):
    """Lightweight recommendation for list and dashboard views."""
    scheme_id: uuid.UUID
    scheme_name: str
    scheme_code: str
    scheme_type: str
    category: str | None
    ministry: str | None
    state: str | None
    is_featured: bool
    official_url: str | None

    recommendation_score: float
    priority: RecommendationPriority
    eligibility_status: str        # eligible | incomplete_profile | no_rules
    eligible: bool

    reasons: list[RecommendationReason]
    missing_information: list[str]

    # Short description for card preview
    short_description: str | None


# ── Detail (used in /recommendations/{scheme_id} view) ───────────────────

class RecommendationDetail(BaseModel):
    """
    Full recommendation analysis for a single scheme.
    Includes score breakdown, all reasons, eligibility rule results,
    and complete scheme metadata.
    """
    scheme_id: uuid.UUID
    scheme_name: str
    scheme_code: str
    scheme_type: str
    category: str | None
    ministry: str | None
    department: str | None
    state: str | None
    is_featured: bool
    official_url: str | None
    official_pdf_url: str | None
    contact_email: str | None
    contact_phone: str | None
    short_description: str | None
    full_description: str | None
    benefits: str | None
    application_mode: str
    application_start_date: str | None
    application_end_date: str | None

    recommendation_score: float
    score_breakdown: RecommendationScore
    priority: RecommendationPriority
    eligibility_status: str
    eligible: bool

    reasons: list[RecommendationReason]
    missing_information: list[str]

    # Full rule-by-rule eligibility breakdown
    passed_rules: list[dict]
    failed_rules: list[dict]

    evaluated_at: datetime


# ── List response ─────────────────────────────────────────────────────────

class RecommendationResponse(BaseModel):
    """Paginated recommendation list — GET /recommendations."""
    success: bool = True
    message: str = "OK"
    total: int
    page: int
    page_size: int
    total_pages: int
    data: list[RecommendationSummary]


# ── Refresh response ──────────────────────────────────────────────────────

class RecommendationRefreshResponse(BaseModel):
    """Response for POST /recommendations/refresh."""
    success: bool = True
    message: str = "Recommendations refreshed successfully."
    total_recommendations: int
    refreshed_at: datetime


# ── Top recommendations ───────────────────────────────────────────────────

class TopRecommendationsResponse(BaseModel):
    """Response for GET /recommendations/top."""
    success: bool = True
    message: str = "OK"
    data: list[RecommendationSummary]


# ── Profile completion ────────────────────────────────────────────────────

class ProfileFieldStatus(BaseModel):
    field: str
    label: str
    filled: bool
    importance: Literal["required", "important", "optional"]


class ProfileCompletionResponse(BaseModel):
    """Profile completion breakdown for the dashboard card."""
    success: bool = True
    completion_percentage: float = Field(ge=0.0, le=100.0)
    filled_count: int
    total_fields: int
    missing_fields: list[str]
    fields: list[ProfileFieldStatus]
