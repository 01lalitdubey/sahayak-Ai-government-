"""
Scheme Repository — Sahayak AI (Phase 4)
=========================================
Extended repository — all SQL for scheme management lives here.
Service layer calls this; routes never touch SQLAlchemy directly.
"""

import uuid
from datetime import date
from typing import Any

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.scheme import Scheme
from app.models.enums import SchemeCategoryEnum, SchemeTypeEnum, ApplicationModeEnum
from app.repositories.base import BaseRepository
from app.core.logging import get_logger

logger = get_logger(__name__)

# Ordered sort expressions
_SORT_MAP: dict[str, Any] = {
    "newest":           lambda: Scheme.created_at.desc(),
    "oldest":           lambda: Scheme.created_at.asc(),
    "alphabetical":     lambda: Scheme.name.asc(),
    "most_viewed":      lambda: Scheme.view_count.desc(),
    "recently_updated": lambda: Scheme.updated_at.desc(),
}


class SchemeRepository(BaseRepository[Scheme]):

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Scheme, db)

    # ── Lookup helpers ────────────────────────────────────────────────────

    async def get_by_code(self, scheme_code: str) -> Scheme | None:
        """Fetch by unique scheme_code (case-insensitive)."""
        result = await self._db.execute(
            select(Scheme).where(
                func.upper(Scheme.scheme_code) == scheme_code.upper()
            )
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str, state: str | None = None) -> Scheme | None:
        """Fetch by name + state scope (unique constraint)."""
        stmt = select(Scheme).where(
            func.lower(Scheme.name) == name.lower()
        )
        if state is not None:
            stmt = stmt.where(Scheme.state == state)
        else:
            stmt = stmt.where(Scheme.state == None)  # noqa: E711
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def code_exists(self, scheme_code: str, exclude_id: uuid.UUID | None = None) -> bool:
        stmt = select(func.count()).select_from(Scheme).where(
            func.upper(Scheme.scheme_code) == scheme_code.upper()
        )
        if exclude_id:
            stmt = stmt.where(Scheme.id != exclude_id)
        result = await self._db.execute(stmt)
        return result.scalar_one() > 0

    async def name_exists(
        self,
        name: str,
        state: str | None,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        stmt = select(func.count()).select_from(Scheme).where(
            func.lower(Scheme.name) == name.lower(),
        )
        if state is not None:
            stmt = stmt.where(Scheme.state == state)
        else:
            stmt = stmt.where(Scheme.state == None)  # noqa: E711
        if exclude_id:
            stmt = stmt.where(Scheme.id != exclude_id)
        result = await self._db.execute(stmt)
        return result.scalar_one() > 0

    # ── Paginated search + filter ─────────────────────────────────────────

    async def search(
        self,
        *,
        query: str | None = None,
        category: SchemeCategoryEnum | None = None,
        scheme_type: SchemeTypeEnum | None = None,
        application_mode: ApplicationModeEnum | None = None,
        state: str | None = None,
        ministry: str | None = None,
        is_featured: bool | None = None,
        is_active: bool | None = True,
        date_from: date | None = None,
        date_to: date | None = None,
        sort: str = "newest",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Scheme], int]:
        """
        Full-text search + multi-filter + pagination.
        Returns (items, total_count) tuple.
        """
        stmt = select(Scheme)
        count_stmt = select(func.count()).select_from(Scheme)

        conditions = []

        # Full-text search across key text fields
        if query:
            like = f"%{query}%"
            conditions.append(
                or_(
                    Scheme.name.ilike(like),
                    Scheme.short_description.ilike(like),
                    Scheme.full_description.ilike(like),
                    Scheme.benefits.ilike(like),
                    Scheme.ministry.ilike(like),
                    Scheme.department.ilike(like),
                )
            )

        if category is not None:
            conditions.append(Scheme.category == category)
        if scheme_type is not None:
            conditions.append(Scheme.scheme_type == scheme_type)
        if application_mode is not None:
            conditions.append(Scheme.application_mode == application_mode)
        if state is not None:
            conditions.append(
                or_(Scheme.state == state, Scheme.state == None)  # noqa: E711
            )
        if ministry is not None:
            conditions.append(Scheme.ministry.ilike(f"%{ministry}%"))
        if is_featured is not None:
            conditions.append(Scheme.is_featured == is_featured)
        if is_active is not None:
            conditions.append(Scheme.is_active == is_active)
        if date_from is not None:
            conditions.append(Scheme.application_start_date >= date_from)
        if date_to is not None:
            conditions.append(Scheme.application_end_date <= date_to)

        if conditions:
            for cond in conditions:
                stmt = stmt.where(cond)
                count_stmt = count_stmt.where(cond)

        # Sorting
        order_fn = _SORT_MAP.get(sort, _SORT_MAP["newest"])
        stmt = stmt.order_by(order_fn())

        # Count (before pagination)
        total_result = await self._db.execute(count_stmt)
        total = total_result.scalar_one()

        # Pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self._db.execute(stmt)
        return list(result.scalars().all()), total

    # ── Specific list queries ─────────────────────────────────────────────

    async def get_featured(self, *, limit: int = 10) -> list[Scheme]:
        """Return is_featured=True + is_active=True, most viewed first."""
        result = await self._db.execute(
            select(Scheme)
            .where(Scheme.is_featured == True, Scheme.is_active == True)  # noqa: E712
            .order_by(Scheme.view_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(self, *, limit: int = 10) -> list[Scheme]:
        """Return the N most recently added active schemes."""
        result = await self._db.execute(
            select(Scheme)
            .where(Scheme.is_active == True)  # noqa: E712
            .order_by(Scheme.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_schemes(
        self, *, skip: int = 0, limit: int = 100
    ) -> list[Scheme]:
        result = await self._db.execute(
            select(Scheme)
            .where(Scheme.is_active == True)  # noqa: E712
            .order_by(Scheme.name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_category(
        self, category: SchemeCategoryEnum, *, skip: int = 0, limit: int = 100
    ) -> list[Scheme]:
        result = await self._db.execute(
            select(Scheme)
            .where(Scheme.category == category, Scheme.is_active == True)  # noqa: E712
            .order_by(Scheme.name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_state(
        self, state: str, *, skip: int = 0, limit: int = 100
    ) -> list[Scheme]:
        result = await self._db.execute(
            select(Scheme)
            .where(
                Scheme.is_active == True,  # noqa: E712
                or_(Scheme.state == state, Scheme.state == None),  # noqa: E711
            )
            .order_by(Scheme.name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_rules(self, scheme_id: uuid.UUID) -> Scheme | None:
        result = await self._db.execute(
            select(Scheme)
            .options(selectinload(Scheme.eligibility_rules))
            .where(Scheme.id == scheme_id)
        )
        return result.scalar_one_or_none()

    # ── Distinct values (for filter dropdowns) ────────────────────────────

    async def get_distinct_states(self) -> list[str]:
        """Return sorted list of distinct non-null state values."""
        result = await self._db.execute(
            select(Scheme.state)
            .where(Scheme.state != None, Scheme.is_active == True)  # noqa: E711, E712
            .distinct()
            .order_by(Scheme.state)
        )
        return [row[0] for row in result.all()]

    # ── Mutations ─────────────────────────────────────────────────────────

    async def soft_delete(self, scheme: Scheme) -> Scheme:
        """Set is_active=False (hidden from public, recoverable)."""
        scheme.is_active = False
        await self._db.flush()
        await self._db.refresh(scheme)
        logger.info("Scheme soft-deleted: %s (%s)", scheme.scheme_code, scheme.id)
        return scheme

    async def restore(self, scheme: Scheme) -> Scheme:
        """Restore a soft-deleted scheme."""
        scheme.is_active = True
        await self._db.flush()
        await self._db.refresh(scheme)
        logger.info("Scheme restored: %s (%s)", scheme.scheme_code, scheme.id)
        return scheme

    async def increment_view_count(self, scheme_id: uuid.UUID) -> None:
        """
        Atomic counter increment using UPDATE ... SET view_count = view_count + 1.
        Does NOT load the full object — minimal DB overhead.
        """
        await self._db.execute(
            update(Scheme)
            .where(Scheme.id == scheme_id)
            .values(view_count=Scheme.view_count + 1)
        )
        # No flush needed — will be committed with the session
