"""
Government Import Admin Endpoints — Sahayak AI
================================================
POST   /api/v1/admin/government/import
POST   /api/v1/admin/government/import/preview
GET    /api/v1/admin/government/import/status
GET    /api/v1/admin/government/import/history
GET    /api/v1/admin/government/import/report/{import_id}
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.database.database import get_db
from app.models.user import User
from app.schemas.import_schema import (
    ImportRequest, ImportResponse,
    PreviewRequest, PreviewResponse,
    ImportStatusResponse, ImportHistoryResponse,
)
from app.services.import_service import GovernmentImportService
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/admin/government", tags=["Government Import"])


def _svc(db: AsyncSession = Depends(get_db)) -> GovernmentImportService:
    return GovernmentImportService(db)


@router.post(
    "/import",
    response_model=ImportResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger government scheme import [Admin]",
)
async def trigger_import(
    payload: ImportRequest,
    _: User = Depends(require_admin),
    svc: GovernmentImportService = Depends(_svc),
) -> ImportResponse:
    report = await svc.run_import(
        resource_id=payload.resource_id,
        mode=payload.mode,
        max_records=payload.max_records,
        dry_run=payload.dry_run,
    )
    return ImportResponse(
        message=f"Import {report.status}. Created={report.statistics.created} Updated={report.statistics.updated}",
        report=report,
    )


@router.post(
    "/import/preview",
    response_model=PreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Preview import without saving [Admin]",
)
async def preview_import(
    payload: PreviewRequest,
    _: User = Depends(require_admin),
    svc: GovernmentImportService = Depends(_svc),
) -> PreviewResponse:
    preview = await svc.preview(payload.resource_id, limit=payload.limit)
    return PreviewResponse(preview=preview)


@router.get(
    "/import/status",
    response_model=ImportStatusResponse,
    summary="Get current import status [Admin]",
)
async def import_status(
    _: User = Depends(require_admin),
) -> ImportStatusResponse:
    s = GovernmentImportService.get_status()
    return ImportStatusResponse(
        is_running=s["is_running"],
        current_import=s["current_import"],
    )


@router.get(
    "/import/history",
    response_model=ImportHistoryResponse,
    summary="Get import history [Admin]",
)
async def import_history(
    _: User = Depends(require_admin),
) -> ImportHistoryResponse:
    history = GovernmentImportService.get_history()
    return ImportHistoryResponse(data=history, total=len(history))


@router.get(
    "/import/report/{import_id}",
    response_model=ImportResponse,
    summary="Get detailed import report [Admin]",
)
async def import_report(
    import_id: str,
    _: User = Depends(require_admin),
) -> ImportResponse:
    report = GovernmentImportService.get_report(import_id)
    if not report:
        raise NotFoundException(f"Import report '{import_id}' not found.")
    return ImportResponse(report=report)
