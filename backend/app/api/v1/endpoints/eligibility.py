"""
Eligibility Engine Endpoints — Sahayak AI
==========================================
User endpoints (requires login):
    POST /api/v1/eligibility/check          — check one scheme
    GET  /api/v1/eligibility/my-schemes     — bulk check all schemes
    GET  /api/v1/eligibility/{scheme_id}    — detailed analysis

Admin endpoints:
    GET    /api/v1/eligibility/admin/rules
    POST   /api/v1/eligibility/admin/rules
    PUT    /api/v1/eligibility/admin/rules/{id}
    DELETE /api/v1/eligibility/admin/rules/{id}
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user, require_admin
from app.api.deps import get_language
from app.database.database import get_db
from app.models.user import User
from app.schemas.eligibility import (
    EligibilityCheckRequest,
    EligibilityCheckResponse,
    MySchemeEligibilityResponse,
    EligibilityRuleAdminCreate,
    EligibilityRuleAdminUpdate,
    EligibilityRuleAdminResponse,
    EligibilityRuleListResponse,
)
from app.services.eligibility_service import EligibilityService

router = APIRouter(prefix="/eligibility", tags=["Eligibility"])


def _svc(db: AsyncSession = Depends(get_db)) -> EligibilityService:
    return EligibilityService(db)


# ── User endpoints ────────────────────────────────────────────────────────

@router.post(
    "/check",
    response_model=EligibilityCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Check eligibility for one scheme",
)
async def check_eligibility(
    payload: EligibilityCheckRequest,
    current_user: User = Depends(get_current_active_user),
    lang: str = Depends(get_language),
    svc: EligibilityService = Depends(_svc),
) -> EligibilityCheckResponse:
    return await svc.evaluate_scheme(payload.scheme_id, current_user.id, lang=lang)


@router.get(
    "/my-schemes",
    response_model=MySchemeEligibilityResponse,
    summary="Get eligibility status across all schemes",
)
async def my_schemes(
    current_user: User = Depends(get_current_active_user),
    lang: str = Depends(get_language),
    svc: EligibilityService = Depends(_svc),
) -> MySchemeEligibilityResponse:
    return await svc.get_my_schemes(current_user.id, lang=lang)


@router.get(
    "/{scheme_id}",
    response_model=EligibilityCheckResponse,
    summary="Detailed eligibility analysis for one scheme",
)
async def get_eligibility(
    scheme_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    lang: str = Depends(get_language),
    svc: EligibilityService = Depends(_svc),
) -> EligibilityCheckResponse:
    return await svc.evaluate_scheme(scheme_id, current_user.id, lang=lang)


# ── Admin endpoints ───────────────────────────────────────────────────────

@router.get(
    "/admin/rules",
    response_model=EligibilityRuleListResponse,
    summary="List eligibility rules [Admin]",
)
async def list_rules(
    scheme_id: uuid.UUID | None = Query(default=None),
    _: User = Depends(require_admin),
    svc: EligibilityService = Depends(_svc),
) -> EligibilityRuleListResponse:
    return await svc.list_rules(scheme_id=scheme_id)


@router.post(
    "/admin/rules",
    response_model=EligibilityRuleAdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create eligibility rule [Admin]",
)
async def create_rule(
    payload: EligibilityRuleAdminCreate,
    _: User = Depends(require_admin),
    svc: EligibilityService = Depends(_svc),
) -> EligibilityRuleAdminResponse:
    data = payload.model_dump(exclude_unset=False)
    return await svc.create_rule(data)


@router.put(
    "/admin/rules/{rule_id}",
    response_model=EligibilityRuleAdminResponse,
    summary="Update eligibility rule [Admin]",
)
async def update_rule(
    rule_id: uuid.UUID,
    payload: EligibilityRuleAdminUpdate,
    _: User = Depends(require_admin),
    svc: EligibilityService = Depends(_svc),
) -> EligibilityRuleAdminResponse:
    data = payload.model_dump(exclude_unset=True)
    return await svc.update_rule(rule_id, data)


@router.delete(
    "/admin/rules/{rule_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete eligibility rule [Admin]",
)
async def delete_rule(
    rule_id: uuid.UUID,
    _: User = Depends(require_admin),
    svc: EligibilityService = Depends(_svc),
) -> dict:
    return await svc.delete_rule(rule_id)
