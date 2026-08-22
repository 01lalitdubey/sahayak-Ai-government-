"""
User Repository — Sahayak AI
Extended in Phase 3 with auth-specific methods.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.enums import UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    # ── Lookup helpers ────────────────────────────────────────────────────

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email (case-insensitive, normalised)."""
        result = await self._db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Return True if an account with this email already exists."""
        return await self.get_by_email(email) is not None

    async def get_active_users(self, *, skip: int = 0, limit: int = 100) -> list[User]:
        """Return only active user accounts."""
        result = await self._db.execute(
            select(User)
            .where(User.is_active == True)  # noqa: E712
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ── Auth-specific methods (Phase 3) ───────────────────────────────────

    async def create_user(
        self,
        email: str,
        full_name: str,
        password_hash: str,
        role: UserRole = UserRole.USER,
    ) -> User:
        """
        Create and persist a new user account.
        Returns the refreshed instance with DB-generated id and timestamps.
        """
        user = User(
            email=email.lower().strip(),
            full_name=full_name,
            password_hash=password_hash,
            role=role,
            is_active=True,
            is_verified=False,
        )
        return await self.create(user)

    async def authenticate_user(self, email: str, plain_password: str) -> User | None:
        """
        Verify email + password combination.
        Returns the User if credentials are valid, None otherwise.
        Caller is responsible for raising InvalidCredentialsException.
        Importing password module here avoids circular imports.
        """
        from app.auth.password import verify_password
        user = await self.get_by_email(email)
        if user is None:
            return None
        if not user.password_hash:
            return None
        if not verify_password(plain_password, user.password_hash):
            return None
        return user

    async def update_last_login(self, user_id: UUID) -> None:
        """Record the current UTC timestamp as last_login_at for audit purposes."""
        user = await self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.now(tz=timezone.utc)
            await self._db.flush()
