"""
User ORM Model — Sahayak AI
============================
Represents an application account (citizen or admin).
Authentication details are stored here; demographic profile is in Profile.
"""

from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.base import UUIDMixin, TimestampMixin
from app.models.enums import UserRole
from sqlalchemy import Enum as SAEnum


class User(UUIDMixin, TimestampMixin, Base):
    """
    Core user account table.

    Constraints:
        - email must be unique (enforced at DB and application level)
        - password_hash stores bcrypt hash — plain-text password is NEVER stored
        - is_active / is_verified support account lifecycle management (Phase 2)

    Relationships:
        - profile  : one-to-one  (User → Profile)
        - chats    : one-to-many (User → ChatHistory)
    """

    __tablename__ = "users"

    # ── Core identity ─────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,     # Fast lookups during login
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # ── Auth (populated in Phase 2) ───────────────────────────────────────
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ── Role ─────────────────────────────────────────────────────────────
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.USER,
        server_default="user",
    )

    # ── Last login audit ──────────────────────────────────────────────────
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── Account status ────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # ── Relationships ──────────────────────────────────────────────────────
    profile: Mapped["Profile"] = relationship(      # type: ignore[name-defined]
        "Profile",
        back_populates="user",
        uselist=False,              # One-to-one
        cascade="all, delete-orphan",
        lazy="select",
    )
    chats: Mapped[list["ChatHistory"]] = relationship(  # type: ignore[name-defined]
        "ChatHistory",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # ── Composite indexes ──────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_users_email_is_active", "email", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!s:.8} email={self.email!r}>"
