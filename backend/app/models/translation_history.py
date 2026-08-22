"""
Translation History ORM Model — Sahayak AI
==========================================
Tracks every edit made to a translation by an admin, preserving the historical JSONB content.
"""

import uuid
from sqlalchemy import Integer, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.base import UUIDMixin, TimestampMixin

class TranslationHistory(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "translation_history"

    translation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scheme_translations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    translated_content: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False
    )

    editor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    reason: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    # Relationship
    translation: Mapped["SchemeTranslation"] = relationship(  # type: ignore[name-defined]
        "SchemeTranslation"
    )

    __table_args__ = (
        Index("ix_trans_hist_translation_id_version", "translation_id", "version", unique=True),
    )

    def __repr__(self) -> str:
        return f"<TranslationHistory translation_id={self.translation_id!s:.8} version={self.version}>"
