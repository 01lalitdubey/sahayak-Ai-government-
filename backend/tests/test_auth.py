"""
Authentication Tests — Sahayak AI
====================================
Tests for:
  - Password utilities (hashing, verification, complexity)
  - Token utilities (create, verify, expire, wrong type)
  - Auth schemas (register validation, login, password match)
  - Exception hierarchy (auth exceptions)
  - Auth service (mocked DB — no live PostgreSQL needed)
  - Auth endpoints (via httpx AsyncClient + mocked services)
  - Role-based dependencies

Run with:
    cd backend
    .venv/Scripts/pytest tests/test_auth.py -v
"""

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ─── Password utility tests ───────────────────────────────────────────────

def test_hash_password_produces_bcrypt_hash():
    from app.auth.password import hash_password
    h = hash_password("MyPassword1!")
    assert h.startswith("$2b$") or h.startswith("$2a$")
    assert h != "MyPassword1!"


def test_verify_password_correct():
    from app.auth.password import hash_password, verify_password
    h = hash_password("MyPassword1!")
    assert verify_password("MyPassword1!", h) is True


def test_verify_password_wrong():
    from app.auth.password import hash_password, verify_password
    h = hash_password("MyPassword1!")
    assert verify_password("WrongPassword1!", h) is False


def test_password_strength_valid():
    from app.auth.password import validate_password_strength
    result = validate_password_strength("StrongPass1!")
    assert result == "StrongPass1!"


def test_password_strength_too_short():
    from app.auth.password import validate_password_strength
    from app.core.exceptions import ValidationException
    with pytest.raises(ValidationException, match="8 characters"):
        validate_password_strength("Ab1!")


def test_password_strength_no_uppercase():
    from app.auth.password import validate_password_strength
    from app.core.exceptions import ValidationException
    with pytest.raises(ValidationException, match="uppercase"):
        validate_password_strength("weakpass1!")


def test_password_strength_no_lowercase():
    from app.auth.password import validate_password_strength
    from app.core.exceptions import ValidationException
    with pytest.raises(ValidationException, match="lowercase"):
        validate_password_strength("ALLCAPS1!")


def test_password_strength_no_digit():
    from app.auth.password import validate_password_strength
    from app.core.exceptions import ValidationException
    with pytest.raises(ValidationException, match="digit"):
        validate_password_strength("NoDigits!")


def test_password_strength_no_special():
    from app.auth.password import validate_password_strength
    from app.core.exceptions import ValidationException
    with pytest.raises(ValidationException, match="special"):
        validate_password_strength("NoSpecial1")


# ─── Token utility tests ──────────────────────────────────────────────────

def test_create_and_verify_access_token():
    from app.auth.token import create_access_token, verify_access_token
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id, "user")
    payload = verify_access_token(token)
    assert payload["sub"] == user_id
    assert payload["role"] == "user"
    assert payload["type"] == "access"


def test_create_and_verify_refresh_token():
    from app.auth.token import create_refresh_token, verify_refresh_token
    user_id = str(uuid.uuid4())
    token = create_refresh_token(user_id)
    payload = verify_refresh_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"


def test_access_token_with_wrong_type_rejected():
    from app.auth.token import create_refresh_token, verify_access_token
    from app.core.exceptions import InvalidTokenException
    token = create_refresh_token(str(uuid.uuid4()))
    with pytest.raises(InvalidTokenException):
        verify_access_token(token)


def test_refresh_token_with_wrong_type_rejected():
    from app.auth.token import create_access_token, verify_refresh_token
    from app.core.exceptions import InvalidTokenException
    token = create_access_token(str(uuid.uuid4()), "user")
    with pytest.raises(InvalidTokenException):
        verify_refresh_token(token)


def test_expired_token_raises_expired_exception():
    from app.auth.token import extract_user_id
    from app.core.exceptions import ExpiredTokenException
    from jose import jwt
    from app.core.config import settings

    payload = {
        "sub": str(uuid.uuid4()),
        "type": "access",
        "role": "user",
        "exp": datetime.now(tz=timezone.utc) - timedelta(seconds=1),
    }
    expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    from app.auth.token import decode_token
    with pytest.raises(ExpiredTokenException):
        decode_token(expired_token)


def test_invalid_token_raises_invalid_exception():
    from app.auth.token import decode_token
    from app.core.exceptions import InvalidTokenException
    with pytest.raises(InvalidTokenException):
        decode_token("this.is.not.a.valid.jwt")


def test_extract_user_id_success():
    from app.auth.token import create_access_token, verify_access_token, extract_user_id
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id, "user")
    payload = verify_access_token(token)
    assert extract_user_id(payload) == user_id


