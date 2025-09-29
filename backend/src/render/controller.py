from typing import Any, Dict, Optional

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from base.controller import BaseController
from render.models import RenderTask
from render.repository import RenderTaskRepository
from render.schemas import RenderRequest, RenderTaskCreate


class RenderController(BaseController[RenderTaskRepository]):
    """Controller for render task business logic."""

    def __init__(self):
        super().__init__(RenderTaskRepository())

    async def create_render_task(
        self, session: AsyncSession, project_id: str, render_request: RenderRequest
    ) -> RenderTask:
        """Create a new render task for a project."""
        # Create render task data
        task_data = RenderTaskCreate(project_id=project_id, status="pending", progress=0)

        # Create the render task
        task_dict = task_data.model_dump()
        return await self.repository.create(session, task_dict)

    async def get_render_status(self, session: AsyncSession, task_id: str) -> Dict[str, Any]:
        """Get render task status."""
        task = await self.get_entity(session, task_id)

        return {
            "status": task.status,
            "progress": task.progress,
            "video_url": task.output_file_path,
            "error": task.error_message,
        }

    async def update_render_status(
        self,
        session: AsyncSession,
        task_id: str,
        status: str,
        progress: Optional[int] = None,
        video_url: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[RenderTask]:
        """Update render task status."""
        return await self.repository.update_status(
            session=session,
            task_id=task_id,
            status=status,
            progress=progress,
            output_file_path=video_url,
            error_message=error_message,
        )

    async def get_project_render_tasks(self, session: AsyncSession, project_id: str) -> Dict[str, Any]:
        """Get all render tasks for a project."""
        tasks = await self.repository.get_by_project_id(session, project_id)

        return {
            "project_id": project_id,
            "tasks": [
                {
                    "id": task.id,
                    "status": task.status,
                    "progress": task.progress,
                    "output_file_path": task.output_file_path,
                    "error_message": task.error_message,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                }
                for task in tasks
            ],
        }

    async def get_latest_completed_render(self, session: AsyncSession, project_id: str) -> Optional[str]:
        """Get the latest completed render video URL for a project."""
        completed_tasks = await self.repository.get_completed_by_project_id(session, project_id)

        if completed_tasks:
            return completed_tasks[0].output_file_path

        return None
