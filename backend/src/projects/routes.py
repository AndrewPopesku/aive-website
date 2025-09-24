from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_session
from projects.controller import ProjectController
from projects.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse, 
    FootageChoices, MusicResponse, Sentence
)


router = APIRouter()
controller = ProjectController()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_projects(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session)
):
    """Get a list of all projects."""
    projects = await controller.get_entities(session, skip, limit)
    
    # Convert to response format with additional details
    result = []
    for project in projects:
        project_details = await controller.get_project_with_details(session, project.id)
        result.append(project_details)
    
    return result


@router.get("/{project_id}", response_model=Dict[str, Any])
async def get_project_details(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get details for a specific project."""
    return await controller.get_project_with_details(session, project_id)


@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_project(
    audio_file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    """Create a new project with audio file upload."""
    # This is a simplified version - in a full implementation,
    # you would handle the audio file upload, transcription, etc.
    # For now, we'll create a basic project structure
    
    from projects.schemas import generate_id
    from base.config import get_settings
    import shutil
    
    settings = get_settings()
    
    # Validate audio file
    if audio_file.content_type not in settings.allowed_audio_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Supported types: {settings.allowed_audio_types}"
        )
    
    # Generate project ID and save audio file
    project_id = generate_id("proj")
    audio_path = settings.temp_dir / f"{project_id}_{audio_file.filename}"
    
    # Save the audio file
    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)
    
    # Create project data
    project_data = ProjectCreate(
        id=project_id,
        title=f"Project {project_id}",
        audio_file_path=str(audio_path)
    )
    
    # Create the project
    project = await controller.create_project_with_audio(session, project_data)
    
    # Return project details
    return await controller.get_project_with_details(session, project.id)


@router.put("/{project_id}", response_model=Dict[str, Any])
async def update_project(
    project_id: str,
    project_data: Dict[str, Any],
    session: AsyncSession = Depends(get_session)
):
    """Update a project by ID."""
    await controller.update_entity(session, project_id, project_data)
    return await controller.get_project_with_details(session, project_id)


@router.patch("/{project_id}", response_model=Dict[str, Any])
async def patch_project(
    project_id: str,
    project_data: Dict[str, Any],
    session: AsyncSession = Depends(get_session)
):
    """Partially update a project by ID."""
    await controller.update_entity(session, project_id, project_data)
    return await controller.get_project_with_details(session, project_id)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Delete a project by ID."""
    await controller.delete_entity(session, project_id)
    return None


@router.post("/{project_id}/footage", response_model=MusicResponse)
async def submit_footage_choices(
    project_id: str,
    footage_choices: FootageChoices,
    session: AsyncSession = Depends(get_session)
):
    """Submit footage choices for sentences and get music recommendations."""
    # Validate project exists
    await controller.validate_entity_exists(session, project_id)
    
    # This would include the full footage processing logic
    # For now, return a basic response
    return MusicResponse(
        project_id=project_id,
        recommended_music=[]
    )