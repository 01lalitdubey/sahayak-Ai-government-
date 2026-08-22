"""
Profile Repository — Sahayak AI
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import Profile
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository[Profile]):

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Profile, db)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Profile | None:
        """Fetch the profile that belongs to a specific user."""
        result = await self._db.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_with_user(self, user_id: uuid.UUID) -> Profile | None:
        """Fetch profile eagerly loading the related User."""
        result = await self._db.execute(
            select(Profile)
            .options(selectinload(Profile.user))
            .where(Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def profile_exists_for_user(self, user_id: uuid.UUID) -> bool:
        profile = await self.get_by_user_id(user_id)
        return profile is not None
