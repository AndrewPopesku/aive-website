import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from render.controller import RenderController
from render.schemas import RenderRequest, RenderResponse, RenderStatusResponse

router = APIRouter()
controller = RenderController()
logger = logging.getLogger(__name__)


@router.post(
    "/{project_id}/render",
    response_model=RenderResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def render_project(
    project_id: str,
    render_request: RenderRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> RenderResponse:
    """Start rendering a video for a project."""
    import asyncio

    from base.config import get_settings
    from projects.controller import ProjectController
    from video_processing.services import find_background_music
    from video_processing.video_editor import render_project_video
    from video_processing.lambda_client import render_video_via_lambda

    settings = get_settings()
    project_controller = ProjectController()

    # Validate project exists and get project data
    project_details = await project_controller.get_project_with_details(
        session, project_id
    )

    # Check if all sentences have selected footage
    sentences = project_details["sentences"]
    if not all(
        s.get("selected_footage") and s["selected_footage"].get("url")
        for s in sentences
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not all sentences have selected footage. Please select footage for all sentences.",
        )

    # Create render task
    render_task = await controller.create_render_task(
        session, project_id, render_request
    )

    # Define the background rendering function
    async def render_video_task() -> None:
        # Create a new session for the background task
        from database.session import async_session_factory

        async with async_session_factory() as bg_session:
            try:
                # Update status to processing
                await controller.update_render_status(
                    bg_session, render_task.id, "processing", progress=10
                )

                # Get audio file path from project
                audio_file_path = project_details["audio_file_path"]
                if not audio_file_path or not os.path.exists(audio_file_path):
                    await controller.update_render_status(
                        bg_session,
                        render_task.id,
                        "failed",
                        error_message="Audio file not found",
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

                # Render the video - use Lambda if enabled
                if settings.use_lambda_rendering:
                    # Lambda rendering - requires publicly accessible URLs
                    # Upload audio file to S3 and get presigned URL
                    from video_processing.s3_client import get_presigned_url_for_file
                    
                    try:
                        logger.info("Uploading audio file to S3...")
                        # Generate unique S3 key for the audio file
                        audio_s3_key = f"audio/{project_id}/{Path(audio_file_path).name}"
                        audio_s3_key_result, audio_url = await get_presigned_url_for_file(
                            audio_file_path,
                            s3_key=audio_s3_key,
                            expiration=7200,  # 2 hours to allow for rendering
                        )
                        logger.info(f"Audio file uploaded to S3: {audio_s3_key_result}")
                        
                        # Upload music file to S3 if it's a local file
                        music_url = None
                        if music_file_path:
                            # Check if it's a relative API path (starts with /api/)
                            if music_file_path.startswith('/api/audio/'):
                                # Convert relative API path to absolute local file path
                                # /api/audio/file.mp3 -> /path/to/backend/static/audio/file.mp3
                                filename = music_file_path.replace('/api/audio/', '')
                                music_file_path = str(settings.audio_dir / filename)
                                logger.info(f"Converted relative music path to: {music_file_path}")
                            
                            if os.path.exists(music_file_path):
                                logger.info(f"Uploading music file to S3: {music_file_path}")
                                music_s3_key = f"music/{project_id}/{Path(music_file_path).name}"
                                music_s3_key_result, music_url = await get_presigned_url_for_file(
                                    music_file_path,
                                    s3_key=music_s3_key,
                                    expiration=7200,
                                )
                                logger.info(f"Music file uploaded to S3: {music_s3_key_result}")
                            elif music_file_path.startswith('http'):
                                # If music_file_path is already a URL, use it directly
                                music_url = music_file_path
                                logger.info(f"Using music URL directly: {music_url}")
                            else:
                                logger.warning(f"Music file not found at {music_file_path}, skipping background music")
                        
                        logger.info("Starting Lambda video rendering...")
                        # Debug: Log sentence data being sent to Lambda
                        logger.info(f"Project ID: {project_id}")
                        logger.info(f"Number of sentences: {len(project_details.get('sentences', []))}")
                        for idx, sent in enumerate(project_details.get('sentences', [])[:3]):
                            logger.info(f"Sentence {idx}: {sent.get('text', '')[:50]}...")
                            logger.info(f"  - selected_footage type: {type(sent.get('selected_footage'))}")
                            logger.info(f"  - selected_footage: {sent.get('selected_footage')}")
                            if sent.get('selected_footage'):
                                footage_url = sent.get('selected_footage', {}).get('url') if isinstance(sent.get('selected_footage'), dict) else None
                                logger.info(f"  - footage URL: {footage_url}")
                        
                        result = await render_video_via_lambda(
                            project_data=project_details,
                            audio_url=audio_url,
                            music_url=music_url,
                        )
                        
                        # Get video URL from Lambda result
                        video_url = result.get("video_url")
                        s3_key = result.get("s3_key")
                        
                        logger.info(f"Lambda rendering complete: {video_url}")
                        
                        # Update status to complete
                        await controller.update_render_status(
                            bg_session,
                            render_task.id,
                            "complete",
                            progress=100,
                            video_url=video_url,
                        )
                        
                        # Update project with video URL
                        await project_controller.update_entity(
                            bg_session, project_id, {"video_url": video_url}
                        )
                    except Exception as lambda_error:
                        logger.error(f"Lambda rendering failed: {str(lambda_error)}")
                        raise
                else:
                    # Local rendering (original method)
                    output_filename = f"{project_id}_final_video.mp4"
                    output_path = await render_project_video(
                        project_data=project_details,
                        audio_file_path=audio_file_path,
                        music_file_path=music_file_path,
                        output_filename=output_filename,
                    )
                    
                    # Extract the actual filename from the returned path
                    actual_filename = Path(output_path).name
                    relative_path = f"/api/videos/{actual_filename}"
                    
                    # Update status to complete
                    await controller.update_render_status(
                        bg_session,
                        render_task.id,
                        "complete",
                        progress=100,
                        video_url=relative_path,
                    )
                    
                    # Update project with video URL
                    await project_controller.update_entity(
                        bg_session, project_id, {"video_url": relative_path}
                    )

            except Exception as e:
                logger.error(f"Error in render task {render_task.id}: {str(e)}")
                await controller.update_render_status(
                    bg_session, render_task.id, "failed", error_message=str(e)
                )

    # Add the rendering task to background tasks
    background_tasks.add_task(render_video_task)

    # Return response
    base_url = str(request.base_url).rstrip("/")
    status_url = f"{base_url}/api/v1/render/status/{render_task.id}"

    return RenderResponse(render_task_id=render_task.id, status_url=status_url)


@router.get("/status/{task_id}", response_model=RenderStatusResponse)
async def get_render_status(
    task_id: str, session: AsyncSession = Depends(get_session)
) -> RenderStatusResponse:
    """Get the status of a render task."""
    status_info = await controller.get_render_status(session, task_id)

    return RenderStatusResponse(
        status=status_info["status"],
        video_url=status_info["video_url"],
        error=status_info["error"],
        progress=status_info["progress"],
    )


@router.get("/{project_id}/tasks", response_model=dict[str, Any])
async def get_project_render_tasks(
    project_id: str, session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    """Get all render tasks for a project."""
    return await controller.get_project_render_tasks(session, project_id)


@router.put("/status/{task_id}")
async def update_render_status(
    task_id: str,
    status_update: dict[str, Any],
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Update render task status (internal endpoint)."""
    updated_task = await controller.update_render_status(
        session=session,
        task_id=task_id,
        status=status_update.get("status"),
        progress=status_update.get("progress"),
        video_url=status_update.get("video_url"),
        error_message=status_update.get("error_message"),
    )

    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Render task with ID {task_id} not found",
        )

    return {"message": "Render task status updated successfully"}
