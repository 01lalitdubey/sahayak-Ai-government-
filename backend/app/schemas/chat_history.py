"""
ChatHistory Schemas — Sahayak AI
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import LanguageEnum


class ChatHistoryBase(BaseModel):
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    language: LanguageEnum = LanguageEnum.ENGLISH


class ChatHistoryCreate(ChatHistoryBase):
    """user_id is injected by the service layer, not the caller."""
    pass


class ChatHistoryRead(ChatHistoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ChatHistoryResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: ChatHistoryRead | None = None
