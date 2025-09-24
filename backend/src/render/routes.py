from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_session
from render.controller import RenderController
from render.schemas import RenderRequest, RenderResponse, RenderStatusResponse


router = APIRouter()
controller = RenderController()


@router.post("/{project_id}/render", response_model=RenderResponse, status_code=status.HTTP_202_ACCEPTED)
async def render_project(
    project_id: str,
    render_request: RenderRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Start rendering a video for a project."""
    # Create render task
    render_task = await controller.create_render_task(session, project_id, render_request)
    
    # TODO: Add the actual background rendering logic here
    # This would include:
    # 1. Get project sentences and footage
    # 2. Download footage files
    # 3. Create video segments
    # 4. Combine with audio and music
    # 5. Export final video
    
    # For now, we'll just create the task
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