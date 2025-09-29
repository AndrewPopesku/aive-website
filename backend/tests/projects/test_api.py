import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestProjectsAPI:
    """Test cases for Projects API endpoints."""

    def test_health_check(self, test_client: TestClient):
        """Test health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_get_projects_empty(self, test_client: TestClient):
        """Test getting projects when database is empty."""
        response = test_client.get("/api/v1/projects/")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_project_without_file(self, test_client: TestClient):
        """Test creating a project without audio file should fail."""
        response = test_client.post("/api/v1/projects/")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_project_repository_methods(self, test_session: AsyncSession):
        """Test project repository methods."""
        from src.projects.models import Project
        from src.projects.repository import ProjectRepository

        repo = ProjectRepository()

        # Test create
        project_data = {
            "id": "test-proj-1",
            "title": "Test Project",
            "description": "A test project",
            "audio_file_path": "/tmp/test.mp3",
        }

        project = await repo.create(test_session, project_data)
        assert project.id == "test-proj-1"
        assert project.title == "Test Project"

        # Test get
        retrieved_project = await repo.get(test_session, "test-proj-1")
        assert retrieved_project is not None
        assert retrieved_project.title == "Test Project"

        # Test get by title
        project_by_title = await repo.get_by_title(test_session, "Test Project")
        assert project_by_title is not None
        assert project_by_title.id == "test-proj-1"

        # Test get_all
        all_projects = await repo.get_all(test_session)
        assert len(all_projects) == 1

        # Test update
        updated_project = await repo.update(
            test_session, "test-proj-1", {"description": "Updated description"}
        )
        assert updated_project.description == "Updated description"

        # Test exists
        exists = await repo.exists(test_session, "test-proj-1")
        assert exists is True

        # Test delete
        deleted = await repo.delete(test_session, "test-proj-1")
        assert deleted is True

        # Verify deletion
        deleted_project = await repo.get(test_session, "test-proj-1")
        assert deleted_project is None


class TestProjectController:
    """Test cases for Project Controller."""

    @pytest.mark.asyncio
    async def test_create_project_with_audio(self, test_session: AsyncSession):
        """Test creating a project with audio file."""
        from src.projects.controller import ProjectController
        from src.projects.schemas import ProjectCreate

        controller = ProjectController()

        project_data = ProjectCreate(
            title="Test Project",
            description="Test description",
            audio_file_path="/tmp/test.mp3",
        )

        project = await controller.create_project_with_audio(test_session, project_data)
        assert project.title == "Test Project"
        assert project.audio_file_path == "/tmp/test.mp3"

    @pytest.mark.asyncio
    async def test_get_project_with_details(self, test_session: AsyncSession):
        """Test getting project with all related data."""
        from src.projects.controller import ProjectController
        from src.projects.schemas import ProjectCreate

        controller = ProjectController()

        # Create a project first
        project_data = ProjectCreate(
            title="Test Project",
            description="Test description",
            audio_file_path="/tmp/test.mp3",
        )

        project = await controller.create_project_with_audio(test_session, project_data)

        # Get project details
        details = await controller.get_project_with_details(test_session, project.id)

        assert details["id"] == project.id
        assert details["title"] == "Test Project"
        assert details["sentences"] == []
        assert details["footage_choices"] == []
        assert details["music_recommendations"] == []
