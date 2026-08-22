"""
Translation Repository — Sahayak AI
====================================
Data access layer for SchemeTranslation.
"""

import uuid
from typing import Sequence

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.translation import SchemeTranslation
from app.models.enums import TranslationStatusEnum

class TranslationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_scheme_and_lang(self, scheme_id: uuid.UUID, language_code: str, only_published: bool = False) -> SchemeTranslation | None:
        """Fetch a specific translation for a scheme."""
        conditions = [
            SchemeTranslation.scheme_id == scheme_id,
            SchemeTranslation.language_code == language_code
        ]
        if only_published:
            conditions.append(SchemeTranslation.is_published == True)
            conditions.append(SchemeTranslation.status == TranslationStatusEnum.PUBLISHED)
            
        stmt = select(SchemeTranslation).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_scheme_ids_and_lang(self, scheme_ids: list[uuid.UUID], language_code: str, only_published: bool = False) -> Sequence[SchemeTranslation]:
        """Fetch translations for a list of schemes."""
        if not scheme_ids:
            return []
            
        conditions = [
            SchemeTranslation.scheme_id.in_(scheme_ids),
            SchemeTranslation.language_code == language_code
        ]
        if only_published:
            conditions.append(SchemeTranslation.is_published == True)
            conditions.append(SchemeTranslation.status == TranslationStatusEnum.PUBLISHED)
            
        stmt = select(SchemeTranslation).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_checksum(self, checksum: str, language_code: str) -> SchemeTranslation | None:
        """Check if a translation with this checksum already exists for the given language."""
        stmt = select(SchemeTranslation).where(
            and_(
                SchemeTranslation.checksum == checksum,
                SchemeTranslation.language_code == language_code,
                SchemeTranslation.status == TranslationStatusEnum.TRANSLATED
            )
        ).limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, translation: SchemeTranslation) -> SchemeTranslation:
        """Create a new translation record."""
        self.session.add(translation)
        await self.session.commit()
        await self.session.refresh(translation)
        return translation

    async def update(self, translation: SchemeTranslation) -> SchemeTranslation:
        """Update an existing translation."""
        await self.session.commit()
        await self.session.refresh(translation)
        return translation

    async def mark_outdated(self, scheme_id: uuid.UUID) -> None:
        """Mark all translations for a scheme as OUTDATED (e.g. when original English updates)."""
        stmt = select(SchemeTranslation).where(SchemeTranslation.scheme_id == scheme_id)
        result = await self.session.execute(stmt)
        translations = result.scalars().all()
        for t in translations:
            t.status = TranslationStatusEnum.OUTDATED
        await self.session.commit()
