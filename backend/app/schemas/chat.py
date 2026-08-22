"""
Chat Schemas — Sahayak AI
"""

from pydantic import BaseModel, Field

from app.schemas.chat_history import ChatHistoryRead


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
        description="User's question, in any of the 13 supported languages",
    )


class ChatAskResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: ChatHistoryRead
