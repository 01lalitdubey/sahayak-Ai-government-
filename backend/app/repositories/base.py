"""
Generic Base Repository — Sahayak AI
======================================
Full async CRUD with pagination, filtering, and count support.
Every domain repository inherits this and gets all operations for free.
Pattern: Service layer calls Repository; Repository calls SQLAlchemy only.
"""

from typing import Any, Generic, Sequence, Type, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.database.database import Base

logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic async CRUD repository.

    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self, db: AsyncSession):
                super().__init__(User, db)
    """

    def __init__(self, model: Type[ModelType], db: AsyncSession) -> None:
        self._model = model
        self._db = db

    # ── Single record retrieval ────────────────────────────────────────────

    async def get_by_id(self, record_id: UUID) -> ModelType | None:
        """Fetch a single record by its UUID primary key."""
        result = await self._db.execute(
            select(self._model).where(self._model.id == record_id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def get_by_field(self, field: str, value: Any) -> ModelType | None:
        """Fetch a single record by an arbitrary column value."""
        column = getattr(self._model, field)
        result = await self._db.execute(
            select(self._model).where(column == value)
        )
        return result.scalar_one_or_none()

    # ── Collection retrieval ───────────────────────────────────────────────

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
    ) -> Sequence[ModelType]:
        """
        Return a page of records with optional simple equality filters.

        Args:
            skip:     offset (for pagination)
            limit:    max rows to return
            filters:  {column_name: value} equality conditions
            order_by: column name to sort by (ascending)
        """
        stmt = select(self._model)

        if filters:
            for field, value in filters.items():
                column = getattr(self._model, field, None)
                if column is not None:
                    stmt = stmt.where(column == value)

        if order_by:
            col = getattr(self._model, order_by, None)
            if col is not None:
                stmt = stmt.order_by(col)

        stmt = stmt.offset(skip).limit(limit)
        result = await self._db.execute(stmt)
        return result.scalars().all()

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Return total row count, optionally with equality filters."""
        stmt = select(func.count()).select_from(self._model)

        if filters:
            for field, value in filters.items():
                column = getattr(self._model, field, None)
                if column is not None:
                    stmt = stmt.where(column == value)

        result = await self._db.execute(stmt)
        return result.scalar_one()

    # ── Mutations ─────────────────────────────────────────────────────────

    async def create(self, instance: ModelType) -> ModelType:
        """
        Persist a new ORM instance.
        Flushes (not commits) so the caller controls the transaction boundary.
        Refreshes the instance so DB-generated values (id, timestamps) are visible.
        """
        try:
            self._db.add(instance)
            await self._db.flush()
            await self._db.refresh(instance)
            return instance
        except IntegrityError as exc:
            await self._db.rollback()
            logger.error("IntegrityError on create (%s): %s", self._model.__name__, exc)
            raise
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error("SQLAlchemyError on create (%s): %s", self._model.__name__, exc)
            raise

    async def update(self, instance: ModelType, data: dict[str, Any]) -> ModelType:
        """
        Apply a dictionary of field updates to an existing ORM instance.
        Only sets fields that actually exist on the model.
        """
        for field, value in data.items():
            if hasattr(instance, field):
                setattr(instance, field, value)
        try:
            await self._db.flush()
            await self._db.refresh(instance)
            return instance
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error("SQLAlchemyError on update (%s): %s", self._model.__name__, exc)
            raise

    async def delete(self, instance: ModelType) -> None:
        """Delete an ORM instance. Flushes but does not commit."""
        try:
            await self._db.delete(instance)
            await self._db.flush()
        except SQLAlchemyError as exc:
            await self._db.rollback()
            logger.error("SQLAlchemyError on delete (%s): %s", self._model.__name__, exc)
            raise

    async def exists(self, record_id: UUID) -> bool:
        """Return True if a record with the given UUID exists."""
        result = await self._db.execute(
            select(func.count())
            .select_from(self._model)
            .where(self._model.id == record_id)  # type: ignore[attr-defined]
        )
        return result.scalar_one() > 0
