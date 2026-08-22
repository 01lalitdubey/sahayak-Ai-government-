"""
Recommendation Engine Endpoints — Sahayak AI (Phase 5)
=======================================================
All routes require authentication (Bearer token).

Routes:
    GET  /api/v1/recommendations              — paginated recommendations
    GET  /api/v1/recommendations/top          — top 5 for dashboard
    GET  /api/v1/recommendations/profile      — profile completion data
    GET  /api/v1/recommendations/{scheme_id}  — single scheme detail
    POST /api/v1/recommendations/refresh      — force re-score
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.api.deps import get_language
from app.database.database import get_db
from app.models.user import User
from app.schemas.recommendation import (
    ProfileCompletionResponse,
    RecommendationDetail,
    RecommendationRefreshResponse,
    RecommendationResponse,
    TopRecommendationsResponse,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


def _svc(db: AsyncSession = Depends(get_db)) -> RecommendationService:
    return RecommendationService(db)


# ── Fixed-path routes MUST be declared before /{scheme_id} ───────────────

@router.get(
    "/top",
    response_model=TopRecommendationsResponse,
    summary="Get top 5 recommendations for the dashboard",
)
async def get_top_recommendations(
    limit: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
    lang: str = Depends(get_language),
    svc: RecommendationService = Depends(_svc),
) -> TopRecommendationsResponse:
    """
    Returns the highest-scoring recommendations for the authenticated user.
    Returns an empty list (not an error) if the user has no profile yet.
    """
    return await svc.get_top_recommendations(current_user.id, limit=limit, lang=lang)


@router.get(
    "/profile",
    response_model=ProfileCompletionResponse,
    summary="Get profile completion status",
)
async def get_profile_completion(
    current_user: User = Depends(get_current_active_user),
    svc: RecommendationService = Depends(_svc),
) -> ProfileCompletionResponse:
    """
    Returns profile completion percentage, missing fields, and per-field details.
    Used by the dashboard ProfileCompletionCard component.
    """
    return await svc.get_profile_completion(current_user.id)


@router.post(
    "/refresh",
    response_model=RecommendationRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Recalculate recommendation scores",
)
async def refresh_recommendations(
    current_user: User = Depends(get_current_active_user),
    svc: RecommendationService = Depends(_svc),
) -> RecommendationRefreshResponse:
    """
    Force re-evaluation of all schemes for the authenticated user.
    Call this after updating a profile to get fresh recommendations.
    """
    return await svc.refresh_recommendations(current_user.id)


@router.get(
    "",
    response_model=RecommendationResponse,
    summary="Get personalised ranked recommendations",
)
async def get_recommendations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    priority: str | None = Query(default=None, description="Filter: HIGH | MEDIUM | LOW"),
    category: str | None = Query(default=None, description="Filter by scheme category"),
    sort: str = Query(
        default="score_desc",
        description="Sort order: score_desc | score_asc | alphabetical | priority",
    ),
    current_user: User = Depends(get_current_active_user),
    lang: str = Depends(get_language),
    svc: RecommendationService = Depends(_svc),
) -> RecommendationResponse:
    """
    Returns all recommendations for the authenticated user, ranked by score.
    Supports filtering by priority level and category, and multiple sort orders.
    """
    return await svc.get_recommendations(
        current_user.id,
        page=page,
        page_size=page_size,
        priority_filter=priority,
        category_filter=category,
        sort=sort,
        lang=lang,
    )


@router.get(
    "/{scheme_id}",
    response_model=RecommendationDetail,
    summary="Get detailed recommendation analysis for a scheme",
)
async def get_recommendation(
    scheme_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    lang: str = Depends(get_language),
    svc: RecommendationService = Depends(_svc),
) -> RecommendationDetail:
    """
    Returns the full recommendation analysis for one scheme:
    score breakdown, all reasons, eligibility rule results,
    and complete scheme metadata.
    """
    return await svc.get_recommendation(current_user.id, scheme_id, lang=lang)
