"""
Scheme ORM Model — Sahayak AI (Extended Phase 4)
==================================================
Represents a central or state government scheme, subsidy, or benefit.
Extended with production fields: scheme_code, scheme_type, ministry,
department, application_mode, contact info, dates, audit fields, etc.
Original fields preserved — only new columns added.
"""

import uuid
from datetime import date

from sqlalchemy import (
    Boolean, Date, Index, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.base import UUIDMixin, TimestampMixin
from app.models.enums import SchemeCategoryEnum, SchemeTypeEnum, ApplicationModeEnum
from sqlalchemy import Enum as SAEnum


class Scheme(UUIDMixin, TimestampMixin, Base):
    """
    Government scheme record — extended for Phase 4.

    Soft-delete pattern: is_active=False hides from public API.
    Unique constraints: scheme_code (globally unique), name+state (unique per scope).
    """

    __tablename__ = "schemes"

    # ── Identification ────────────────────────────────────────────────────
    scheme_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique short code, e.g. PM-KISAN-2024",
    )
    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    # ── Content ───────────────────────────────────────────────────────────
    short_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="One-line summary shown in list views",
    )
    full_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed scheme description (was: description)",
    )
    benefits: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="What the beneficiary receives — cash, subsidy, asset, service",
    )
    required_documents: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="List of documents required for application",
    )
    application_process: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Step-by-step application process",
    )

    # ── Classification ────────────────────────────────────────────────────
    scheme_type: Mapped[SchemeTypeEnum] = mapped_column(
        SAEnum(SchemeTypeEnum, name="scheme_type_enum", create_type=True,
               values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=SchemeTypeEnum.CENTRAL,
        server_default="central",
        index=True,
    )
    category: Mapped[SchemeCategoryEnum | None] = mapped_column(
        SAEnum(SchemeCategoryEnum, name="scheme_category_enum", create_type=False,
               values_callable=lambda obj: [e.value for e in obj]),
        nullable=True,
        index=True,
    )
    ministry: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
        index=True,
        comment="Administering ministry, e.g. Ministry of Agriculture",
    )
    department: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
        comment="Administering department under the ministry",
    )

    # ── Geographic scope ──────────────────────────────────────────────────
    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="NULL = central scheme applicable nationwide",
    )
    district: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Further geographic restriction to a district (rare)",
    )

    # ── Application ───────────────────────────────────────────────────────
    application_mode: Mapped[ApplicationModeEnum] = mapped_column(
        SAEnum(ApplicationModeEnum, name="application_mode_enum", create_type=True,
               values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ApplicationModeEnum.ONLINE,
        server_default="online",
    )
    application_start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date from which applications are accepted",
    )
    application_end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Last date for applications (NULL = always open)",
    )

    # ── External references ───────────────────────────────────────────────
    official_url: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )
    official_pdf_url: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        comment="URL to official scheme guidelines PDF",
    )
    contact_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    contact_phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # ── Lifecycle & visibility ─────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
        comment="False = soft-deleted, hidden from public API",
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
        comment="Highlighted on homepage / discovery page",
    )
    view_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Incremented on each public GET /schemes/{id} call",
    )

    # ── Audit ─────────────────────────────────────────────────────────────
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User UUID who created this record",
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User UUID who last updated this record",
    )

    # ── Relationships ──────────────────────────────────────────────────────
    eligibility_rules: Mapped[list["EligibilityRule"]] = relationship(  # type: ignore[name-defined]
        "EligibilityRule",
        back_populates="scheme",
        cascade="all, delete-orphan",
        lazy="select",
    )
    translations: Mapped[list["SchemeTranslation"]] = relationship(  # type: ignore[name-defined]
        "SchemeTranslation",
        back_populates="scheme",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # ── Table-level constraints and indexes ───────────────────────────────
    __table_args__ = (
        UniqueConstraint("name", "state", name="uq_schemes_name_state"),
        Index("ix_schemes_category_state", "category", "state"),
        Index("ix_schemes_type_category", "scheme_type", "category"),
        Index("ix_schemes_is_active_featured", "is_active", "is_featured"),
        Index("ix_schemes_ministry", "ministry"),
        Index("ix_schemes_application_mode", "application_mode"),
        Index("ix_schemes_dates", "application_start_date", "application_end_date"),
    )

    def __repr__(self) -> str:
        return f"<Scheme id={self.id!s:.8} code={self.scheme_code!r} name={self.name!r}>"
