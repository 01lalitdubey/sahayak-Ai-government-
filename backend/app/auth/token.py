"""
JWT Token Utilities — Sahayak AI
==================================
Centralised token creation, verification, and decoding.
All token operations live here — nothing JWT-related in routes or services.

Token design:
  - Access token  : short-lived (default 30 min), carries user identity + role
  - Refresh token : long-lived (default 7 days), carries only sub + type
  - Both tokens are signed with the same SECRET_KEY using HS256
  - "type" claim distinguishes access from refresh to prevent substitution attacks
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, ExpiredSignatureError, jwt

from app.core.config import settings
from app.core.exceptions import InvalidTokenException, ExpiredTokenException
from app.core.logging import get_logger

logger = get_logger(__name__)

# Token type identifiers stored in the "type" claim
_ACCESS_TOKEN_TYPE = "access"
_REFRESH_TOKEN_TYPE = "refresh"


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_access_token(
    subject: str,
    role: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject:      User UUID as string — stored in "sub" claim
        role:         User role string — stored in "role" claim
        extra_claims: Any additional claims to embed

    Returns:
        Signed JWT string
    """
    now = _utc_now()
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": _ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """
    Create a signed JWT refresh token.
    Carries only sub + type — role is fetched fresh from DB on refresh.

    Args:
        subject: User UUID as string

    Returns:
        Signed JWT string
    """
    now = _utc_now()
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload: dict[str, Any] = {
        "sub": subject,
        "type": _REFRESH_TOKEN_TYPE,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT token.

    Raises:
        ExpiredTokenException   — token is valid but past expiry
        InvalidTokenException   — token is malformed or signature invalid

    Returns:
        Decoded payload dict
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except ExpiredSignatureError:
        logger.warning("Expired JWT token received")
        raise ExpiredTokenException()
    except JWTError as exc:
        logger.warning("Invalid JWT token: %s", exc)
        raise InvalidTokenException()


def verify_access_token(token: str) -> dict[str, Any]:
    """
    Decode token and assert it is an access token.

    Raises:
        InvalidTokenException — if token type is not "access"
    """
    payload = decode_token(token)
    if payload.get("type") != _ACCESS_TOKEN_TYPE:
        raise InvalidTokenException("Token is not an access token.")
    return payload


def verify_refresh_token(token: str) -> dict[str, Any]:
    """
    Decode token and assert it is a refresh token.

    Raises:
        InvalidTokenException — if token type is not "refresh"
    """
    payload = decode_token(token)
    if payload.get("type") != _REFRESH_TOKEN_TYPE:
        raise InvalidTokenException("Token is not a refresh token.")
    return payload


def extract_user_id(payload: dict[str, Any]) -> str:
    """
    Extract the user ID from a decoded JWT payload.

    Raises:
        InvalidTokenException — if "sub" claim is missing
    """
    subject = payload.get("sub")
    if not subject:
        raise InvalidTokenException("Token is missing subject claim.")
    return subject
