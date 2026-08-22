"""
Auth Dependencies — Sahayak AI
================================
Reusable FastAPI Depends() guards for every protected endpoint.

Usage:
    from app.auth.dependencies import get_current_user, require_admin

    @router.get("/me")
    async def me(user: User = Depends(get_current_active_user)):
        ...

    @router.delete("/users/{id}")
    async def delete_user(user: User = Depends(require_admin)):
        ...
"""

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.token import verify_access_token, extract_user_id
from app.core.exceptions import (
    ForbiddenException,
    InactiveUserException,
    TokenMissingException,
)
from app.database.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.services.auth_service import AuthService

# Points to the login endpoint — enables Swagger Authorize button
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,   # We raise our own exceptions, not HTTPException
)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Decode the Bearer token and return the authenticated User.
    Raises TokenMissingException (401) if no token is provided.
    Raises InvalidTokenException / ExpiredTokenException on bad tokens.
    """
    if token is None:
        raise TokenMissingException()

    payload = verify_access_token(token)
    user_id = extract_user_id(payload)

    service = AuthService(db)
    return await service.get_user_by_id(user_id)


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Extends get_current_user — additionally asserts is_active=True.
    Raises InactiveUserException (403) for deactivated accounts.
    """
    if not current_user.is_active:
        raise InactiveUserException()
    return current_user


def require_role(*allowed_roles: UserRole):
    """
    Factory that returns a dependency enforcing one of the given roles.

    Usage:
        @router.get("/admin-only")
        async def admin_route(user: User = Depends(require_role(UserRole.ADMIN))):
    """
    async def _check(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException(
                f"Requires role: {', '.join(r.value for r in allowed_roles)}."
            )
        return current_user
    return _check


# Convenience aliases ──────────────────────────────────────────────────────
require_admin = require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)
require_super_admin = require_role(UserRole.SUPER_ADMIN)
