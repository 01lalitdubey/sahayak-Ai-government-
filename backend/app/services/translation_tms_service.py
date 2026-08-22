import uuid
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.translation import SchemeTranslation
from app.models.translation_history import TranslationHistory
from app.models.translation_feedback import TranslationFeedback
from app.models.scheme import Scheme
from app.models.enums import TranslationStatusEnum
from app.schemas.translation_tms import TranslationEditRequest, TranslationReviewRequest

class TranslationTMSService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_translations(
        self,
        page: int = 1,
        size: int = 50,
        status: Optional[TranslationStatusEnum] = None,
        language: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[SchemeTranslation], int]:
        
        query = select(SchemeTranslation).options(selectinload(SchemeTranslation.scheme))
        
        if status:
            query = query.where(SchemeTranslation.status == status)
        if language:
            query = query.where(SchemeTranslation.language_code == language)
        if search:
            # We can search in translated content or scheme name (requires join)
            query = query.join(Scheme).where(
                or_(
                    Scheme.name.ilike(f"%{search}%"),
                    # Add more robust JSON search if needed
                )
            )
            
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Pagination
        query = query.order_by(SchemeTranslation.updated_at.desc()).offset((page - 1) * size).limit(size)
        
        result = await self.db.execute(query)
        items = list(result.scalars().all())
        
        return items, total or 0

    async def get_translation(self, translation_id: uuid.UUID) -> Optional[SchemeTranslation]:
        query = select(SchemeTranslation).where(SchemeTranslation.id == translation_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
        
    async def get_translation_history(self, translation_id: uuid.UUID) -> List[TranslationHistory]:
        query = select(TranslationHistory).where(TranslationHistory.translation_id == translation_id).order_by(TranslationHistory.version.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_translation(self, translation_id: uuid.UUID, editor_id: uuid.UUID, req: TranslationEditRequest) -> SchemeTranslation:
        trans = await self.get_translation(translation_id)
        if not trans:
            raise ValueError("Translation not found")

        # Create history snapshot BEFORE updating
        history = TranslationHistory(
            translation_id=trans.id,
            version=trans.version,
            translated_content=trans.translated_content,
            editor_id=editor_id,
            reason=req.reason or "Manual edit"
        )
        self.db.add(history)

        # Update translation
        trans.translated_content = req.translated_content
        trans.version += 1
        trans.manual_override = True
        trans.last_editor = editor_id
        
        # If it was published, and it's edited, what happens? 
        # Usually it stays published but version bumps, or requires re-review. Let's keep it simple: just bump version.
        
        await self.db.commit()
        await self.db.refresh(trans)
        return trans

    async def approve_translation(self, translation_id: uuid.UUID, reviewer_id: uuid.UUID, req: TranslationReviewRequest) -> SchemeTranslation:
        trans = await self.get_translation(translation_id)
        if not trans:
            raise ValueError("Translation not found")
            
        trans.status = TranslationStatusEnum.APPROVED
        trans.review_status = TranslationStatusEnum.APPROVED
        trans.approved_by = reviewer_id
        trans.last_reviewer = reviewer_id
        trans.reviewed_at = datetime.now(timezone.utc)
        trans.approved_version = trans.version
        
        if req.comment:
            trans.review_comment = req.comment
            
        await self.db.commit()
        await self.db.refresh(trans)
        return trans

    async def reject_translation(self, translation_id: uuid.UUID, reviewer_id: uuid.UUID, req: TranslationReviewRequest) -> SchemeTranslation:
        trans = await self.get_translation(translation_id)
        if not trans:
            raise ValueError("Translation not found")
            
        trans.status = TranslationStatusEnum.REJECTED
        trans.review_status = TranslationStatusEnum.REJECTED
        trans.last_reviewer = reviewer_id
        trans.reviewed_at = datetime.now(timezone.utc)
        
        if req.comment:
            trans.review_comment = req.comment
            
        await self.db.commit()
        await self.db.refresh(trans)
        return trans

    async def publish_translation(self, translation_id: uuid.UUID) -> SchemeTranslation:
        trans = await self.get_translation(translation_id)
        if not trans:
            raise ValueError("Translation not found")
            
        if trans.status != TranslationStatusEnum.APPROVED:
            raise ValueError("Only APPROVED translations can be published")
            
        trans.status = TranslationStatusEnum.PUBLISHED
        trans.is_published = True
        trans.published_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(trans)
        return trans
        
    async def get_analytics(self) -> dict:
        # Get translation status counts
        status_query = select(SchemeTranslation.status, func.count()).group_by(SchemeTranslation.status)
        status_res = await self.db.execute(status_query)
        status_counts = {status.value: count for status, count in status_res.all()}
        
        # Get total schemes active
        scheme_count_query = select(func.count(Scheme.id)).where(Scheme.is_active == True)
        total_schemes = await self.db.scalar(scheme_count_query) or 0
        
        # The number of target languages is 11 (12 total - 1 English).
        total_expected_translations = total_schemes * 11
        total_translations = sum(status_counts.values())
        
        coverage = (total_translations / total_expected_translations * 100) if total_expected_translations > 0 else 0
        
        return {
            "total_schemes": total_schemes,
            "total_translations": total_translations,
            "pending_review": status_counts.get("pending_review", 0),
            "approved": status_counts.get("approved", 0),
            "published": status_counts.get("published", 0),
            "rejected": status_counts.get("rejected", 0),
            "coverage_percentage": round(coverage, 2)
        }
