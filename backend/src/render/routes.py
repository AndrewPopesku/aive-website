import os
import logging
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_session
from render.controller import RenderController
from render.schemas import RenderRequest, RenderResponse, RenderStatusResponse


router = APIRouter()
controller = RenderController()
logger = logging.getLogger(__name__)


@router.post("/{project_id}/render", response_model=RenderResponse, status_code=status.HTTP_202_ACCEPTED)
async def render_project(
    project_id: str,
    render_request: RenderRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Start rendering a video for a project."""
    from projects.controller import ProjectController
    from video_processing.video_editor import render_project_video
    from video_processing.services import find_background_music
    from base.config import get_settings
    import asyncio
    
    settings = get_settings()
    project_controller = ProjectController()
    
    # Validate project exists and get project data
    project_details = await project_controller.get_project_with_details(session, project_id)
    
    # Check if all sentences have selected footage
    sentences = project_details["sentences"]
    if not all(s.get("selected_footage") and s["selected_footage"].get("url") for s in sentences):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not all sentences have selected footage. Please select footage for all sentences."
        )
    
    # Create render task
    render_task = await controller.create_render_task(session, project_id, render_request)
    
    # Define the background rendering function
    async def render_video_task():
        # Create a new session for the background task
        from database.session import get_async_session
        async with get_async_session() as bg_session:
            try:
                # Update status to processing
                await controller.update_render_status(
                    bg_session, render_task.id, "processing", progress=10
                )
            
                # Get audio file path from project
                audio_file_path = project_details["audio_file_path"]
                if not audio_file_path or not os.path.exists(audio_file_path):
                    await controller.update_render_status(
                        bg_session, render_task.id, "failed", 
                        error_message="Audio file not found"
                    )
                    return
                
                # Update progress
                await controller.update_render_status(
                    bg_session, render_task.id, "processing", progress=25
                )
            
                # Find background music if not provided
                music_file_path = None
                music_recommendations = project_details.get("music_recommendations", [])
                
                if music_recommendations:
                    # Use the first music recommendation
                    music_file_path = music_recommendations[0].get("url")
                else:
                    # Find music from local directory
                    music_tracks = await find_background_music()
                    if music_tracks:
                        music_file_path = music_tracks[0]["url"]
                
                # Update progress
                await controller.update_render_status(
                    bg_session, render_task.id, "processing", progress=40
                )
                
                # Render the video
                output_filename = f"{project_id}_final_video.mp4"
                output_path = await render_project_video(
                    project_data=project_details,
                    audio_file_path=audio_file_path,
                    music_file_path=music_file_path,
                    output_filename=output_filename
                )
                
                # Extract the actual filename from the returned path
                actual_filename = Path(output_path).name
                relative_path = f"/api/videos/{actual_filename}"
                
                # Update status to complete
                await controller.update_render_status(
                    bg_session, render_task.id, "complete", 
                    progress=100, video_url=relative_path
                )
                
                # Update project with video URL
                await project_controller.update_entity(
                    bg_session, project_id, {"video_url": relative_path}
                )
                
            except Exception as e:
                logger.error(f"Error in render task {render_task.id}: {str(e)}")
                await controller.update_render_status(
                    bg_session, render_task.id, "failed", 
                    error_message=str(e)
                )
    
    # Add the rendering task to background tasks
    background_tasks.add_task(render_video_task)
    
    # Return response
    base_url = str(request.base_url).rstrip("/")
    status_url = f"{base_url}/api/v1/render/status/{render_task.id}"
    
    return RenderResponse(
        render_task_id=render_task.id,
        status_url=status_url
    )


@router.get("/status/{task_id}", response_model=RenderStatusResponse)
async def get_render_status(
    task_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get the status of a render task."""
    status_info = await controller.get_render_status(session, task_id)
    
    return RenderStatusResponse(
        status=status_info["status"],
        video_url=status_info["video_url"],
        error=status_info["error"],
        progress=status_info["progress"]
    )


@router.get("/{project_id}/tasks", response_model=Dict[str, Any])
async def get_project_render_tasks(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get all render tasks for a project."""
    return await controller.get_project_render_tasks(session, project_id)


@router.put("/status/{task_id}")
async def update_render_status(
    task_id: str,
    status_update: Dict[str, Any],
    session: AsyncSession = Depends(get_session)
):
    """Update render task status (internal endpoint)."""
    updated_task = await controller.update_render_status(
        session=session,
        task_id=task_id,
        status=status_update.get("status"),
        progress=status_update.get("progress"),
        video_url=status_update.get("video_url"),
        error_message=status_update.get("error_message")
    )
    
    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Render task with ID {task_id} not found"
        )
    
    return {"message": "Render task status updated successfully"}