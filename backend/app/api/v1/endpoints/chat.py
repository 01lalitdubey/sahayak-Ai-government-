"""
Chat Endpoints — Sahayak AI
==============================
POST /api/v1/chat/ask      — ask the RAG assistant a question; answered in
                              whichever of the 13 supported languages it was
                              asked in
GET  /api/v1/chat/history  — list the current user's past conversation turns
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.chat import ChatAskResponse, ChatRequest
from app.schemas.chat_history import ChatHistoryRead
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


def _svc(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(db)


@router.post(
    "/ask",
    response_model=ChatAskResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask the multilingual scheme assistant a question",
)
async def ask(
    payload: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    svc: ChatService = Depends(_svc),
) -> ChatAskResponse:
    chat = await svc.ask(current_user.id, payload.message)
    return ChatAskResponse(data=ChatHistoryRead.model_validate(chat))


@router.get(
    "/history",
    response_model=list[ChatHistoryRead],
    summary="Get the current user's chat history, newest first",
)
async def history(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    svc: ChatService = Depends(_svc),
) -> list[ChatHistoryRead]:
    chats = await svc.get_history(current_user.id, skip=skip, limit=limit)
    return [ChatHistoryRead.model_validate(c) for c in chats]
