"""
EligibilityRule ORM Model — Sahayak AI (Extended Phase 5)
===========================================================
Defines criteria a citizen must meet to be eligible for a scheme.
Extended with: minimum_income, education, require_farmer, require_disabled.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.base import UUIDMixin, TimestampMixin
from app.models.enums import GenderEnum, OccupationEnum, CategoryEnum, EducationEnum
from sqlalchemy import Enum as SAEnum


class EligibilityRule(UUIDMixin, TimestampMixin, Base):
    """
    Eligibility criteria for a specific scheme.
    NULL = no restriction on that criterion.
    All non-NULL fields must be satisfied simultaneously.
    """

    __tablename__ = "eligibility_rules"

    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schemes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Age ───────────────────────────────────────────────────────────────
    minimum_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    maximum_age: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Income ────────────────────────────────────────────────────────────
    minimum_income: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Minimum annual income in INR (NULL = no floor)"
    )
    maximum_income: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Maximum annual income in INR (NULL = no ceiling)"
    )

    # ── Demographics ──────────────────────────────────────────────────────
    gender: Mapped[GenderEnum | None] = mapped_column(
        SAEnum(GenderEnum, name="gender_enum", create_type=False), nullable=True
    )
    occupation: Mapped[OccupationEnum | None] = mapped_column(
        SAEnum(OccupationEnum, name="occupation_enum", create_type=False), nullable=True
    )
    education: Mapped[EducationEnum | None] = mapped_column(
        SAEnum(EducationEnum, name="education_enum", create_type=False),
        nullable=True,
        comment="Minimum required education level",
    )
    category: Mapped[CategoryEnum | None] = mapped_column(
        SAEnum(CategoryEnum, name="category_enum", create_type=False), nullable=True
    )

    # ── Geography ─────────────────────────────────────────────────────────
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ── Special flags ─────────────────────────────────────────────────────
    require_farmer: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True,
        comment="True = must be farmer; False = must NOT be farmer; None = irrelevant"
    )
    require_disabled: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True,
        comment="True = must be disabled; None = irrelevant"
    )

    # ── Relationship ──────────────────────────────────────────────────────
    scheme: Mapped["Scheme"] = relationship(  # type: ignore[name-defined]
        "Scheme", back_populates="eligibility_rules"
    )

    __table_args__ = (
        Index("ix_eligibility_rules_scheme_id", "scheme_id"),
        Index("ix_eligibility_rules_state_category", "state", "category"),
    )

    def __repr__(self) -> str:
        return f"<EligibilityRule id={self.id!s:.8} scheme_id={self.scheme_id!s:.8}>"
