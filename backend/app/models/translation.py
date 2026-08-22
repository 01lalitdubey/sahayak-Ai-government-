"""
SchemeTranslation ORM Model — Sahayak AI
==========================================
Stores the translated JSONB content for a specific scheme and language.
Implements versioning and checksum caching.
"""

import uuid
from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, Index, UniqueConstraint, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from app.database.database import Base
from app.models.base import UUIDMixin, TimestampMixin
from app.models.enums import TranslationStatusEnum

class SchemeTranslation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "scheme_translations"

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

    translated_content: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default='{}'
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1"
    )

    checksum: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True
    )

    translation_quality: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    provider: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    status: Mapped[TranslationStatusEnum] = mapped_column(
        SAEnum(TranslationStatusEnum, name="translation_status_enum", create_type=True,
               values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=TranslationStatusEnum.PENDING_REVIEW,
        server_default="pending_review"
    )

    # TMS specific fields
    review_status: Mapped[TranslationStatusEnum | None] = mapped_column(
        SAEnum(TranslationStatusEnum, name="translation_status_enum", create_type=False,
               values_callable=lambda obj: [e.value for e in obj]),
        nullable=True
    )
    
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    review_comment: Mapped[str | None] = mapped_column(String, nullable=True)
    
    last_editor: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    last_reviewer: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    manual_override: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false"
    )
    
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        index=True
    )
    
    approved_version: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    # Relationship
    scheme: Mapped["Scheme"] = relationship(  # type: ignore[name-defined]
        "Scheme",
        back_populates="translations"
    )

    __table_args__ = (
        UniqueConstraint("scheme_id", "language_code", name="uq_translation_scheme_lang"),
    )

    def __repr__(self) -> str:
        return f"<SchemeTranslation id={self.id!s:.8} scheme_id={self.scheme_id!s:.8} lang={self.language_code}>"
