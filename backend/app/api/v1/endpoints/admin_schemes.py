"""
Admin Scheme Management Endpoints — Sahayak AI
===============================================
Admin-only routes for scheme lifecycle management.
All routes require admin or super_admin role.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.database.database import get_db
from app.models.user import User
from app.schemas.scheme import (
    AdminSchemeFilters,
    SchemeListResponse,
    SchemeResponse,
)
from app.services.scheme_service import SchemeService

router = APIRouter(prefix="/admin/schemes", tags=["Admin — Scheme Management"])


def _svc(db: AsyncSession = Depends(get_db)) -> SchemeService:
    return SchemeService(db)


@router.get(
    "",
    response_model=SchemeListResponse,
    summary="List all schemes (admin) — includes draft and archived",
    description=(
        "Returns ALL schemes regardless of active status. "
        "Pass is_active=true for published only, is_active=false for draft/archived only, "
        "or omit for all."
    ),
)
async def list_admin_schemes(
    query: str | None = Query(default=None, max_length=200),
    category: str | None = Query(default=None),
    scheme_type: str | None = Query(default=None),
    application_mode: str | None = Query(default=None),
    state: str | None = Query(default=None),
    ministry: str | None = Query(default=None),
    is_featured: bool | None = Query(default=None),
    is_active: bool | None = Query(default=None, description="None=all, true=published, false=draft/archived"),
    sort: str = Query(default="newest"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(require_admin),
    svc: SchemeService = Depends(_svc),
) -> SchemeListResponse:
    from app.models.enums import SchemeCategoryEnum, SchemeTypeEnum, ApplicationModeEnum
    filters = AdminSchemeFilters(
        query=query,
        category=SchemeCategoryEnum(category) if category else None,
        scheme_type=SchemeTypeEnum(scheme_type) if scheme_type else None,
        application_mode=ApplicationModeEnum(application_mode) if application_mode else None,
        state=state,
        ministry=ministry,
        is_featured=is_featured,
        is_active=is_active,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return await svc.get_admin_schemes(filters)


@router.get(
    "/{scheme_id}",
    response_model=SchemeResponse,
    summary="Get a specific scheme (admin) — includes inactive",
)
async def get_admin_scheme(
    scheme_id_or_str: str,
    _: User = Depends(require_admin),
    svc: SchemeService = Depends(_svc),
) -> SchemeResponse:
    import uuid as _uuid
    try:
        scheme_id = _uuid.UUID(scheme_id_or_str)
    except ValueError:
        from app.core.exceptions import SchemeNotFoundException
        raise SchemeNotFoundException()
    return await svc.get_scheme_by_id_admin(scheme_id)
