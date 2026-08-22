"""
EligibilityRule Repository — Sahayak AI (Extended Phase 5)
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.eligibility_rule import EligibilityRule
from app.models.scheme import Scheme
from app.repositories.base import BaseRepository


class EligibilityRepository(BaseRepository[EligibilityRule]):

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(EligibilityRule, db)

    async def get_rules_for_scheme(self, scheme_id: uuid.UUID) -> list[EligibilityRule]:
        result = await self._db.execute(
            select(EligibilityRule)
            .where(EligibilityRule.scheme_id == scheme_id)
            .order_by(EligibilityRule.created_at)
        )
        return list(result.scalars().all())

    async def get_all_rules(
        self, *, scheme_id: uuid.UUID | None = None, skip: int = 0, limit: int = 100
    ) -> list[EligibilityRule]:
        stmt = select(EligibilityRule)
        if scheme_id:
            stmt = stmt.where(EligibilityRule.scheme_id == scheme_id)
        stmt = stmt.order_by(EligibilityRule.created_at).offset(skip).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def count_rules(self, scheme_id: uuid.UUID | None = None) -> int:
        return await self.count(
            filters={"scheme_id": scheme_id} if scheme_id else None
        )

    async def create_rule(self, data: dict[str, Any]) -> EligibilityRule:
        rule = EligibilityRule(**data)
        return await self.create(rule)

    async def update_rule(
        self, rule_id: uuid.UUID, data: dict[str, Any]
    ) -> EligibilityRule | None:
        rule = await self.get_by_id(rule_id)
        if not rule:
            return None
        return await self.update(rule, data)

    async def delete_rule(self, rule_id: uuid.UUID) -> bool:
        rule = await self.get_by_id(rule_id)
        if not rule:
            return False
        await self.delete(rule)
        return True

    async def delete_rules_for_scheme(self, scheme_id: uuid.UUID) -> int:
        rules = await self.get_rules_for_scheme(scheme_id)
        for rule in rules:
            await self._db.delete(rule)
        await self._db.flush()
        return len(rules)

    async def get_active_schemes_with_rules(self) -> list[Scheme]:
        """Return all active schemes that have at least one eligibility rule."""
        result = await self._db.execute(
            select(Scheme)
            .options(selectinload(Scheme.eligibility_rules))
            .where(Scheme.is_active == True)  # noqa: E712
            .order_by(Scheme.name)
        )
        return [s for s in result.scalars().unique().all() if s.eligibility_rules]
