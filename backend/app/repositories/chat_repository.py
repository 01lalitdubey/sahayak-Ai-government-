"""
ChatHistory Repository — Sahayak AI
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_history import ChatHistory
from app.repositories.base import BaseRepository


class ChatRepository(BaseRepository[ChatHistory]):

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(ChatHistory, db)

    async def get_user_history(
        self,
        user_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ChatHistory]:
        """
        Return chat history for a user, newest first.
        Default limit of 50 — chat history can grow large quickly.
        """
        result = await self._db.execute(
            select(ChatHistory)
            .where(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_user_messages(self, user_id: uuid.UUID) -> int:
        """Return total number of messages sent by a user."""
        return await self.count(filters={"user_id": user_id})

    async def delete_user_history(self, user_id: uuid.UUID) -> int:
        """Hard-delete all chat records for a user. Returns deleted count."""
        chats = await self.get_user_history(user_id, limit=10_000)
        for chat in chats:
            await self._db.delete(chat)
        await self._db.flush()
        return len(chats)
