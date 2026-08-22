"""
Translation Service — Sahayak AI
==================================
Core service handling job execution, batching, checksums, and versioning.
"""

import hashlib
import json
import uuid
from typing import Dict, Any, List
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.scheme import Scheme
from app.models.translation import SchemeTranslation
from app.models.translation_job import TranslationJob
from app.models.enums import TranslationJobStatusEnum, TranslationStatusEnum, LanguageEnum
from app.repositories.translation_repository import TranslationRepository
from app.repositories.translation_job_repository import TranslationJobRepository
from app.services.translation.provider import TranslationProvider

def _calculate_checksum(data: Dict[str, Any]) -> str:
    """Generate SHA256 checksum from a stable JSON representation."""
    stable_json = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(stable_json.encode('utf-8')).hexdigest()

def _extract_translation_fields(scheme: Scheme) -> Dict[str, Any]:
    """Extract standard text fields to translate from Scheme model."""
    return {
        "name": scheme.name or "",
        "short_description": scheme.short_description or "",
        "full_description": scheme.full_description or "",
        "benefits": scheme.benefits or "",
        # Adding empty placeholders for the ones missing from original Scheme table
        "eligibility": "",
        "application_process": "",
        "required_documents": "",
        "faq": ""
    }

class TranslationService:
    def __init__(self, session: AsyncSession, provider: TranslationProvider):
        self.session = session
        self.provider = provider
        self.trans_repo = TranslationRepository(session)
        self.job_repo = TranslationJobRepository(session)
        self.supported_langs = [lang.value for lang in LanguageEnum if lang != LanguageEnum.ENGLISH]

    async def start_pilot_job(self, limit: int = 100) -> TranslationJob:
        """Start a pilot translation job asynchronously."""
        # 1. Query English schemes
        stmt = select(Scheme).where(Scheme.is_active == True).limit(limit)
        result = await self.session.execute(stmt)
        schemes = list(result.scalars().all())

        total_records = len(schemes) * len(self.supported_langs)
        
        job = await self.job_repo.create("pilot_translation", total_records)
        await self.job_repo.append_log(job.id, f"Started pilot job for {len(schemes)} schemes across {len(self.supported_langs)} languages.")

        # Trigger background processing
        asyncio.create_task(self._process_job(job.id, schemes))
        return job

    async def _process_job(self, job_id: uuid.UUID, schemes: List[Scheme]) -> None:
        """Background processor for handling batch translations per job."""
        import time
        try:
            batch_size = int(settings.TRANSLATION_BATCH_SIZE) if hasattr(settings, "TRANSLATION_BATCH_SIZE") else 16
            max_retries = int(settings.TRANSLATION_MAX_RETRIES) if hasattr(settings, "TRANSLATION_MAX_RETRIES") else 3
            
            await self.job_repo.update_status(job_id, TranslationJobStatusEnum.RUNNING)
            
            total_schemes = len(schemes)
            
            for i in range(0, total_schemes, batch_size):
                batch_schemes = schemes[i:i + batch_size]
                
                # Check job status before processing batch
                job = await self.job_repo.get(job_id)
                if job and job.status in [TranslationJobStatusEnum.PAUSED, TranslationJobStatusEnum.CANCELLED]:
                    await self.job_repo.append_log(job_id, f"Job stopped. Status: {job.status.value}")
                    return

                success_count = 0
                failed_count = 0
                
                batch_start_time = time.time()

                for scheme in batch_schemes:
                    original_data = _extract_translation_fields(scheme)
                    checksum = _calculate_checksum(original_data)

                    for target_lang in self.supported_langs:
                        for attempt in range(max_retries):
                            try:
                                # 1. Cache Check
                                existing = await self.trans_repo.get_by_scheme_and_lang(scheme.id, target_lang)
                                if existing and existing.checksum == checksum:
                                    success_count += 1
                                    break # Skip, already translated and up-to-date
                                    
                                # 2. Translate
                                translated_json = await self.provider.translate_json(
                                    original_data, 
                                    source_lang="en", 
                                    target_lang=target_lang
                                )
                                
                                if existing:
                                    # Update existing version
                                    existing.translated_content = translated_json
                                    existing.checksum = checksum
                                    existing.version += 1
                                    existing.status = TranslationStatusEnum.TRANSLATED
                                    await self.trans_repo.update(existing)
                                else:
                                    # Create new
                                    new_trans = SchemeTranslation(
                                        scheme_id=scheme.id,
                                        language_code=target_lang,
                                        translated_content=translated_json,
                                        version=1,
                                        checksum=checksum,
                                        provider=self.provider.provider_name,
                                        status=TranslationStatusEnum.TRANSLATED
                                    )
                                    await self.trans_repo.create(new_trans)
                                    
                                success_count += 1
                                break # Success, break retry loop
                                
                            except Exception as e:
                                if attempt == max_retries - 1:
                                    await self.job_repo.append_log(job_id, f"Failed translating scheme {scheme.id} to {target_lang} after {max_retries} attempts: {str(e)}", "error")
                                    failed_count += 1
                                else:
                                    await asyncio.sleep(1) # short backoff

                # Update progress after batch
                current_batch = (i // batch_size) + 1
                batch_duration = time.time() - batch_start_time
                
                memory_info = ""
                if hasattr(self.provider, 'memory_usage_mb'):
                    mem = self.provider.memory_usage_mb
                    if mem > 0:
                        memory_info = f" | GPU Mem: {mem:.1f} MB"
                
                speed = len(batch_schemes) * len(self.supported_langs) / batch_duration if batch_duration > 0 else 0
                await self.job_repo.increment_progress(job_id, success_count, failed_count, current_batch)
                await self.job_repo.append_log(
                    job_id, 
                    f"Completed batch {current_batch} | Duration: {batch_duration:.2f}s | Speed: {speed:.2f} items/s{memory_info}"
                )

            # Job finished
            await self.job_repo.update_status(job_id, TranslationJobStatusEnum.COMPLETED)
            await self.job_repo.append_log(job_id, "Job completed successfully.")
            
        except Exception as e:
            await self.job_repo.append_log(job_id, f"Fatal Job Error: {str(e)}", "error")
            await self.job_repo.update_status(job_id, TranslationJobStatusEnum.FAILED)
