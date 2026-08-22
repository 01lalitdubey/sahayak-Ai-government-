"""
Models package — Sahayak AI
============================
ALL ORM models MUST be imported here.
Alembic env.py does `import app.models` which triggers this file,
making SQLAlchemy register every table in Base.metadata for autogenerate.

Import order matters: parent models before children (FK dependencies).
"""

from app.models.base import UUIDMixin, TimestampMixin          # noqa: F401
from app.models.enums import (                                  # noqa: F401
    GenderEnum,
    OccupationEnum,
    EducationEnum,
    CategoryEnum,
    SchemeCategoryEnum,
    SchemeTypeEnum,
    ApplicationModeEnum,
    LanguageEnum,
    UserRole,
)
from app.models.user import User                                # noqa: F401
from app.models.profile import Profile                         # noqa: F401
from app.models.scheme import Scheme                           # noqa: F401
from app.models.eligibility_rule import EligibilityRule        # noqa: F401
from app.models.chat_history import ChatHistory                # noqa: F401
from app.models.translation import SchemeTranslation
from app.models.translation_job import TranslationJob
from app.models.translation_history import TranslationHistory
from app.models.translation_feedback import TranslationFeedback          # noqa: F401
from app.models.audit_log import AuditLog                        # noqa: F401

__all__ = [
    "UUIDMixin",
    "TimestampMixin",
    "GenderEnum",
    "OccupationEnum",
    "EducationEnum",
    "CategoryEnum",
    "SchemeCategoryEnum",
    "LanguageEnum",
    "User",
    "Profile",
    "Scheme",
    "EligibilityRule",
    "ChatHistory",
    "SchemeTranslation",
    "TranslationJob",
    "TranslationHistory",
    "TranslationFeedback",
    "AuditLog",
]
