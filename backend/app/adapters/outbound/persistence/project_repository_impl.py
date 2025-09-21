from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from ....core.domain.entities.project import Project as ProjectEntity
from ....core.domain.repositories.project_repository import ProjectRepository
from ....infrastructure.database.models import Project as ProjectModel


class DatabaseProjectRepository(ProjectRepository):
    """Database implementation of ProjectRepository."""
    
    def __init__(self, db_session: Session):
        self._db = db_session
    
    async def create(self, project: ProjectEntity) -> ProjectEntity:
        """Create a new project in the database."""
        db_project = ProjectModel(
            id=project.id,
            title=project.title,
            description=project.description,
            audio_file_path=project.audio_file_path,
            total_duration=project.total_duration,
            overall_mood=project.overall_mood,
            video_url=project.video_url,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
        
        self._db.add(db_project)
        self._db.commit()
        self._db.refresh(db_project)
        
        return self._to_entity(db_project)
    
    async def get_by_id(self, project_id: str) -> Optional[ProjectEntity]:
        """Get a project by its ID."""
        db_project = self._db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not db_project:
            return None
        
        return self._to_entity(db_project)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ProjectEntity]:
        """Get all projects with pagination."""
        db_projects = self._db.query(ProjectModel).offset(skip).limit(limit).all()
        return [self._to_entity(db_project) for db_project in db_projects]
    
    async def update(self, project: ProjectEntity) -> ProjectEntity:
        """Update an existing project."""
        db_project = self._db.query(ProjectModel).filter(ProjectModel.id == project.id).first()
        if not db_project:
            raise ValueError(f"Project {project.id} not found")
        
        # Update fields
        db_project.title = project.title
        db_project.description = project.description
        db_project.audio_file_path = project.audio_file_path
        db_project.total_duration = project.total_duration
        db_project.overall_mood = project.overall_mood
        db_project.video_url = project.video_url
        db_project.updated_at = project.updated_at
        
        self._db.commit()
        self._db.refresh(db_project)
        
        return self._to_entity(db_project)
    
    async def delete(self, project_id: str) -> bool:
        """Delete a project by its ID."""
        db_project = self._db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not db_project:
            return False
        
        self._db.delete(db_project)
        self._db.commit()
        return True
    
    async def exists(self, project_id: str) -> bool:
        """Check if a project exists."""
        return self._db.query(ProjectModel).filter(ProjectModel.id == project_id).first() is not None
    
    def _to_entity(self, db_project: ProjectModel) -> ProjectEntity:
        """Convert database model to domain entity."""
        return ProjectEntity(
            id=db_project.id,
            title=db_project.title or "",
            description=db_project.description,
            audio_file_path=db_project.audio_file_path,
            total_duration=db_project.total_duration,
            overall_mood=db_project.overall_mood,
            video_url=db_project.video_url,
            created_at=db_project.created_at or datetime.utcnow(),
            updated_at=db_project.updated_at or datetime.utcnow()
        )