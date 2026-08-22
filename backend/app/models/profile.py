"""
Profile ORM Model — Sahayak AI
================================
Stores demographic data for a User, used by the eligibility engine.
Kept separate from User so:
  1. Profile can be updated without touching auth fields
  2. Eligibility checks can JOIN profile without loading auth data
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.base import UUIDMixin, TimestampMixin
from app.models.enums import (
    GenderEnum,
    OccupationEnum,
    EducationEnum,
    CategoryEnum,
)

# SQLAlchemy Enum wrapper imports
from sqlalchemy import Enum as SAEnum


class Profile(UUIDMixin, TimestampMixin, Base):
    """
    Citizen demographic profile.

    Every field mirrors a common eligibility criterion used across
    central and state government schemes (age, income, caste, etc.).

    Relationship:
        profile.user → User (many-to-one, FK = user_id)
    """

    __tablename__ = "profiles"

    # ── Foreign key to users ──────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,        # Enforces one-to-one at DB level
        index=True,
    )

    # ── Demographics ──────────────────────────────────────────────────────
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)

    gender: Mapped[GenderEnum | None] = mapped_column(
        SAEnum(GenderEnum, name="gender_enum", create_type=True),
        nullable=True,
    )

    occupation: Mapped[OccupationEnum | None] = mapped_column(
        SAEnum(OccupationEnum, name="occupation_enum", create_type=True),
        nullable=True,
    )

    # ── Financial ─────────────────────────────────────────────────────────
    annual_income: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Annual household income in INR",
    )

    # ── Location ──────────────────────────────────────────────────────────
    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,         # Filtered frequently in scheme queries
    )
    district: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ── Education & social category ───────────────────────────────────────
    education: Mapped[EducationEnum | None] = mapped_column(
        SAEnum(EducationEnum, name="education_enum", create_type=True),
        nullable=True,
    )
    category: Mapped[CategoryEnum | None] = mapped_column(
        SAEnum(CategoryEnum, name="category_enum", create_type=True),
        nullable=True,
        index=True,         # Filtered frequently in eligibility rules
    )

    # ── Special flags ─────────────────────────────────────────────────────
    is_farmer: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    is_disabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # ── Relationship ──────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(        # type: ignore[name-defined]
        "User",
        back_populates="profile",
    )

    # ── Composite indexes ──────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_profiles_state_category", "state", "category"),
        Index("ix_profiles_income_category", "annual_income", "category"),
    )

    def __repr__(self) -> str:
        return f"<Profile id={self.id!s:.8} user_id={self.user_id!s:.8}>"
