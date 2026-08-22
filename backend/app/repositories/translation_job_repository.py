"""
Translation Job Repository — Sahayak AI
=======================================
Data access layer for TranslationJob.
"""

import uuid
from typing import Sequence
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.translation_job import TranslationJob
from app.models.enums import TranslationJobStatusEnum

class TranslationJobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, job_type: str, total_records: int) -> TranslationJob:
        job = TranslationJob(
            job_type=job_type,
            total_records=total_records,
            status=TranslationJobStatusEnum.PENDING,
            started_at=datetime.now(timezone.utc),
            logs=[]
        )
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get(self, job_id: uuid.UUID) -> TranslationJob | None:
        stmt = select(TranslationJob).where(TranslationJob.id == job_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_latest_job(self) -> TranslationJob | None:
        stmt = select(TranslationJob).order_by(TranslationJob.created_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_status(self, job_id: uuid.UUID, status: TranslationJobStatusEnum) -> TranslationJob | None:
        job = await self.get(job_id)
        if job:
            job.status = status
            if status in [TranslationJobStatusEnum.COMPLETED, TranslationJobStatusEnum.FAILED, TranslationJobStatusEnum.CANCELLED]:
                job.finished_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(job)
        return job

    async def increment_progress(self, job_id: uuid.UUID, success_count: int, failed_count: int, current_batch: int) -> None:
        job = await self.get(job_id)
        if job:
            job.processed_records += success_count
            job.failed_records += failed_count
            job.current_batch = current_batch
            
            # Simple estimated remaining calculation (could be improved)
            if job.processed_records > 0 and job.started_at:
                elapsed = (datetime.now(timezone.utc) - job.started_at).total_seconds()
                avg_time_per_record = elapsed / (job.processed_records + job.failed_records)
                remaining = job.total_records - (job.processed_records + job.failed_records)
                job.estimated_remaining = int(remaining * avg_time_per_record)
                
            await self.session.commit()

    async def append_log(self, job_id: uuid.UUID, message: str, level: str = "info") -> None:
        job = await self.get(job_id)
        if job:
            if job.logs is None:
                job.logs = []
            
            # Create a new list and assign it back so SQLAlchemy detects the change
            current_logs = list(job.logs)
            current_logs.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": level,
                "message": message
            })
            job.logs = current_logs
            await self.session.commit()