def test_extract_user_id_missing_sub():
    from app.auth.token import extract_user_id
    from app.core.exceptions import InvalidTokenException
    with pytest.raises(InvalidTokenException):
        extract_user_id({"type": "access"})


# ─── Auth schema tests ────────────────────────────────────────────────────

def test_register_request_valid():
    from app.schemas.auth import RegisterRequest
    r = RegisterRequest(
        email="test@example.com",
        full_name="Test User",
        password="StrongPass1!",
        confirm_password="StrongPass1!",
    )
    assert r.email == "test@example.com"


def test_register_request_email_normalised():
    from app.schemas.auth import RegisterRequest
    r = RegisterRequest(
        email="  TEST@EXAMPLE.COM  ",
        full_name="Test",
        password="StrongPass1!",
        confirm_password="StrongPass1!",
    )
    assert r.email == "test@example.com"


def test_register_request_passwords_mismatch():
    from app.schemas.auth import RegisterRequest
    import pydantic
    with pytest.raises(pydantic.ValidationError, match="do not match"):
        RegisterRequest(
            email="a@b.com",
            full_name="Test",
            password="StrongPass1!",
            confirm_password="DifferentPass1!",
        )


def test_register_request_invalid_email():
    from app.schemas.auth import RegisterRequest
    import pydantic
    with pytest.raises(pydantic.ValidationError):
        RegisterRequest(
            email="not-an-email",
            full_name="Test",
            password="StrongPass1!",
            confirm_password="StrongPass1!",
        )


def test_login_request_email_normalised():
    from app.schemas.auth import LoginRequest
    r = LoginRequest(email="  USER@EXAMPLE.COM  ", password="any")
    assert r.email == "user@example.com"


# ─── Auth exception tests ─────────────────────────────────────────────────

def test_auth_exceptions_status_codes():
    from app.core.exceptions import (
        InvalidCredentialsException,
        UnauthorisedException,
        ExpiredTokenException,
        InvalidTokenException,
        TokenMissingException,
        ForbiddenException,
        InactiveUserException,
    )
    assert InvalidCredentialsException.status_code == 401
    assert UnauthorisedException.status_code == 401
    assert ExpiredTokenException.status_code == 401
    assert InvalidTokenException.status_code == 401
    assert TokenMissingException.status_code == 401
    assert ForbiddenException.status_code == 403
    assert InactiveUserException.status_code == 403


# ─── User role enum tests ─────────────────────────────────────────────────

def test_user_role_values():
    from app.models.enums import UserRole
    assert UserRole.USER == "user"
    assert UserRole.ADMIN == "admin"
    assert UserRole.SUPER_ADMIN == "super_admin"


# ─── User model role field test ───────────────────────────────────────────

def test_user_model_has_role_and_last_login():
    from app.models.user import User
    from app.models.enums import UserRole
    user = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    assert user.role == UserRole.ADMIN
    assert user.last_login_at is None


# ─── Auth service tests (mocked DB) ──────────────────────────────────────

def _make_mock_user(
    role="user",
    is_active=True,
    password_hash=None,
) -> MagicMock:
    from app.auth.password import hash_password
    from app.models.enums import UserRole
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "ravi@example.com"
    user.full_name = "Ravi Kumar"
    # Use a real UserRole enum value so Pydantic model_validate works
    user.role = UserRole(role)
    user.is_active = is_active
    user.is_verified = False
    user.password_hash = password_hash or hash_password("StrongPass1!")
    user.last_login_at = None
    user.created_at = datetime.now(tz=timezone.utc)
    user.updated_at = datetime.now(tz=timezone.utc)
    return user


@pytest.mark.asyncio
async def test_auth_service_register_success():
    from app.services.auth_service import AuthService
    from app.schemas.auth import RegisterRequest

    mock_db = AsyncMock()
    service = AuthService(mock_db)

    request = RegisterRequest(
        email="newuser@example.com",
        full_name="New User",
        password="StrongPass1!",
        confirm_password="StrongPass1!",
    )

    mock_user = _make_mock_user()
    mock_user.email = "newuser@example.com"

    with patch.object(service._repo, "email_exists", return_value=False), \
         patch.object(service._repo, "create_user", return_value=mock_user):
        result = await service.register(request)

    assert result.success is True
    assert result.access_token != ""
    assert result.refresh_token != ""


@pytest.mark.asyncio
async def test_auth_service_register_duplicate_email():
    from app.services.auth_service import AuthService
    from app.schemas.auth import RegisterRequest
    from app.core.exceptions import DuplicateEmailException

    mock_db = AsyncMock()
    service = AuthService(mock_db)

    request = RegisterRequest(
        email="existing@example.com",
        full_name="Existing",
        password="StrongPass1!",
        confirm_password="StrongPass1!",
    )

    with patch.object(service._repo, "email_exists", return_value=True):
        with pytest.raises(DuplicateEmailException):
            await service.register(request)


