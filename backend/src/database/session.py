"""Database session management for the application."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from base.config import get_settings

__all__ = [
    "engine",
    "async_session_factory",
    "init_db",
    "create_db_and_tables",
    "close_db",
    "get_session",
    "get_async_session",
    "get_async_session_context",
]

# Get settings
settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize the database, creating all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def create_db_and_tables() -> None:
    """Create database tables - alias for init_db for backward compatibility."""
    await init_db()


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def get_async_session() -> async_sessionmaker[AsyncSession]:
    """Get the async session factory for use in background tasks.

    Usage:
        async with get_async_session()() as session:
            # Use session here
    """
    return async_session_factory


async def get_async_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session for background tasks.

    This is a convenience function that can be used directly with async with:
        async with get_async_session_context() as session:
            # Use session here
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
