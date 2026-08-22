"""
TranslationJob ORM Model — Sahayak AI
=======================================
Tracks asynchronous batch translation jobs.
"""

import uuid
from datetime import datetime

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum as SAEnum

from app.database.database import Base
from app.models.base import UUIDMixin, TimestampMixin
from app.models.enums import TranslationJobStatusEnum

class TranslationJob(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "translation_jobs"

    job_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Type of job, e.g., 'pilot_translation', 'full_translation'"
    )

    status: Mapped[TranslationJobStatusEnum] = mapped_column(
        SAEnum(TranslationJobStatusEnum, name="translation_job_status_enum", create_type=True,
               values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=TranslationJobStatusEnum.PENDING,
        server_default="pending"
    )

    total_records: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    processed_records: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    failed_records: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    current_batch: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    estimated_remaining: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Estimated time remaining in seconds"
    )

    logs: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        server_default="[]",
        comment="Array of log events"
    )

    def __repr__(self) -> str:
        return f"<TranslationJob id={self.id!s:.8} status={self.status}>"