@pytest.mark.asyncio
async def test_auth_service_login_success():
    from app.services.auth_service import AuthService
    from app.schemas.auth import LoginRequest

    mock_db = AsyncMock()
    service = AuthService(mock_db)
    mock_user = _make_mock_user()

    with patch.object(service._repo, "authenticate_user", return_value=mock_user), \
         patch.object(service._repo, "update_last_login", return_value=None), \
         patch.object(service._repo, "get_by_id", return_value=mock_user):
        result = await service.login(LoginRequest(email="ravi@example.com", password="StrongPass1!"))

    assert result.success is True
    assert result.access_token != ""


@pytest.mark.asyncio
async def test_auth_service_login_wrong_password():
    from app.services.auth_service import AuthService
    from app.schemas.auth import LoginRequest
    from app.core.exceptions import InvalidCredentialsException

    mock_db = AsyncMock()
    service = AuthService(mock_db)

    with patch.object(service._repo, "authenticate_user", return_value=None):
        with pytest.raises(InvalidCredentialsException):
            await service.login(LoginRequest(email="a@b.com", password="WrongPass1!"))


@pytest.mark.asyncio
async def test_auth_service_login_inactive_user():
    from app.services.auth_service import AuthService
    from app.schemas.auth import LoginRequest
    from app.core.exceptions import InactiveUserException

    mock_db = AsyncMock()
    service = AuthService(mock_db)
    inactive_user = _make_mock_user(is_active=False)

    with patch.object(service._repo, "authenticate_user", return_value=inactive_user):
        with pytest.raises(InactiveUserException):
            await service.login(LoginRequest(email="a@b.com", password="StrongPass1!"))


@pytest.mark.asyncio
async def test_auth_service_refresh_success():
    from app.services.auth_service import AuthService
    from app.auth.token import create_refresh_token

    mock_db = AsyncMock()
    service = AuthService(mock_db)
    mock_user = _make_mock_user()
    refresh_token = create_refresh_token(str(mock_user.id))

    with patch.object(service._repo, "get_by_id", return_value=mock_user):
        result = await service.refresh(refresh_token)

    assert result.access_token != ""
    assert result.refresh_token != ""


@pytest.mark.asyncio
async def test_auth_service_refresh_invalid_token():
    from app.services.auth_service import AuthService
    from app.core.exceptions import InvalidTokenException

    mock_db = AsyncMock()
    service = AuthService(mock_db)

    with pytest.raises(InvalidTokenException):
        await service.refresh("totally.invalid.token")


# ─── API endpoint tests (TestClient — no live DB) ─────────────────────────

def _get_test_client():
    from app.main import create_application
    app = create_application()
    return TestClient(app, raise_server_exceptions=False)


def test_register_endpoint_returns_422_on_empty_body():
    client = _get_test_client()
    resp = client.post("/api/v1/auth/register", json={})
    assert resp.status_code == 422


def test_login_endpoint_returns_422_on_empty_body():
    client = _get_test_client()
    resp = client.post("/api/v1/auth/login", json={})
    assert resp.status_code == 422


def test_me_endpoint_returns_401_without_token():
    client = _get_test_client()
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_logout_endpoint_returns_401_without_token():
    client = _get_test_client()
    resp = client.post("/api/v1/auth/logout")
    assert resp.status_code == 401


def test_refresh_endpoint_returns_422_on_empty_body():
    client = _get_test_client()
    resp = client.post("/api/v1/auth/refresh", json={})
    assert resp.status_code == 422


def test_me_endpoint_returns_401_with_invalid_token():
    client = _get_test_client()
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401


def test_auth_routes_in_openapi():
    client = _get_test_client()
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    assert "/api/v1/auth/register" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/me" in paths
    assert "/api/v1/auth/refresh" in paths
    assert "/api/v1/auth/logout" in paths


def test_swagger_has_security_scheme():
    client = _get_test_client()
    spec = client.get("/openapi.json").json()
    assert "securitySchemes" in spec.get("components", {})


# ─── Dependency tests ─────────────────────────────────────────────────────

def test_dependencies_are_importable():
    from app.auth.dependencies import (
        get_current_user,
        get_current_active_user,
        require_role,
        require_admin,
    )
    assert callable(get_current_user)
    assert callable(get_current_active_user)
    assert callable(require_role)
    assert callable(require_admin)


def test_require_role_returns_callable():
    from app.auth.dependencies import require_role
    from app.models.enums import UserRole
    dep = require_role(UserRole.ADMIN)
    assert callable(dep)
