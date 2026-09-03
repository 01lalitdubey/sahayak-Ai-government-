"""
Auth Endpoints — Sahayak AI
=============================
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me

Route handlers are intentionally thin — all logic is in AuthService.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    CurrentUserResponse,
    LogoutResponse,
    AuthUserData,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    responses={
        409: {"description": "Email already registered"},
        400: {"description": "Password does not meet complexity requirements"},
        422: {"description": "Validation error"},
    },
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    """
    Create a new citizen account.

    - Validates email format and uniqueness
    - Enforces password complexity (8+ chars, upper, lower, digit, special)
    - Confirms password == confirm_password
    - Returns access token + refresh token immediately
    """
    service = AuthService(db)
    return await service.register(payload)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with email and password",
    responses={
        401: {"description": "Invalid credentials"},
        403: {"description": "Account is inactive"},
    },
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    Authenticate with email + password.
    Returns access token (30 min) and refresh token (7 days).
    """
    service = AuthService(db)
    return await service.login(payload)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    responses={
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> RefreshResponse:
    """
    Exchange a valid refresh token for a new access token + refresh token pair.

    NOTE: tokens are stateless JWTs with no server-side store, so the previous
    refresh token stays valid until it expires — this is NOT true rotation.
    TODO(auth): add a jti denylist (Redis) to enforce single-use refresh
    tokens and support real logout / revocation.
    """
    service = AuthService(db)
    return await service.refresh(payload.refresh_token)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout (stateless)",
)
async def logout(
    _current_user: User = Depends(get_current_active_user),
) -> LogoutResponse:
    """
    Stateless logout — the client must discard its tokens.
    Server-side token blocklist can be added in a future phase (Redis).
    Requires a valid Bearer token so accidental calls fail cleanly.
    """
    return LogoutResponse()


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user",
    responses={
        401: {"description": "Missing or invalid token"},
        403: {"description": "Account is inactive"},
    },
)
async def me(
    current_user: User = Depends(get_current_active_user),
) -> CurrentUserResponse:
    """
    Return the profile of the currently authenticated user.
    Requires a valid Bearer access token in the Authorization header.
    """
    return CurrentUserResponse(data=AuthUserData.model_validate(current_user))
