"""
ChatHistory ORM Model — Sahayak AI
=====================================
Stores every AI conversation turn for a user.
Each row = one user question + one AI answer pair.
Used for context window management and analytics in later phases.
"""

import uuid

from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.base import UUIDMixin, TimestampMixin
from app.models.enums import LanguageEnum
from sqlalchemy import Enum as SAEnum


class ChatHistory(UUIDMixin, TimestampMixin, Base):
    """
    Single conversation turn (question + answer).

    No updated_at — chat records are immutable once created.
    created_at inherited from TimestampMixin serves as the turn timestamp.

    Relationship:
        chat.user → User (many-to-one, FK = user_id)
    """

    __tablename__ = "chat_history"

    # ── Foreign key ───────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Conversation content ──────────────────────────────────────────────
    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The user's input message",
    )
    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The AI-generated response",
    )

    # ── Language ──────────────────────────────────────────────────────────
    language: Mapped[LanguageEnum] = mapped_column(
        SAEnum(LanguageEnum, name="language_enum", create_type=True),
        nullable=False,
        default=LanguageEnum.ENGLISH,
        server_default="en",
    )

    # ── Relationship ──────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(        # type: ignore[name-defined]
        "User",
        back_populates="chats",
    )

    # ── Indexes ───────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_chat_history_user_id", "user_id"),
        Index("ix_chat_history_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ChatHistory id={self.id!s:.8} user_id={self.user_id!s:.8}>"
