import os
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, Request, status
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import logging

from ....core.application.services.project_service import ProjectService
from ....core.application.services.render_service import RenderService
from ....infrastructure.dto.project_dto import (
    FootageChoicesDTO, RenderRequestDTO, RenderResponseDTO, RenderStatusResponseDTO
)
from ....config import TEMP_DIR, ALLOWED_AUDIO_TYPES
from ....database import get_db

logger = logging.getLogger(__name__)


class ProjectController:
    """REST controller for project-related endpoints."""
    
    def __init__(self, project_service: ProjectService, render_service: RenderService):
        self._project_service = project_service
        self._render_service = render_service
        self.router = self._create_router()
    
    def _create_router(self) -> APIRouter:
        """Create and configure the FastAPI router."""
        router = APIRouter()
        
        # Register all endpoints
        router.get("/", response_model=List[Dict[str, Any]])(self.get_all_projects)
        router.get("/{project_id}", response_model=Dict[str, Any])(self.get_project_details)
        router.post("/", response_model=Dict[str, Any])(self.create_project)
        router.post("/{project_id}/footage", response_model=Dict[str, Any])(self.submit_footage_choices)
        router.post("/{project_id}/render", response_model=RenderResponseDTO, status_code=status.HTTP_202_ACCEPTED)(self.render_project)
        router.get("/render/status/{render_task_id}", response_model=RenderStatusResponseDTO)(self.get_render_status)
        router.put("/{project_id}", response_model=Dict[str, Any])(self.update_project)
        router.patch("/{project_id}", response_model=Dict[str, Any])(self.patch_project)
        router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)(self.delete_project)
        
        return router
    
    async def get_all_projects(
        self,
        skip: int = 0, 
        limit: int = 100,
        db: Session = Depends(get_db)
    ):
        """Get a list of all projects."""
        try:
            # Initialize services with database session
            self._initialize_services(db)
            projects = await self._project_service.get_all_projects(skip, limit)
            return projects
        except Exception as e:
            logger.error(f"Error getting projects: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve projects: {str(e)}"
            )
    
    async def get_project_details(
        self,
        project_id: str,
        db: Session = Depends(get_db)
    ):
        """Get details for a specific project."""
        try:
            self._initialize_services(db)
            project_details = await self._project_service.get_project_details(project_id)
            if not project_details:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project with ID {project_id} not found"
                )
            return project_details
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting project details: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve project details: {str(e)}"
            )
    
    async def create_project(
        self,
        audio_file: UploadFile = File(...),
        db: Session = Depends(get_db)
    ):
        """Create a new project with audio file, transcribe it, and get footage recommendations."""
        # Validate audio file
        if audio_file.content_type not in ALLOWED_AUDIO_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Supported types: {ALLOWED_AUDIO_TYPES}"
            )
        
        # Generate temporary path for audio
        audio_path = TEMP_DIR / f"temp_{audio_file.filename}"
        
        try:
            # Save the audio file
            with open(audio_path, "wb") as buffer:
                shutil.copyfileobj(audio_file.file, buffer)
            
            self._initialize_services(db)
            
            # Create project using application service
            result = await self._project_service.create_project(
                title=f"Project from {audio_file.filename}",
                audio_file_path=str(audio_path),
                description=None
            )
            
            # Convert sentences to legacy format for response compatibility
            sentences = []
            for sentence in result["sentences"]:
                sentence_dict = {
                    "sentence_id": sentence.id,
                    "text": sentence.text,
                    "translated_text": sentence.translated_text,
                    "start": sentence.start_time,
                    "end": sentence.end_time,
                    "selected_footage": sentence.selected_footage
                }
                sentences.append(sentence_dict)
            
            return {
                "project_id": result["project_id"],
                "sentences": sentences
            }
        except Exception as e:
            logger.error(f"Error in create_project: {str(e)}")
            # Clean up any created files
            if os.path.exists(audio_path):
                os.remove(audio_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create project: {str(e)}"
            )
    
    async def submit_footage_choices(
        self,
        project_id: str,
        footage_choices: FootageChoicesDTO,
        db: Session = Depends(get_db)
    ):
        """Submit footage choices for sentences and get music recommendations."""
        try:
            self._initialize_services(db)
            
            # Convert footage choices to the format expected by application service
            choices_data = []
            for choice in footage_choices.footage_choices:
                choices_data.append({
                    "sentence_id": choice.sentence_id,
                    "footage_url": str(choice.footage_url)
                })
            
            music_recommendations = await self._project_service.submit_footage_choices(
                project_id, choices_data
            )
            
            # Convert to legacy format
            recommended_music = []
            for music in music_recommendations:
                recommended_music.append({
                    "id": music.id,
                    "name": music.title,
                    "url": music.url
                })
            
            return {
                "project_id": project_id,
                "recommended_music": recommended_music
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error in submit_footage_choices: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to submit footage choices: {str(e)}"
            )
    
    async def render_project(
        self,
        background_tasks: BackgroundTasks,
        project_id: str,
        render_request: RenderRequestDTO,
        request: Request,
        db: Session = Depends(get_db)
    ):
        """Render the final video with selected footage and music."""
        try:
            self._initialize_services(db)
            
            # Start the render process
            render_task = await self._render_service.start_render(
                project_id, 
                render_request.add_subtitles, 
                render_request.include_audio
            )
            
            # Process render in background
            async def render_task_background():
                try:
                    await self._render_service.process_render(
                        render_task.id,
                        render_request.add_subtitles,
                        render_request.include_audio
                    )
                except Exception as e:
                    logger.error(f"Background render task failed: {str(e)}")
            
            background_tasks.add_task(render_task_background)
            
            # Return the render task ID and status URL
            base_url = str(request.base_url).rstrip("/")
            status_url = f"{base_url}/api/v1/projects/render/status/{render_task.id}"
            
            return RenderResponseDTO(
                render_task_id=render_task.id,
                status_url=status_url
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error in render_project: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to render project: {str(e)}"
            )
    
    async def get_render_status(
        self,
        render_task_id: str,
        db: Session = Depends(get_db)
    ):
        """Get the status of a render task."""
        try:
            self._initialize_services(db)
            
            status_data = await self._render_service.get_render_status(render_task_id)
            if not status_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Render task with ID {render_task_id} not found"
                )
            
            return RenderStatusResponseDTO(
                status=status_data["status"],
                video_url=status_data["video_url"],
                error=status_data["error"]
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_render_status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get render status: {str(e)}"
            )
    
    async def update_project(
        self,
        project_id: str,
        project_data: Dict[str, Any],
        db: Session = Depends(get_db)
    ):
        """Update a project by ID."""
        try:
            self._initialize_services(db)
            
            updated_project = await self._project_service.update_project(project_id, project_data)
            if not updated_project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project with ID {project_id} not found"
                )
            
            return await self.get_project_details(project_id, db)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating project: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update project: {str(e)}"
            )
    
    async def patch_project(
        self,
        project_id: str,
        project_data: Dict[str, Any],
        db: Session = Depends(get_db)
    ):
        """Partially update a project by ID."""
        return await self.update_project(project_id, project_data, db)
    
    async def delete_project(
        self,
        project_id: str,
        db: Session = Depends(get_db)
    ):
        """Delete a project by ID."""
        try:
            self._initialize_services(db)
            
            success = await self._project_service.delete_project(project_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project with ID {project_id} not found"
                )
            
            return None
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting project: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete project: {str(e)}"
            )
    
    def _initialize_services(self, db: Session):
        """Initialize services with database session (temporary approach)."""
        # This is a temporary approach - in the final dependency injection system,
        # services will be properly injected with their dependencies
        pass