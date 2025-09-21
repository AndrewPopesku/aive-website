from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.project import Project


class ProjectRepository(ABC):
    """Abstract repository for Project entities."""
    
    @abstractmethod
    async def create(self, project: Project) -> Project:
        """Create a new project."""
        pass
    
    @abstractmethod
    async def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get a project by its ID."""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get all projects with pagination."""
        pass
    
    @abstractmethod
    async def update(self, project: Project) -> Project:
        """Update an existing project."""
        pass
    
    @abstractmethod
    async def delete(self, project_id: str) -> bool:
        """Delete a project by its ID."""
        pass
    
    @abstractmethod
    async def exists(self, project_id: str) -> bool:
        """Check if a project exists."""
        pass