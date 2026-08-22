"""
Scheme Endpoints — Sahayak AI (Phase 4)
=========================================
All route handlers are intentionally thin — logic lives in SchemeService.

Public (no auth):
    GET  /schemes          — search + filter + paginate
    GET  /schemes/featured — featured schemes
    GET  /schemes/recent   — recent schemes
    GET  /schemes/categories — enum values
    GET  /schemes/states   — distinct active states
    GET  /schemes/{id}     — scheme detail (increments view_count)
    GET  /schemes/code/{code} — by scheme_code

Admin only:
    POST   /schemes           — create
    PUT    /schemes/{id}      — full update
    PATCH  /schemes/{id}/status  — activate/deactivate
    PATCH  /schemes/{id}/restore — restore soft-deleted
    DELETE /schemes/{id}         — soft delete
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user, require_admin
from app.database.database import get_db
from app.api.deps import get_language
from app.models.user import User
from app.schemas.scheme import (
    SchemeCreate,
    SchemeUpdate,
    SchemeStatusUpdate,
    SchemeSearchRequest,
    SchemeListResponse,
    SchemeResponse,
    TranslationStatusResponse,
    AuditHistoryResponse,
)
from app.services.scheme_service import SchemeService

router = APIRouter(prefix="/schemes", tags=["Schemes"])


# ── Helper: build service ──────────────────────────────────────────────────

def _svc(db: AsyncSession = Depends(get_db)) -> SchemeService:
    return SchemeService(db)


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=SchemeListResponse,
    summary="Search and list schemes",
    description="Full-text search + multi-filter + pagination. All parameters optional.",
)
async def list_schemes(
    query: str | None = Query(default=None, max_length=200, description="Text search"),
    category: str | None = Query(default=None),
    scheme_type: str | None = Query(default=None),
    application_mode: str | None = Query(default=None),
    state: str | None = Query(default=None),
    ministry: str | None = Query(default=None),
    is_featured: bool | None = Query(default=None),
    sort: str = Query(default="newest", description="newest|oldest|alphabetical|most_viewed|recently_updated"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    lang: str = Depends(get_language),
    svc: SchemeService = Depends(_svc),
) -> SchemeListResponse:
    from app.models.enums import SchemeCategoryEnum, SchemeTypeEnum, ApplicationModeEnum
    req = SchemeSearchRequest(
        query=query,
        category=SchemeCategoryEnum(category) if category else None,
        scheme_type=SchemeTypeEnum(scheme_type) if scheme_type else None,
        application_mode=ApplicationModeEnum(application_mode) if application_mode else None,
        state=state,
        ministry=ministry,
        is_featured=is_featured,
        is_active=True,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return await svc.search_schemes(req, lang=lang)


@router.get(
    "/featured",
    response_model=SchemeListResponse,
    summary="Get featured schemes",
)
async def get_featured(
    limit: int = Query(default=10, ge=1, le=50),
    lang: str = Depends(get_language),
    svc: SchemeService = Depends(_svc),
) -> SchemeListResponse:
    return await svc.get_featured_schemes(limit=limit, lang=lang)


@router.get(
    "/recent",
    response_model=SchemeListResponse,
    summary="Get recently added schemes",
)
async def get_recent(
    limit: int = Query(default=10, ge=1, le=50),
    lang: str = Depends(get_language),
    svc: SchemeService = Depends(_svc),
) -> SchemeListResponse:
    return await svc.get_recent_schemes(limit=limit, lang=lang)


@router.get(
    "/categories",
    summary="Get all scheme categories",
)
async def get_categories(svc: SchemeService = Depends(_svc)) -> dict:
    return await svc.get_categories()


@router.get(
    "/states",
    summary="Get all active scheme states",
)
async def get_states(svc: SchemeService = Depends(_svc)) -> dict:
    return await svc.get_states()


@router.get(
    "/code/{scheme_code}",
    response_model=SchemeResponse,
    summary="Get scheme by unique code",
)
async def get_by_code(
    scheme_code: str,
    lang: str = Depends(get_language),
    svc: SchemeService = Depends(_svc),
) -> SchemeResponse:
    return await svc.get_scheme_by_code(scheme_code, lang=lang)


@router.get(
    "/{scheme_id}",
    response_model=SchemeResponse,
    summary="Get scheme by ID",
)
async def get_scheme(
    scheme_id: uuid.UUID,
    lang: str = Depends(get_language),
    svc: SchemeService = Depends(_svc),
) -> SchemeResponse:
    return await svc.get_scheme_by_id(scheme_id, lang=lang)

@router.post(
    "/{scheme_id}/feedback",
    summary="Submit translation feedback for a scheme",
)
async def submit_feedback(
    scheme_id: uuid.UUID,
    is_helpful: bool,
    comment: str | None = None,
    lang: str = Depends(get_language),
    # current_user: User | None = Depends(get_current_active_user) # Optional for public feedback
    svc: SchemeService = Depends(_svc),
) -> dict:
    await svc.submit_translation_feedback(
        scheme_id=scheme_id,
        language_code=lang,
        is_helpful=is_helpful,
        comment=comment,
        user_id=None # current_user.id if current_user else None
    )
    return {"success": True, "message": "Feedback submitted successfully"}


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=SchemeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new scheme [Admin]",
    responses={
        409: {"description": "Duplicate scheme name or code"},
        422: {"description": "Validation error"},
    },
)
async def create_scheme(
    payload: SchemeCreate,
    current_user: User = Depends(require_admin),
    svc: SchemeService = Depends(_svc),
) -> SchemeResponse:
    return await svc.create_scheme(payload, created_by=current_user.id)


@router.put(
    "/{scheme_id}",
    response_model=SchemeResponse,
    summary="Update a scheme [Admin]",
)
async def update_scheme(
    scheme_id: uuid.UUID,
    payload: SchemeUpdate,
    current_user: User = Depends(require_admin),
    svc: SchemeService = Depends(_svc),
) -> SchemeResponse:
    return await svc.update_scheme(scheme_id, payload, updated_by=current_user.id)


@router.patch(
    "/{scheme_id}/status",
    response_model=SchemeResponse,
    summary="Activate or deactivate a scheme [Admin]",
)
async def update_status(
    scheme_id: uuid.UUID,
    payload: SchemeStatusUpdate,
    current_user: User = Depends(require_admin),
    svc: SchemeService = Depends(_svc),
) -> SchemeResponse:
    return await svc.update_status(scheme_id, payload, updated_by=current_user.id)


@router.patch(
    "/{scheme_id}/restore",
    response_model=SchemeResponse,
    summary="Restore a soft-deleted scheme [Admin]",
)
async def restore_scheme(
    scheme_id: uuid.UUID,
    _: User = Depends(require_admin),
    svc: SchemeService = Depends(_svc),
) -> SchemeResponse:
    return await svc.restore_scheme(scheme_id)


@router.delete(
    "/{scheme_id}",
    status_code=status.HTTP_200_OK,
    summary="Soft-delete a scheme [Admin]",
)
async def delete_scheme(
    scheme_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    svc: SchemeService = Depends(_svc),
) -> dict:
    return await svc.delete_scheme(scheme_id, deleted_by=current_user.id)


# ── Admin read-only detail routes ──────────────────────────────────────────

@router.get(
    "/{scheme_id}/translation-status",
    response_model=TranslationStatusResponse,
    summary="Get translation status for a scheme [Admin]",
    operation_id="get_scheme_translation_status",
)
async def get_translation_status(
    scheme_id: uuid.UUID,
    _: User = Depends(require_admin),
    svc: SchemeService = Depends(_svc),
) -> TranslationStatusResponse:
    return await svc.get_translation_status(scheme_id)


@router.get(
    "/{scheme_id}/audit-history",
    response_model=AuditHistoryResponse,
    summary="Get audit history for a scheme [Admin]",
    operation_id="get_scheme_audit_history",
)
async def get_audit_history(
    scheme_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    _: User = Depends(require_admin),
    svc: SchemeService = Depends(_svc),
) -> AuditHistoryResponse:
    return await svc.get_audit_history(scheme_id, limit=limit)


@router.patch(
    "/{scheme_id}/restore",
    response_model=SchemeResponse,
    summary="Restore a soft-deleted scheme [Admin]",
    operation_id="restore_scheme_admin",
)
async def restore_scheme(
    scheme_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    svc: SchemeService = Depends(_svc),
) -> SchemeResponse:
    return await svc.restore_scheme(scheme_id, restored_by=current_user.id)
