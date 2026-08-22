"""
Auth Service — Sahayak AI
===========================
All authentication business logic lives here.
Route handlers stay thin — they only call this service.

Responsibilities:
  - User registration (validation, hashing, persistence)
  - User login (credential verification, token generation)
  - Token refresh
  - Role validation
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import hash_password, validate_password_strength
from app.auth.token import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    extract_user_id,
)
from app.core.exceptions import (
    DuplicateEmailException,
    InvalidCredentialsException,
    InactiveUserException,
    UserNotFoundException,
)
from app.core.logging import get_logger
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RegisterResponse,
    LoginResponse,
    RefreshResponse,
    AuthUserData,
)

logger = get_logger(__name__)


class AuthService:
    """
    Stateless auth service — receives a DB session per request via DI.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._repo = UserRepository(db)

    # ── Registration ──────────────────────────────────────────────────────

    async def register(self, payload: RegisterRequest) -> RegisterResponse:
        """
        Register a new user account.

        Steps:
          1. Validate password strength
          2. Check email uniqueness
          3. Hash password
          4. Persist user
          5. Issue tokens
        """
        # 1. Password strength
        validate_password_strength(payload.password)

        # 2. Duplicate check
        if await self._repo.email_exists(payload.email):
            raise DuplicateEmailException()

        # 3. Hash
        password_hash = hash_password(payload.password)

        # 4. Persist
        user = await self._repo.create_user(
            email=payload.email,
            full_name=payload.full_name,
            password_hash=password_hash,
            role=UserRole.USER,
        )
        logger.info("New user registered: %s (id=%s)", user.email, user.id)

        # 5. Tokens
        access_token = create_access_token(str(user.id), user.role.value)
        refresh_token = create_refresh_token(str(user.id))

        return RegisterResponse(
            data=AuthUserData.model_validate(user),
            access_token=access_token,
            refresh_token=refresh_token,
        )

    # ── Login ─────────────────────────────────────────────────────────────

    async def login(self, payload: LoginRequest) -> LoginResponse:
        """
        Authenticate with email + password.

        Steps:
          1. Verify credentials
          2. Check account is active
          3. Record last_login_at
          4. Issue tokens
        """
        # 1. Verify
        user = await self._repo.authenticate_user(payload.email, payload.password)
        if user is None:
            # Constant-time: same error whether email or password is wrong
            raise InvalidCredentialsException()

        # 2. Active check
        if not user.is_active:
            raise InactiveUserException()

        # 3. Audit
        await self._repo.update_last_login(user.id)
        # Re-fetch user after flush so all columns are loaded for Pydantic
        user = await self._repo.get_by_id(user.id) or user
        logger.info("User logged in: %s (id=%s)", user.email, user.id)

        # 4. Tokens
        access_token = create_access_token(str(user.id), user.role.value)
        refresh_token = create_refresh_token(str(user.id))

        return LoginResponse(
            data=AuthUserData.model_validate(user),
            access_token=access_token,
            refresh_token=refresh_token,
        )

    # ── Token refresh ─────────────────────────────────────────────────────

    async def refresh(self, refresh_token: str) -> RefreshResponse:
        """
        Issue new access + refresh token pair from a valid refresh token.
        Fetches user fresh from DB so role/active status is always current.
        """
        payload = verify_refresh_token(refresh_token)
        user_id = extract_user_id(payload)

        from uuid import UUID
        user = await self._repo.get_by_id(UUID(user_id))
        if user is None:
            raise UserNotFoundException()
        if not user.is_active:
            raise InactiveUserException()

        new_access = create_access_token(str(user.id), user.role.value)
        new_refresh = create_refresh_token(str(user.id))

        logger.info("Tokens refreshed for user id=%s", user.id)
        return RefreshResponse(
            access_token=new_access,
            refresh_token=new_refresh,
        )

    # ── Get by ID (used by dependency) ────────────────────────────────────

    async def get_user_by_id(self, user_id: str) -> User:
        """Fetch a user by UUID string. Raises UserNotFoundException if missing."""
        from uuid import UUID
        user = await self._repo.get_by_id(UUID(user_id))
        if user is None:
            raise UserNotFoundException()
        return user
