import asyncio
import logging
import time
import traceback
from typing import List

from sqlalchemy import select, func, distinct
from sqlalchemy.orm import selectinload

from app.database.database import get_db, AsyncSessionLocal
from app.models.scheme import Scheme
from app.models.translation import SchemeTranslation
from app.models.translation_job import TranslationJob
from app.models.enums import LanguageEnum, TranslationJobStatusEnum, TranslationStatusEnum
from app.services.translation.queue_manager import queue_manager
from app.services.translation.provider import TranslationProvider
from app.services.translation.translation_service import _extract_translation_fields, _calculate_checksum

logger = logging.getLogger(__name__)

class TranslationExecutor:
    def __init__(self, provider: TranslationProvider, worker_count: int = 4):
        self.provider = provider
        self.worker_count = worker_count
        self.target_languages = [lang.value for lang in LanguageEnum if lang != LanguageEnum.ENGLISH and lang != LanguageEnum.URDU]
        # Added URDU to skip as requested per Indian languages requirement context

    async def initialize_and_start(self):
        """Initializes a full run across all active schemes and starts workers."""
        if queue_manager.is_running():
            raise ValueError("A translation job is already running.")

        # Reset Queue
        queue_manager.reset()
        
        async with AsyncSessionLocal() as session:
            # 1. Fetch all active schemes
            stmt = select(Scheme.id).where(Scheme.is_active == True)
            result = await session.execute(stmt)
            scheme_ids = result.scalars().all()

            # Create TranslationJob DB record
            total_records = len(scheme_ids) * len(self.target_languages)
            
            job = TranslationJob(
                job_type="full_translation",
                status=TranslationJobStatusEnum.RUNNING,
                total_records=total_records,
                started_at=func.now()
            )
            session.add(job)
            await session.commit()
            await session.refresh(job)

            # 2. Populate Queue
            queue_manager.state.job_id = job.id
            queue_manager.state.status = TranslationJobStatusEnum.RUNNING
            queue_manager.state.start_time = time.time()
            queue_manager.state.total_records = total_records

            # To avoid loading 50k items in memory, we push tuples of (scheme_id, lang)
            for sid in scheme_ids:
                for lang in self.target_languages:
                    await queue_manager.state.queue.put((sid, lang))

        # Start Workers
        self._start_workers()
        return job.id

    async def enqueue_scheme(self, scheme_id):
        """Enqueues a single scheme for translation across target languages."""
        async with AsyncSessionLocal() as session:
            total_new_records = len(self.target_languages)
            
            if not queue_manager.is_running():
                queue_manager.reset()
                job = TranslationJob(
                    job_type="single_translation",
                    status=TranslationJobStatusEnum.RUNNING,
                    total_records=total_new_records,
                    started_at=func.now()
                )
                session.add(job)
                await session.commit()
                await session.refresh(job)
                
                queue_manager.state.job_id = job.id
                queue_manager.state.status = TranslationJobStatusEnum.RUNNING
                queue_manager.state.start_time = time.time()
                queue_manager.state.total_records = total_new_records
            else:
                queue_manager.state.total_records += total_new_records
                if queue_manager.state.job_id:
                    job = await session.get(TranslationJob, queue_manager.state.job_id)
                    if job:
                        job.total_records = queue_manager.state.total_records
                        await session.commit()

            for lang in self.target_languages:
                await queue_manager.state.queue.put((scheme_id, lang))

            active_workers = [w for w in queue_manager.state.workers if not w.done()]
            if not active_workers:
                self._start_workers()
            
            return queue_manager.state.job_id

    def _start_workers(self):
        queue_manager.state.workers = []
        for i in range(self.worker_count):
            task = asyncio.create_task(self._worker_loop(i))
            queue_manager.state.workers.append(task)

    async def _worker_loop(self, worker_id: int):
        logger.info(f"Worker {worker_id} started.")
        while True:
            # Check pause state
            while queue_manager.state.status == TranslationJobStatusEnum.PAUSED:
                await asyncio.sleep(1)

            if queue_manager.state.status == TranslationJobStatusEnum.CANCELLED:
                break

            try:
                task = await queue_manager.state.queue.get()
            except asyncio.QueueEmpty:
                break
            except asyncio.CancelledError:
                break

            scheme_id, lang = task
            queue_manager.state.current_languages.add(lang)
            
            try:
                await self._process_single_translation(scheme_id, lang)
                queue_manager.state.processed_records += 1
            except Exception as e:
                logger.error(f"Worker {worker_id} failed on {scheme_id} to {lang}: {str(e)}")
                queue_manager.state.failed_records += 1
                queue_manager.state.errors.append({
                    "scheme_id": str(scheme_id),
                    "language": lang,
                    "error": str(e),
                    "timestamp": time.time()
                })
            finally:
                queue_manager.state.queue.task_done()
                
            # Periodic DB sync of progress (could be optimized)
            if queue_manager.state.processed_records % 50 == 0:
                await self._sync_job_progress()

        logger.info(f"Worker {worker_id} finished.")
        # If all workers are done and queue is empty, mark job complete
        if queue_manager.state.queue.empty():
            all_done = all(w.done() for w in queue_manager.state.workers if w != asyncio.current_task())
            if all_done:
                queue_manager.state.status = TranslationJobStatusEnum.COMPLETED
                await self._sync_job_progress()

    async def _process_single_translation(self, scheme_id, lang):
        async with AsyncSessionLocal() as session:
            # 1. Load scheme
            scheme = await session.get(Scheme, scheme_id)
            if not scheme:
                raise ValueError("Scheme not found")

            original_data = _extract_translation_fields(scheme)
            checksum = _calculate_checksum(original_data)

            # 2. Check existing translation
            stmt = select(SchemeTranslation).where(
                SchemeTranslation.scheme_id == scheme_id,
                SchemeTranslation.language_code == lang
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Skip if already published or approved
                if existing.is_published or existing.status in [TranslationStatusEnum.PUBLISHED, TranslationStatusEnum.APPROVED]:
                    return
                # Skip if checksum matches
                if existing.checksum == checksum:
                    return

            # 3. Translate
            translated_json = await self.provider.translate_json(
                original_data, 
                source_lang="en", 
                target_lang=lang
            )

            # 4. Validate
            if not translated_json or not any(translated_json.values()):
                raise ValueError("Empty translation output")

            if existing:
                existing.translated_content = translated_json
                existing.checksum = checksum
                existing.version += 1
                existing.status = TranslationStatusEnum.TRANSLATED
                existing.review_status = TranslationStatusEnum.PENDING_REVIEW
                session.add(existing)
            else:
                new_trans = SchemeTranslation(
                    scheme_id=scheme_id,
                    language_code=lang,
                    translated_content=translated_json,
                    version=1,
                    checksum=checksum,
                    provider=self.provider.provider_name,
                    status=TranslationStatusEnum.TRANSLATED,
                    review_status=TranslationStatusEnum.PENDING_REVIEW
                )
                session.add(new_trans)
                
            await session.commit()

    async def _sync_job_progress(self):
        if not queue_manager.state.job_id:
            return
        try:
            async with AsyncSessionLocal() as session:
                job = await session.get(TranslationJob, queue_manager.state.job_id)
                if job:
                    job.processed_records = queue_manager.state.processed_records
                    job.failed_records = queue_manager.state.failed_records
                    job.status = queue_manager.state.status
                    job.estimated_remaining = int(queue_manager.state.get_eta())
                    if queue_manager.state.status in [TranslationJobStatusEnum.COMPLETED, TranslationJobStatusEnum.CANCELLED]:
                        job.finished_at = func.now()
                    await session.commit()
        except Exception as e:
            logger.error(f"Failed to sync job progress: {e}")

    async def resume_job(self, job_id):
        if queue_manager.is_running():
            raise ValueError("A translation job is already running.")

        async with AsyncSessionLocal() as session:
            job = await session.get(TranslationJob, job_id)
            if not job:
                raise ValueError("Job not found")
            
            queue_manager.reset()
            queue_manager.state.job_id = job.id
            queue_manager.state.status = TranslationJobStatusEnum.RUNNING
            queue_manager.state.start_time = time.time()
            queue_manager.state.total_records = job.total_records
            queue_manager.state.processed_records = job.processed_records
            queue_manager.state.failed_records = job.failed_records
            
            # Fetch all active schemes
            stmt = select(Scheme.id).where(Scheme.is_active == True)
            result = await session.execute(stmt)
            scheme_ids = result.scalars().all()
            
            # To resume safely, we enqueue all remaining, and the worker's `_process_single_translation` 
            # already skips existing/matching translations safely. This avoids complex SQL anti-joins.
            for sid in scheme_ids:
                for lang in self.target_languages:
                    await queue_manager.state.queue.put((sid, lang))
                    
        self._start_workers()
