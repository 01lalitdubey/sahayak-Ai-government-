from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.models.enums import UserRole, TranslationStatusEnum
from app.schemas.translation_tms import (
    TranslationTMSDetail,
    TranslationTMSListResponse,
    TranslationEditRequest,
    TranslationReviewRequest,
    BulkActionRequest,
    TranslationAnalyticsResponse,
    TranslationHistoryResponse
)
from app.services.translation_tms_service import TranslationTMSService
from app.auth.dependencies import require_admin
from app.models.user import User

router = APIRouter(prefix="/admin/tms", tags=["admin_tms"])

@router.get("/translations", response_model=TranslationTMSListResponse)
async def list_translations(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status: Optional[TranslationStatusEnum] = None,
    language: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    svc = TranslationTMSService(db)
    items, total = await svc.list_translations(page, size, status, language, search)
    
    # Map to schema manually due to relationship
    results = []
    for item in items:
        detail = TranslationTMSDetail.model_validate(item)
        if item.scheme:
            detail.scheme_name = item.scheme.name
            # Optional: fetch original english if needed here, but usually skipped in list for perf
        results.append(detail)
        
    return TranslationTMSListResponse(items=results, total=total, page=page, size=size)

@router.get("/translations/analytics", response_model=TranslationAnalyticsResponse)
async def get_analytics(db: AsyncSession = Depends(get_db)):
    svc = TranslationTMSService(db)
    stats = await svc.get_analytics()
    return TranslationAnalyticsResponse(**stats)

@router.get("/translations/{id}", response_model=TranslationTMSDetail)
async def get_translation_detail(id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = TranslationTMSService(db)
    item = await svc.get_translation(id)
    if not item:
        raise HTTPException(status_code=404, detail="Translation not found")
        
    detail = TranslationTMSDetail.model_validate(item)
    
    # Get history
    history = await svc.get_translation_history(id)
    detail.history = [TranslationHistoryResponse.model_validate(h) for h in history]
    
    return detail

@router.put("/translations/{id}", response_model=TranslationTMSDetail)
async def edit_translation(
    id: uuid.UUID, 
    req: TranslationEditRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    svc = TranslationTMSService(db)
    try:
        item = await svc.update_translation(id, current_user.id, req)
        return TranslationTMSDetail.model_validate(item)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/translations/{id}/approve", response_model=TranslationTMSDetail)
async def approve_translation(
    id: uuid.UUID,
    req: TranslationReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    svc = TranslationTMSService(db)
    try:
        item = await svc.approve_translation(id, current_user.id, req)
        return TranslationTMSDetail.model_validate(item)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/translations/{id}/reject", response_model=TranslationTMSDetail)
async def reject_translation(
    id: uuid.UUID,
    req: TranslationReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    svc = TranslationTMSService(db)
    try:
        item = await svc.reject_translation(id, current_user.id, req)
        return TranslationTMSDetail.model_validate(item)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/translations/{id}/publish", response_model=TranslationTMSDetail)
async def publish_translation(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    svc = TranslationTMSService(db)
    try:
        item = await svc.publish_translation(id)
        return TranslationTMSDetail.model_validate(item)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/translations/bulk-approve")
async def bulk_approve(
    req: BulkActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    svc = TranslationTMSService(db)
    for t_id in req.translation_ids:
        try:
            await svc.approve_translation(t_id, current_user.id, TranslationReviewRequest(comment="Bulk Approved"))
        except ValueError:
            pass # Skip invalid
    return {"status": "success", "processed": len(req.translation_ids)}

@router.post("/translations/bulk-publish")
async def bulk_publish(
    req: BulkActionRequest,
    db: AsyncSession = Depends(get_db)
):
    svc = TranslationTMSService(db)
    for t_id in req.translation_ids:
        try:
            await svc.publish_translation(t_id)
        except ValueError:
            pass
    return {"status": "success", "processed": len(req.translation_ids)}

# ── Execution Pipeline Endpoints ──────────────────────────────────────────────

from app.services.translation.queue_manager import queue_manager
from app.services.translation.executor import TranslationExecutor
from app.services.translation.indictrans2_provider import IndicTrans2Provider

# Dependency to get executor
def get_executor():
    # In production, we'd inject this cleanly, but here we can instantiate it
    return TranslationExecutor(provider=IndicTrans2Provider())

@router.post("/execution/start-all")
async def start_all(
    current_user: User = Depends(require_admin),
    executor: TranslationExecutor = Depends(get_executor)
):
    try:
        job_id = await executor.initialize_and_start()
        return {"status": "started", "job_id": str(job_id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/execution/pause")
async def pause_execution(current_user: User = Depends(require_admin)):
    queue_manager.pause()
    return {"status": "paused"}

@router.post("/execution/resume")
async def resume_execution(current_user: User = Depends(require_admin)):
    queue_manager.resume()
    return {"status": "resumed"}

@router.post("/execution/cancel")
async def cancel_execution(current_user: User = Depends(require_admin)):
    queue_manager.cancel()
    return {"status": "cancelled"}

@router.post("/execution/retry-failed")
async def retry_failed(
    job_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    executor: TranslationExecutor = Depends(get_executor)
):
    try:
        await executor.resume_job(job_id)
        return {"status": "retrying"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/execution/progress")
async def get_progress(current_user: User = Depends(require_admin)):
    state = queue_manager.state
    return {
        "job_id": str(state.job_id) if state.job_id else None,
        "status": state.status.value,
        "total_records": state.total_records,
        "processed_records": state.processed_records,
        "failed_records": state.failed_records,
        "speed": state.get_speed(),
        "eta_seconds": state.get_eta(),
        "queue_size": state.queue.qsize(),
        "active_workers": len([w for w in state.workers if not w.done()]),
        "current_languages": list(state.current_languages)
    }

@router.get("/execution/health")
async def get_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    svc = TranslationTMSService(db)
    stats = await svc.get_analytics()
    # Adding queue errors
    stats["recent_errors"] = queue_manager.state.errors[-10:] # last 10 errors
    return stats

@router.get("/execution/report")
async def get_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    from fastapi.responses import StreamingResponse
    import csv
    import io
    from sqlalchemy import select
    from app.models.translation import SchemeTranslation
    from app.models.scheme import Scheme
    
    async def iter_csv():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Scheme_ID", "Scheme_Name", "Language", "Status", "Review_Status", "Quality", "Version"])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)
        
        stmt = select(SchemeTranslation, Scheme.name).join(Scheme, SchemeTranslation.scheme_id == Scheme.id)
        result = await db.stream(stmt)
        
        async for row in result:
            trans, s_name = row
            writer.writerow([
                str(trans.scheme_id), 
                s_name, 
                trans.language_code, 
                trans.status.value, 
                trans.review_status.value if trans.review_status else "",
                trans.translation_quality or "",
                trans.version
            ])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    return StreamingResponse(iter_csv(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=translation_report.csv"})
