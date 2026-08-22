"""
Database Layer Tests — Sahayak AI
===================================
Tests for:
  - DB connectivity check (mocked — no live DB required)
  - Model instantiation
  - Schema validation
  - Repository method signatures
  - API endpoint structure

Run with:
    cd backend
    .venv/Scripts/pytest tests/ -v
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# ─── Model instantiation tests ────────────────────────────────────────────

def test_user_model_instantiation():
    """User model can be created with required fields."""
    from app.models.user import User
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        is_verified=False,
    )
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.is_active is True
    assert user.is_verified is False


def test_profile_model_instantiation():
    """Profile model can be created with required fields."""
    from app.models.profile import Profile
    from app.models.enums import GenderEnum, CategoryEnum
    user_id = uuid.uuid4()
    profile = Profile(
        id=uuid.uuid4(),
        user_id=user_id,
        age=30,
        gender=GenderEnum.FEMALE,
        annual_income=150000,
        state="Maharashtra",
        category=CategoryEnum.OBC,
        is_farmer=False,
        is_disabled=False,
    )
    assert profile.user_id == user_id
    assert profile.age == 30
    assert profile.gender == GenderEnum.FEMALE
    assert profile.state == "Maharashtra"


def test_scheme_model_instantiation():
    """Scheme model can be created with required fields (Phase 4 extended model)."""
    from app.models.scheme import Scheme
    from app.models.enums import SchemeCategoryEnum, SchemeTypeEnum, ApplicationModeEnum
    scheme = Scheme(
        id=uuid.uuid4(),
        scheme_code="PM-KISAN-2024",
        name="PM Kisan Samman Nidhi",
        short_description="Income support to farmers",
        full_description="Direct income support of Rs 6000 per year to farmer families.",
        category=SchemeCategoryEnum.AGRICULTURE,
        scheme_type=SchemeTypeEnum.CENTRAL,
        application_mode=ApplicationModeEnum.ONLINE,
        is_active=True,
        is_featured=False,
    )
    assert scheme.name == "PM Kisan Samman Nidhi"
    assert scheme.scheme_code == "PM-KISAN-2024"
    assert scheme.category == SchemeCategoryEnum.AGRICULTURE
    assert scheme.scheme_type == SchemeTypeEnum.CENTRAL
    assert scheme.is_active is True
    assert scheme.state is None  # central scheme


def test_eligibility_rule_model_instantiation():
    """EligibilityRule model can be created correctly."""
    from app.models.eligibility_rule import EligibilityRule
    scheme_id = uuid.uuid4()
    rule = EligibilityRule(
        id=uuid.uuid4(),
        scheme_id=scheme_id,
        minimum_age=18,
        maximum_age=60,
        maximum_income=200000,
    )
    assert rule.scheme_id == scheme_id
    assert rule.minimum_age == 18
    assert rule.maximum_age == 60


def test_chat_history_model_instantiation():
    """ChatHistory model can be created correctly."""
    from app.models.chat_history import ChatHistory
    from app.models.enums import LanguageEnum
    user_id = uuid.uuid4()
    chat = ChatHistory(
        id=uuid.uuid4(),
        user_id=user_id,
        question="What is PM Kisan?",
        answer="PM Kisan is a scheme that provides income support to farmers.",
        language=LanguageEnum.ENGLISH,
    )
    assert chat.user_id == user_id
    assert chat.language == LanguageEnum.ENGLISH


# ─── Schema validation tests ──────────────────────────────────────────────

def test_user_create_schema_valid():
    """UserCreate accepts valid data."""
    from app.schemas.user import UserCreate
    data = UserCreate(
        email="user@example.com",
        full_name="Ravi Kumar",
        password="securepassword123",
    )
    assert data.email == "user@example.com"
    assert data.full_name == "Ravi Kumar"


def test_user_create_schema_invalid_email():
    """UserCreate rejects malformed email."""
    from app.schemas.user import UserCreate
    import pydantic
    with pytest.raises(pydantic.ValidationError):
        UserCreate(email="not-an-email", full_name="Test", password="password123")


def test_user_create_schema_short_password():
    """UserCreate rejects passwords shorter than 8 characters."""
    from app.schemas.user import UserCreate
    import pydantic
    with pytest.raises(pydantic.ValidationError):
        UserCreate(email="a@b.com", full_name="Test", password="short")


def test_profile_schema_invalid_age():
    """ProfileCreate rejects negative age."""
    from app.schemas.profile import ProfileCreate
    import pydantic
    with pytest.raises(pydantic.ValidationError):
        ProfileCreate(age=-5)


def test_profile_schema_invalid_state():
    """ProfileCreate rejects unrecognised state names."""
    from app.schemas.profile import ProfileCreate
    import pydantic
    with pytest.raises(pydantic.ValidationError):
        ProfileCreate(state="FakeState123")


def test_eligibility_rule_age_range_validation():
    """EligibilityRuleCreate rejects min_age > max_age."""
    from app.schemas.eligibility_rule import EligibilityRuleCreate
    import pydantic
    with pytest.raises(pydantic.ValidationError):
        EligibilityRuleCreate(
            scheme_id=uuid.uuid4(),
            minimum_age=65,
            maximum_age=18,
        )


def test_scheme_create_schema_valid():
    """SchemeCreate accepts valid data (Phase 4 schema)."""
    from app.schemas.scheme import SchemeCreate
    from app.models.enums import SchemeCategoryEnum, SchemeTypeEnum
    s = SchemeCreate(
        scheme_code="PM-AWAS-2024",
        name="PM Awas Yojana",
        category=SchemeCategoryEnum.HOUSING,
        scheme_type=SchemeTypeEnum.CENTRAL,
        is_active=True,
    )
    assert s.name == "PM Awas Yojana"
    assert s.scheme_code == "PM-AWAS-2024"


# ─── Enum tests ────────────────────────────────────────────────────────────

def test_all_enums_importable():
    """All enums import cleanly."""
    from app.models.enums import (
        GenderEnum, OccupationEnum, EducationEnum,
        CategoryEnum, SchemeCategoryEnum, LanguageEnum,
    )
    assert GenderEnum.MALE == "male"
    assert LanguageEnum.HINDI == "hi"
    assert SchemeCategoryEnum.AGRICULTURE == "agriculture"
    assert CategoryEnum.SC == "sc"


# ─── Config tests ──────────────────────────────────────────────────────────

def test_settings_load():
    """Settings load with expected defaults."""
    from app.core.config import settings
    assert settings.APP_NAME == "Sahayak AI"
    assert settings.DB_POOL_SIZE >= 1
    assert settings.DB_MAX_OVERFLOW >= 0
    assert settings.ALGORITHM == "HS256"


def test_settings_db_url_format():
    """DATABASE_URL starts with the asyncpg driver prefix."""
    from app.core.config import settings
    assert "postgresql+asyncpg://" in settings.DATABASE_URL


# ─── Database connectivity check (mocked) ─────────────────────────────────

@pytest.mark.asyncio
async def test_check_db_connection_returns_true_when_ok():
    """check_db_connection returns True when SELECT 1 succeeds."""
    from app.database.database import check_db_connection
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock())
    mock_cm = AsyncMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("app.database.database.AsyncSessionLocal", return_value=mock_cm):
        result = await check_db_connection()
    assert result is True


@pytest.mark.asyncio
async def test_check_db_connection_returns_false_on_error():
    """check_db_connection returns False when DB raises OperationalError."""
    from app.database.database import check_db_connection
    from sqlalchemy.exc import OperationalError
    mock_cm = AsyncMock()
    mock_cm.__aenter__ = AsyncMock(
        side_effect=OperationalError("connect", {}, Exception("refused"))
    )
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("app.database.database.AsyncSessionLocal", return_value=mock_cm):
        result = await check_db_connection()
    assert result is False


# ─── Repository method presence tests ─────────────────────────────────────

def test_base_repository_has_all_methods():
    """BaseRepository exposes all required CRUD methods."""
    from app.repositories.base import BaseRepository
    for method in ("get_by_id", "get_by_field", "get_all", "count",
                   "create", "update", "delete", "exists"):
        assert hasattr(BaseRepository, method), f"Missing method: {method}"


def test_user_repository_has_email_methods():
    from app.repositories.user_repository import UserRepository
    assert hasattr(UserRepository, "get_by_email")
    assert hasattr(UserRepository, "email_exists")


def test_profile_repository_has_user_methods():
    from app.repositories.profile_repository import ProfileRepository
    assert hasattr(ProfileRepository, "get_by_user_id")
    assert hasattr(ProfileRepository, "get_with_user")


def test_scheme_repository_has_filter_methods():
    from app.repositories.scheme_repository import SchemeRepository
    assert hasattr(SchemeRepository, "get_active_schemes")
    assert hasattr(SchemeRepository, "get_by_category")
    assert hasattr(SchemeRepository, "get_by_state")
    assert hasattr(SchemeRepository, "get_with_rules")


def test_chat_repository_has_history_methods():
    from app.repositories.chat_repository import ChatRepository
    assert hasattr(ChatRepository, "get_user_history")
    assert hasattr(ChatRepository, "count_user_messages")
    assert hasattr(ChatRepository, "delete_user_history")


# ─── Exception hierarchy tests ────────────────────────────────────────────

def test_exception_hierarchy():
    from app.core.exceptions import (
        SahayakBaseException, NotFoundException,
        UserNotFoundException, DuplicateEmailException,
        DatabaseUnavailableException,
    )
    assert issubclass(NotFoundException, SahayakBaseException)
    assert issubclass(UserNotFoundException, NotFoundException)
    assert DuplicateEmailException.status_code == 409
    assert DatabaseUnavailableException.status_code == 503


def test_custom_exception_message_override():
    from app.core.exceptions import NotFoundException
    exc = NotFoundException("Custom not found message")
    assert exc.message == "Custom not found message"
    assert exc.status_code == 404


# ─── API endpoint structure tests ─────────────────────────────────────────

def test_database_router_importable():
    from app.api.v1.endpoints.database import router
    routes = [r.path for r in router.routes]
    assert "/database/health" in routes


def test_api_router_includes_database():
    from app.api.v1.router import api_router
    prefixes = [r.path for r in api_router.routes]
    assert any("database" in p for p in prefixes)
