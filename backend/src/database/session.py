from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine
from base.config import get_settings

settings = get_settings()

# Create async engine for database operations
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session.
    
    Yields:
        AsyncSession: The database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_db_and_tables():
    """
    Create database and tables.
    This should be called during application startup.
    """
    async with async_engine.begin() as conn:
        # Import all models here to ensure they are registered with SQLModel
        from projects.models import Project, Sentence, FootageChoice, MusicRecommendation
        from render.models import RenderTask
        
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_db():
    """
    Close database connections.
    This should be called during application shutdown.
    """
    await async_engine.dispose()


# For use with Alembic migrations (sync engine)
sync_engine = create_engine(
    settings.database_url.replace("+asyncpg", ""),  # Remove async driver for sync operations
    echo=settings.debug,
)


def get_sync_session():
    """
    Get synchronous session for migrations and other sync operations.
    """
    from sqlmodel import Session
    return Session(sync_engine)