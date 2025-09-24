from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from base.repository import BaseRepository
from render.models import RenderTask


class RenderTaskRepository(BaseRepository[RenderTask]):
    """Repository for render task-specific database operations."""
    
    def __init__(self):
        super().__init__(RenderTask)
    
    async def get_by_project_id(self, session: AsyncSession, project_id: str) -> List[RenderTask]:
        """Get all render tasks for a specific project."""
        statement = select(self.model).where(self.model.project_id == project_id)
        result = await session.exec(statement)
        return result.all()
    
    async def get_latest_by_project_id(self, session: AsyncSession, project_id: str) -> Optional[RenderTask]:
        """Get the latest render task for a specific project."""
        statement = (
            select(self.model)
            .where(self.model.project_id == project_id)
            .order_by(self.model.created_at.desc())
        )
        result = await session.exec(statement)
        return result.first()
    
    async def get_completed_by_project_id(self, session: AsyncSession, project_id: str) -> List[RenderTask]:
        """Get all completed render tasks for a specific project."""
        statement = (
            select(self.model)
            .where(self.model.project_id == project_id)
            .where(self.model.status == "complete")
            .order_by(self.model.created_at.desc())
        )
        result = await session.exec(statement)
        return result.all()
    
    async def update_status(
        self, 
        session: AsyncSession, 
        task_id: str, 
        status: str,
        progress: Optional[int] = None,
        output_file_path: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[RenderTask]:
        """Update render task status and related fields."""
        task = await self.get(session, task_id)
        if not task:
            return None
        
        task.status = status
        if progress is not None:
            task.progress = progress
        if output_file_path:
            task.output_file_path = output_file_path
        if error_message:
            task.error_message = error_message
        
        await session.commit()
        await session.refresh(task)
        return task