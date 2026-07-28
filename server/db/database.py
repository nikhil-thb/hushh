"""
Async SQLAlchemy engine, session factory, and dependency injection.

Design
------
- Uses ``create_async_engine`` with ``aiosqlite`` (SQLite) or ``asyncpg`` (PG).
- Provides ``get_session`` as a FastAPI dependency that yields an
  ``AsyncSession`` and commits/rolls back automatically.
- ``Base`` is the declarative base class for all ORM models.
- ``init_db`` is called at application startup to create tables (dev) or
  validate the schema (prod via Alembic).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from server.config import get_settings

logger = structlog.get_logger(__name__)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


# Engine & session factory are created lazily at first access.
_engine = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine():  # type: ignore[return]
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args: dict[str, object] = {}
        if settings.database_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}

        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    return _engine


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            _get_engine(),
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _async_session_factory


async def init_db() -> None:
    """
    Create all tables from ORM metadata.

    In production, prefer running ``alembic upgrade head`` instead.
    This function is safe to call on every startup (no-op if tables exist).
    """
    # Import models so metadata is populated
    from server.models import tunnel, user  # noqa: F401

    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database.init", message="Tables created / verified.")


async def close_db() -> None:
    """Dispose the engine connection pool."""
    engine = _get_engine()
    await engine.dispose()
    logger.info("database.close", message="Database connection pool disposed.")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session.

    Automatically commits on success and rolls back on exception.
    """
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
