from abc import ABC, abstractmethod
from typing import Optional
from ..entities.render_task import RenderTask


class RenderTaskRepository(ABC):
    """Abstract repository for RenderTask entities."""
    
    @abstractmethod
    async def create(self, render_task: RenderTask) -> RenderTask:
        """Create a new render task."""
        pass
    
    @abstractmethod
    async def get_by_id(self, task_id: str) -> Optional[RenderTask]:
        """Get a render task by its ID."""
        pass
    
    @abstractmethod
    async def update(self, render_task: RenderTask) -> RenderTask:
        """Update an existing render task."""
        pass
    
    @abstractmethod
    async def get_completed_by_project_id(self, project_id: str) -> Optional[RenderTask]:
        """Get the most recent completed render task for a project."""
        pass