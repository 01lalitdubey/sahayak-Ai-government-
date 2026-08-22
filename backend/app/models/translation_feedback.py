"""
Translation Feedback ORM Model — Sahayak AI
=============================================
Stores crowdsourced feedback on translations from the public UI.
"""

import uuid
from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base
from app.models.base import UUIDMixin, TimestampMixin

class TranslationFeedback(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "translation_feedback"

    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schemes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    language_code: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        index=True
    )

    is_helpful: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )

    comment: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
        server_default="open"
    )

    def __repr__(self) -> str:
        return f"<TranslationFeedback scheme={self.scheme_id!s:.8} lang={self.language_code} helpful={self.is_helpful}>"
