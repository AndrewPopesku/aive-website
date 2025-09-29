from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from base.repository import BaseRepository
from render.models import RenderTask


class RenderTaskRepository(BaseRepository[RenderTask]):
    """Repository for render task-specific database operations."""

    def __init__(self) -> None:
        super().__init__(RenderTask)

    async def get_by_project_id(
        self, session: AsyncSession, project_id: str
    ) -> list[RenderTask]:
        """Get all render tasks for a specific project."""
        statement = select(self.model).where(self.model.project_id == project_id)  # type: ignore
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_latest_by_project_id(
        self, session: AsyncSession, project_id: str
    ) -> RenderTask | None:
        """Get the latest render task for a specific project."""
        statement = (
            select(self.model)
            .where(self.model.project_id == project_id)  # type: ignore
            .order_by(self.model.created_at.desc())  # type: ignore
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_completed_by_project_id(
        self, session: AsyncSession, project_id: str
    ) -> list[RenderTask]:
        """Get all completed render tasks for a specific project."""
        statement = (
            select(self.model)
            .where(self.model.project_id == project_id)  # type: ignore
            .where(self.model.status == "complete")  # type: ignore
            .order_by(self.model.created_at.desc())  # type: ignore
        )
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def update_status(
        self,
        session: AsyncSession,
        task_id: str,
        status: str,
        progress: int | None = None,
        output_file_path: str | None = None,
        error_message: str | None = None,
    ) -> RenderTask | None:
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
