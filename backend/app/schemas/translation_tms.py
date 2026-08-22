"""
Translation TMS Schemas — Sahayak AI
====================================
Pydantic schemas for the Translation Management System.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TranslationStatusEnum

class TranslationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class TranslationHistoryResponse(BaseModel):
    id: UUID
    translation_id: UUID
    version: int
    translated_content: Dict[str, Any]
    editor_id: Optional[UUID] = None
    reason: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TranslationTMSDetail(TranslationBase):
    id: UUID
    scheme_id: UUID
    language_code: str
    translated_content: Dict[str, Any]
    version: int
    checksum: str
    translation_quality: Optional[int] = None
    provider: str
    status: TranslationStatusEnum
    
    # TMS extensions
    review_status: Optional[TranslationStatusEnum] = None
    approved_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    review_comment: Optional[str] = None
    last_editor: Optional[UUID] = None
    last_reviewer: Optional[UUID] = None
    manual_override: bool
    is_published: bool
    approved_version: Optional[int] = None
    
    created_at: datetime
    updated_at: datetime

    # For the frontend comparison
    original_english: Optional[Dict[str, Any]] = None
    scheme_name: Optional[str] = None
    history: Optional[List[TranslationHistoryResponse]] = None

class TranslationTMSListResponse(BaseModel):
    items: List[TranslationTMSDetail]
    total: int
    page: int
    size: int

class TranslationEditRequest(BaseModel):
    translated_content: Dict[str, Any]
    reason: Optional[str] = None

class TranslationReviewRequest(BaseModel):
    comment: Optional[str] = None

class BulkActionRequest(BaseModel):
    translation_ids: List[UUID]

class TranslationAnalyticsResponse(BaseModel):
    total_schemes: int
    total_translations: int
    pending_review: int
    approved: int
    published: int
    rejected: int
    coverage_percentage: float

class TranslationFeedbackBase(BaseModel):
    is_helpful: bool
    comment: Optional[str] = None

class TranslationFeedbackCreate(TranslationFeedbackBase):
    pass

class TranslationFeedbackResponse(TranslationFeedbackBase):
    id: UUID
    scheme_id: UUID
    language_code: str
    user_id: Optional[UUID] = None
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
