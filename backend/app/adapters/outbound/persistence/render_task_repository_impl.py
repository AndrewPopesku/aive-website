from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from ....core.domain.entities.render_task import RenderTask as RenderTaskEntity, RenderStatus
from ....core.domain.repositories.render_task_repository import RenderTaskRepository
from ....infrastructure.database.models import RenderTask as RenderTaskModel, RenderStatusEnum


class DatabaseRenderTaskRepository(RenderTaskRepository):
    """Database implementation of RenderTaskRepository."""
    
    def __init__(self, db_session: Session):
        self._db = db_session
    
    async def create(self, render_task: RenderTaskEntity) -> RenderTaskEntity:
        """Create a new render task."""
        # Map domain enum to database enum
        db_status = RenderStatusEnum(render_task.status.value)
        
        db_task = RenderTaskModel(
            id=render_task.id,
            project_id=render_task.project_id,
            status=db_status,
            progress=render_task.progress,
            output_file_path=render_task.output_file_path,
            error_message=render_task.error_message,
            created_at=render_task.created_at,
            updated_at=render_task.updated_at
        )
        
        self._db.add(db_task)
        self._db.commit()
        self._db.refresh(db_task)
        
        return self._to_entity(db_task)
    
    async def get_by_id(self, task_id: str) -> Optional[RenderTaskEntity]:
        """Get a render task by its ID."""
        db_task = self._db.query(RenderTaskModel).filter(
            RenderTaskModel.id == task_id
        ).first()
        
        if not db_task:
            return None
        
        return self._to_entity(db_task)
    
    async def update(self, render_task: RenderTaskEntity) -> RenderTaskEntity:
        """Update an existing render task."""
        db_task = self._db.query(RenderTaskModel).filter(
            RenderTaskModel.id == render_task.id
        ).first()
        
        if not db_task:
            raise ValueError(f"Render task {render_task.id} not found")
        
        # Update fields
        db_task.status = RenderStatusEnum(render_task.status.value)
        db_task.progress = render_task.progress
        db_task.output_file_path = render_task.output_file_path
        db_task.error_message = render_task.error_message
        db_task.updated_at = render_task.updated_at
        
        self._db.commit()
        self._db.refresh(db_task)
        
        return self._to_entity(db_task)
    
    async def get_completed_by_project_id(self, project_id: str) -> Optional[RenderTaskEntity]:
        """Get the most recent completed render task for a project."""
        db_task = self._db.query(RenderTaskModel).filter(
            RenderTaskModel.project_id == project_id,
            RenderTaskModel.status == "complete"
        ).order_by(RenderTaskModel.updated_at.desc()).first()
        
        if not db_task:
            return None
        
        return self._to_entity(db_task)
    
    def _to_entity(self, db_task: RenderTaskModel) -> RenderTaskEntity:
        """Convert database model to domain entity."""
        # Map database enum to domain enum
        domain_status = RenderStatus(db_task.status.value) if db_task.status else RenderStatus.PENDING
        
        return RenderTaskEntity(
            id=db_task.id,
            project_id=db_task.project_id,
            status=domain_status,
            progress=db_task.progress or 0,
            output_file_path=db_task.output_file_path,
            error_message=db_task.error_message,
            created_at=db_task.created_at or datetime.utcnow(),
            updated_at=db_task.updated_at or datetime.utcnow()
        )
