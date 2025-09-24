import pytest
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from backend.src.main import app
from src.database.session import get_session
from src.base.config import get_settings

# Test database URL (in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# Create test session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with test_engine.begin() as conn:
        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
def test_client(test_session: AsyncSession) -> TestClient:
    """Create a test client with database session override."""
    
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield test_session
    
    app.dependency_overrides[get_session] = override_get_session
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings():
    """Get test settings."""
    return get_settings()


@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "title": "Test Project",
        "description": "A test project for unit testing",
        "audio_file_path": "/tmp/test_audio.mp3"
    }


@pytest.fixture
def sample_sentence_data():
    """Sample sentence data for testing."""
    return {
        "text": "This is a test sentence.",
        "translated_text": "This is a test sentence.",
        "start_time": 0.0,
        "end_time": 3.0
    }


@pytest.fixture
def sample_render_task_data():
    """Sample render task data for testing."""
    return {
        "project_id": "test-project-id",
        "status": "pending",
        "progress": 0
    }