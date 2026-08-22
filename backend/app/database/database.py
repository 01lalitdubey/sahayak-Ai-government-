"""
Database Configuration — Sahayak AI Backend
============================================
SQLAlchemy 2.0 async engine with full production configuration.
- Async engine with connection pooling
- Session factory with automatic commit / rollback
- FastAPI dependency for per-request sessions
- Startup connectivity check
- Graceful shutdown
"""

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# ── Declarative Base ──────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """
    Single declarative base for ALL ORM models in the project.
    Every model in app/models/ must inherit from this class.
    Alembic reads Base.metadata for autogenerate.
    """
    pass


# ── Engine factory ────────────────────────────────────────────────────────
def _build_engine() -> AsyncEngine:
    """
    Build the async SQLAlchemy engine from application settings.
    Pool settings are fully configurable via environment variables.
    pool_pre_ping=True sends a lightweight SELECT before each checkout
    to detect stale connections (essential for long-running services).
    """
    # In development: echo can be toggled via DATABASE_ECHO; in dev defaults True
    echo = settings.DATABASE_ECHO if not settings.is_development else True

    return create_async_engine(
        settings.DATABASE_URL,
        echo=echo,
        future=True,
        # ── Connection pool ─────────────────────────────────────────────
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,
    )


engine: AsyncEngine = _build_engine()


# ── Session factory ────────────────────────────────────────────────────────
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # Safe for async — objects stay accessible after commit
)


# ── FastAPI request-scoped session dependency ──────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields one AsyncSession per HTTP request.

    Lifecycle:
      1. Session opened from pool
      2. Route handler executes (yield)
      3. On success  → commit
      4. On exception → rollback
      5. Session always closed and returned to pool

    Inject with:
        from fastapi import Depends
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.database.database import get_db

        async def my_route(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as exc:
            await session.rollback()
            logger.error("DB session rolled back due to SQLAlchemyError: %s", exc)
            raise
        except Exception as exc:
            await session.rollback()
            logger.error("DB session rolled back due to unexpected error: %s", exc)
            raise
        finally:
            await session.close()


# ── DB health check helper ─────────────────────────────────────────────────
async def check_db_connection() -> bool:
    """
    Runs SELECT 1 against the database.
    Returns True if the DB responds, False otherwise.
    Used by the /api/v1/database/health endpoint and startup probe.
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except OperationalError as exc:
        logger.error("Database connectivity check failed (OperationalError): %s", exc)
        return False
    except Exception as exc:
        logger.error("Database connectivity check failed (unexpected): %s", exc)
        return False


# ── Lifespan helpers ───────────────────────────────────────────────────────
async def init_db() -> None:
    """
    Called at application startup (FastAPI lifespan).
    Probes the database so we get a clear error on boot if unreachable.
    Does NOT run migrations — use `alembic upgrade head` for that.
    """
    logger.info("Verifying database connectivity...")
    reachable = await check_db_connection()
    if reachable:
        logger.info("✅ Database connection verified successfully")
    else:
        logger.warning(
            "⚠️  Database is NOT reachable at startup. "
            "The app will run but DB-dependent endpoints will fail. "
            "Check DATABASE_URL in .env and ensure PostgreSQL is running."
        )


async def close_db() -> None:
    """
    Called at application shutdown (FastAPI lifespan).
    Cleanly disposes the engine and all pooled connections.
    """
    await engine.dispose()
    logger.info("Database engine disposed — all connections closed")
