"""
Domain Enums — Sahayak AI
==========================
All Enum types used by ORM models and Pydantic schemas are centralised
here so they can be imported by both layers without circular dependencies.
"""

import enum


class GenderEnum(str, enum.Enum):
    """Biological sex / gender identity as used in Indian government scheme criteria."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class OccupationEnum(str, enum.Enum):
    """Primary livelihood categories used in eligibility rules."""
    FARMER = "farmer"
    AGRICULTURAL_LABOURER = "agricultural_labourer"
    SELF_EMPLOYED = "self_employed"
    SALARIED = "salaried"
    DAILY_WAGE = "daily_wage"
    UNEMPLOYED = "unemployed"
    STUDENT = "student"
    HOMEMAKER = "homemaker"
    RETIRED = "retired"
    OTHER = "other"


class EducationEnum(str, enum.Enum):
    """Highest educational qualification."""
    NO_FORMAL_EDUCATION = "no_formal_education"
    PRIMARY = "primary"            # Up to Class 5
    MIDDLE = "middle"              # Up to Class 8
    SECONDARY = "secondary"        # Class 10 (Matriculation)
    HIGHER_SECONDARY = "higher_secondary"  # Class 12
    GRADUATE = "graduate"          # Bachelor's degree
    POST_GRADUATE = "post_graduate"
    DOCTORATE = "doctorate"
    OTHER = "other"


class CategoryEnum(str, enum.Enum):
    """Social category as defined by Government of India classification."""
    GENERAL = "general"
    OBC = "obc"       # Other Backward Class
    SC = "sc"         # Scheduled Caste
    ST = "st"         # Scheduled Tribe
    EWS = "ews"       # Economically Weaker Section
    OTHER = "other"


class SchemeCategoryEnum(str, enum.Enum):
    """Government scheme domain / ministry category — expanded for Phase 4."""
    AGRICULTURE = "agriculture"
    EDUCATION = "education"
    HEALTH = "health"
    HOUSING = "housing"
    WOMEN_AND_CHILD = "women_and_child"
    SOCIAL_WELFARE = "social_welfare"
    FINANCIAL_INCLUSION = "financial_inclusion"
    SKILL_DEVELOPMENT = "skill_development"
    RURAL_DEVELOPMENT = "rural_development"
    PENSION = "pension"
    INSURANCE = "insurance"
    EMPLOYMENT = "employment"
    DISABILITY = "disability"
    MINORITY = "minority"
    # Phase 4 additions
    FARMER = "farmer"
    STUDENT = "student"
    WOMEN = "women"
    HEALTHCARE = "healthcare"
    BUSINESS = "business"
    TRIBAL = "tribal"
    TRANSPORT = "transport"
    FINANCE = "finance"
    OTHER = "other"


class SchemeTypeEnum(str, enum.Enum):
    """Whether a scheme is run by central or state government."""
    CENTRAL = "central"
    STATE = "state"


class ApplicationModeEnum(str, enum.Enum):
    """How applications are accepted for this scheme."""
    ONLINE = "online"
    OFFLINE = "offline"
    BOTH = "both"


class UserRole(str, enum.Enum):
    """
    User role for role-based access control (RBAC).
    Future-ready: SUPER_ADMIN can be added without schema changes.
    """
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    TRANSLATION_MANAGER = "translation_manager"
    EDITOR = "editor"
    VIEWER = "viewer"


class LanguageEnum(str, enum.Enum):
    """Supported chat languages (ISO 639-1 codes with display names)."""
    ENGLISH = "en"
    HINDI = "hi"
    TAMIL = "ta"
    TELUGU = "te"
    BENGALI = "bn"
    MARATHI = "mr"
    GUJARATI = "gu"
    KANNADA = "kn"
    MALAYALAM = "ml"
    PUNJABI = "pa"
    ODIA = "or"
    ASSAMESE = "as"
    URDU = "ur"


class TranslationStatusEnum(str, enum.Enum):
    """Status of a scheme translation."""
    PENDING = "pending"
    TRANSLATED = "translated"
    OUTDATED = "outdated"
    FAILED = "failed"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"


class TranslationJobStatusEnum(str, enum.Enum):
    """Status of a translation batch job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"
    PAUSED = "paused"
