"""
Admin Translation Endpoints — Sahayak AI
==========================================
APIs for triggering and monitoring translation jobs.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.auth.dependencies import require_admin
from app.database.database import get_db
from app.services.translation.translation_service import TranslationService
from app.services.translation.indictrans2_provider import IndicTrans2Provider
from app.services.translation.nllb_provider import NLLBProvider
from app.models.translation_job import TranslationJob
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/admin/translations", tags=["Admin Translations"])

def _svc(db: AsyncSession = Depends(get_db)) -> TranslationService:
    if settings.TRANSLATION_PROVIDER.lower() == "nllb":
        provider = NLLBProvider()
    else:
        provider = IndicTrans2Provider()
    return TranslationService(db, provider)


class HardwareStatusResponse(BaseModel):
    provider_name: str
    model_name: str | None
    device: str | None
    batch_size: int | None
    gpu_memory_mb: float | None

@router.get(
    "/hardware-status",
    response_model=HardwareStatusResponse,
    summary="Get translation hardware metrics"
)
async def get_hardware_status(
    current_user: User = Depends(require_admin),
    svc: TranslationService = Depends(_svc),
) -> HardwareStatusResponse:
    provider = svc.provider
    return HardwareStatusResponse(
        provider_name=provider.provider_name,
        model_name=getattr(provider, "_model_name", None),
        device=getattr(provider, "_device", None),
        batch_size=getattr(provider, "_batch_size", None),
        gpu_memory_mb=getattr(provider, "memory_usage_mb", None)
    )

class JobResponse(BaseModel):
    id: uuid.UUID
    job_type: str
    status: str
    total_records: int
    processed_records: int
    failed_records: int
    current_batch: int
    estimated_remaining: int | None
    logs: list[Any] | None

@router.post(
    "/pilot",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start pilot translation job",
    description="Triggers async translation of 100 schemes.",
)
async def start_pilot_job(
    current_user: User = Depends(require_admin),
    svc: TranslationService = Depends(_svc),
) -> dict:
    job = await svc.start_pilot_job(limit=100)
    return {
        "message": "Pilot translation job started.",
        "job_id": str(job.id)
    }

@router.get(
    "/jobs/latest",
    response_model=JobResponse,
    summary="Get the latest translation job status",
)
async def get_latest_job(
    current_user: User = Depends(require_admin),
    svc: TranslationService = Depends(_svc),
) -> JobResponse:
    job = await svc.job_repo.get_latest_job()
    if not job:
        raise HTTPException(status_code=404, detail="No translation jobs found.")
    
    return JobResponse(
        id=job.id,
        job_type=job.job_type,
        status=job.status.value,
        total_records=job.total_records,
        processed_records=job.processed_records,
        failed_records=job.failed_records,
        current_batch=job.current_batch,
        estimated_remaining=job.estimated_remaining,
        logs=job.logs
    )

@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    summary="Get translation job status",
)
async def get_job_status(
    job_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    svc: TranslationService = Depends(_svc),
) -> JobResponse:
    job = await svc.job_repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
        
    return JobResponse(
        id=job.id,
        job_type=job.job_type,
        status=job.status.value,
        total_records=job.total_records,
        processed_records=job.processed_records,
        failed_records=job.failed_records,
        current_batch=job.current_batch,
        estimated_remaining=job.estimated_remaining,
        logs=job.logs
    )
