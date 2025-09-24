import os
from pathlib import Path
from app.video_editor import VideoEditor
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, Request, status
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import shutil
import logging

from app.schemas import (
    Sentence, FootageChoices, ProjectResponse, MusicResponse, 
    RenderRequest, RenderResponse, RenderStatusResponse,
    SelectedFootage, generate_id, SentenceCreate, ProjectCreate,
    MusicRecommendationCreate, RenderTaskCreate
)
from app.services import (
    transcribe_audio, find_footage_for_sentence,
    find_background_music, render_final_video
)
from app.config import TEMP_DIR, OUTPUT_DIR, ALLOWED_AUDIO_TYPES, AUDIO_DIR
from app.database import get_db
from app.models import RenderTask, Project
from app.db_service import (
    create_project as db_create_project, get_project, create_sentences, get_sentences,
    create_footage_choices, get_footage_choices, create_music_recommendations,
    get_music_recommendations, create_render_task, get_render_task,
    update_render_task_status, db_sentence_to_schema, db_project_to_dict,
    validate_project_exists, list_projects, get_project_with_all_data,
    update_project, delete_project
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper to validate project_id exists
def validate_project_exists(db: Session, project_id: str):
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    return project

# Add new route to list all projects
@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_projects(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get a list of all projects
    """
    try:
        # Get list of projects from database
        projects = list_projects(db, skip=skip, limit=limit)
        
        # Convert projects to response format
        project_list = []
        for project in projects:
            # Get sentences for this project to include sentence count
            sentences = get_sentences(db, project.id)
            
            # Use the project's video_url field directly
            video_url = project.video_url
            
            # If no video_url in project, check render tasks as fallback
            if not video_url:
                render_tasks = db.query(RenderTask).filter(
                    RenderTask.project_id == project.id,
                    RenderTask.status == "complete"
                ).all()
                
                if render_tasks:
                    # Use the most recent completed render
                    video_url = render_tasks[-1].output_file_path
            
            project_list.append(db_project_to_dict(project, sentences, video_url))
            
        return project_list
    except Exception as e:
        logger.error(f"Error getting projects: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve projects: {str(e)}"
        )

# Add new route to get project details
@router.get("/{project_id}", response_model=Dict[str, Any])
async def get_project_details(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get details for a specific project
    """
    try:
        # Validate project exists
        project = get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        # Get all project data
        sentences = get_sentences(db, project_id)
        footage_choices = get_footage_choices(db, project_id)
        music_recommendations = get_music_recommendations(db, project_id)
        
        # Get render tasks to find video URL if not in project
        video_url = project.video_url
        if not video_url:
            render_tasks = db.query(RenderTask).filter(
                RenderTask.project_id == project_id,
                RenderTask.status == "complete"
            ).all()
            
            if render_tasks:
                # Use the most recent completed render
                video_url = render_tasks[-1].output_file_path
        
        return db_project_to_dict(project, sentences, video_url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve project details: {str(e)}"
        )

@router.post("/", response_model=ProjectResponse)
async def create_project(
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Step A: Create a new project with audio file, transcribe it, and get footage recommendations.
    """
    # Validate audio file
    if audio_file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Supported types: {ALLOWED_AUDIO_TYPES}"
        )
    
    # Generate project ID and temporary path for audio
    project_id = generate_id("proj")
    audio_path = TEMP_DIR / f"{project_id}_{audio_file.filename}"
    
    try:
        # Save the audio file
        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        # Transcribe audio to get sentences with timestamps
        sentences = await transcribe_audio(str(audio_path))
        
        if not sentences:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to transcribe audio"
            )
        
        # For each sentence, find recommended footage and set as selected by default
        for sentence in sentences:
            footage_url = await find_footage_for_sentence(sentence.text)
            sentence.recommended_footage_url = footage_url
            
            # Create default selected footage from recommendation
            if footage_url:
                # Extract video ID from URL for unique identifier
                video_id = footage_url.split('/')[-2] if '/' in footage_url else 'video'
                
                selected_footage = SelectedFootage(
                    id=f"footage-{sentence.sentence_id}-recommended",
                    title=f"{sentence.text[:35]}{'...' if len(sentence.text) > 35 else ''}",
                    description="AI-recommended footage from Pexels based on content analysis",
                    thumbnail="/placeholder.svg",  # Would need proper Pexels integration for thumbnails
                    duration=sentence.end - sentence.start,
                    tags=["ai-recommended", "pexels", "relevant"],
                    category="recommended",
                    mood="neutral",
                    relevance_score=95,
                    url=footage_url
                )
                sentence.selected_footage = selected_footage

        # Create project in database
        from app.schemas import ProjectCreate, SentenceCreate
        project_data = ProjectCreate(
            id=project_id,
            title=f"Project {project_id}",
            description=None,
            audio_file_path=str(audio_path)
        )
        db_project = db_create_project(db, project_data)
        
        # Convert sentences to SentenceCreate objects
        sentence_creates = []
        for sentence in sentences:
            sentence_create = SentenceCreate(
                text=sentence.text,
                start_time=sentence.start,
                end_time=sentence.end,
                selected_footage=sentence.selected_footage
            )
            sentence_creates.append(sentence_create)
        
        # Save sentences to database
        db_sentences = create_sentences(db, project_id, sentence_creates)
        
        # Calculate and update total duration
        total_duration = sum(s.end - s.start for s in sentences)
        update_project(db, project_id, {"total_duration": total_duration})
        
        # Return response
        return ProjectResponse(
            project_id=project_id,
            sentences=sentences
        )
    except Exception as e:
        logger.error(f"Error in create_project: {str(e)}")
        # Clean up any created files
        if os.path.exists(audio_path):
            os.remove(audio_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )

@router.post("/{project_id}/footage", response_model=MusicResponse)
async def submit_footage_choices(
    project_id: str,
    footage_choices: FootageChoices,
    db: Session = Depends(get_db)
):
    """
    Step B: Submit footage choices for sentences and get music recommendations.
    """
    try:
        # Validate project exists
        validate_project_exists(db, project_id)
        
        # Create and save footage choices
        create_footage_choices(db, project_id, footage_choices.footage_choices)
        
        # For each footage choice, update the sentence with the selected footage
        for choice in footage_choices.footage_choices:
            # Get the footage URL from the footage choice
            footage_url = choice.footage_url
            
            # Create selected footage object
            from app.schemas import SelectedFootage
            selected_footage = SelectedFootage(
                id=f"footage-{choice.sentence_id}-selected",
                title=f"User-selected footage for sentence {choice.sentence_id}",
                description="User-selected footage from Pexels",
                thumbnail="/placeholder.svg",  # Would need proper Pexels integration for thumbnails
                duration=10.0,  # Default duration, would be updated with actual duration
                tags=["user-selected", "pexels"],
                category="user-selected",
                mood="neutral",
                relevance_score=100,  # User selected is always most relevant
                url=footage_url
            )
            
            # Update the sentence with the selected footage
            from app.db_service import update_sentence_footage
            update_sentence_footage(db, choice.sentence_id, selected_footage)
        
        # Find background music recommendations
        sentences = get_sentences(db, project_id)
        sentence_texts = [s.text for s in sentences]
        music_tracks = await find_background_music(sentence_texts)
        
        # Save music recommendations to database
        from app.schemas import MusicRecommendationCreate
        music_recs = []
        for track in music_tracks:
            music_rec = MusicRecommendationCreate(
                title=track.name,
                artist="AI Generated",
                genre="Ambient",
                mood="Neutral",
                energy_level=5,
                url=track.url,
                duration=60.0  # Default duration, would be updated with actual duration
            )
            music_recs.append(music_rec)
        
        create_music_recommendations(db, project_id, music_recs)
        
        return MusicResponse(
            project_id=project_id,
            recommended_music=music_tracks
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in submit_footage_choices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit footage choices: {str(e)}"
        )

@router.post("/{project_id}/render", response_model=RenderResponse, status_code=status.HTTP_202_ACCEPTED)
async def render_project(
    background_tasks: BackgroundTasks,
    project_id: str,
    render_request: RenderRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Step C: Render the final video with selected footage and music.
    """
    try:
        # Validate project exists
        validate_project_exists(db, project_id)
        
        # Create a render task
        render_task_id = generate_id("task")
        from app.schemas import RenderTaskCreate
        
        render_task_data = RenderTaskCreate(
            id=render_task_id,
            project_id=project_id,
            status="pending"
        )
        create_render_task(db, render_task_data)
        
        # Get the project with all data
        project_data = get_project_with_all_data(db, project_id)
        
        # Check if all sentences have selected footage
        sentences = get_sentences(db, project_id)
        if not all(s.selected_footage for s in sentences):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not all sentences have selected footage. Please select footage for all sentences."
            )
        
        # Get music recommendations
        music_recs = get_music_recommendations(db, project_id)
        
        # If no music recommendations, find and use available music files
        music_url = None
        if not music_recs:
            # Find music files from local audio directory
            music_files = list(AUDIO_DIR.glob("*.mp3"))
            if music_files:
                music_url = str(music_files[0])  # Use the first available music file
                logger.info(f"Using music file: {music_url}")
            else:
                # Render without music if no music files available
                logger.warning("No music files available in audio directory, rendering without music")
                music_url = None
        else:
            # Use the first music recommendation and convert API URLs to local paths
            music_url = music_recs[0].url
            # If it's an API URL, convert it to local path
            if music_url.startswith('/api/audio/'):
                # Extract filename and construct local path
                filename = os.path.basename(music_url)
                music_url = str(AUDIO_DIR / filename)
            logger.info(f"Using music recommendation: {music_url}")
        
        # Create render task for background processing
        async def render_task_async():
            try:
                # Update task status to processing
                update_render_task_status(db, render_task_id, "processing", progress=0)
                
                # For each sentence, extract the footage URL
                render_segments = []
                for sentence in sentences:
                    # Check if sentence has selected footage
                    if not sentence.selected_footage:
                        logger.warning(f"Sentence {sentence.id} has no selected footage. Skipping.")
                        continue
                    
                    # Get the footage URL from the selected footage
                    footage_url = sentence.selected_footage.get("url")
                    if not footage_url:
                        logger.warning(f"Sentence {sentence.id} selected footage has no URL. Skipping.")
                        continue
                    
                    # Add segment to render list
                    render_segments.append({
                        "text": sentence.text,
                        "start_time": sentence.start_time,
                        "end_time": sentence.end_time,
                        "footage_url": footage_url
                    })
                
                # Sort segments by start time
                render_segments.sort(key=lambda x: x["start_time"])
                
                # Run the video rendering process using the working render function
                output_path = await render_final_video(
                    project_id=project_id,
                    render_segments=render_segments,
                    music_url=music_url,
                    add_subtitles=render_request.add_subtitles,
                    include_audio=render_request.include_audio,
                )
                
                # Check if rendering was successful
                if not output_path or not os.path.exists(output_path):
                    raise Exception(f"Video rendering failed - no output file created: {output_path}")
                
                # Update task status to complete
                video_url = f"/api/videos/{os.path.basename(output_path)}"
                update_render_task_status(db, render_task_id, "complete", video_url=video_url, progress=100)
                
                # Also update the project's video_url field
                update_project(db, project_id, {"video_url": video_url})
            except Exception as e:
                logger.error(f"Error in render task: {str(e)}")
                update_render_task_status(db, render_task_id, "failed", error_message=str(e))
        
        # Run the render task in the background
        background_tasks.add_task(render_task_async)
        
        # Return the render task ID and status URL
        base_url = str(request.base_url).rstrip("/")
        status_url = f"{base_url}/api/v1/projects/render/status/{render_task_id}"
        
        return RenderResponse(
            render_task_id=render_task_id,
            status_url=status_url
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in render_project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to render project: {str(e)}"
        )

@router.get("/render/status/{render_task_id}", response_model=RenderStatusResponse)
async def get_render_status(
    render_task_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the status of a render task.
    """
    try:
        # Get the render task from the database
        render_task = get_render_task(db, render_task_id)
        if not render_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Render task with ID {render_task_id} not found"
            )
        
        # Return the status
        return RenderStatusResponse(
            status=render_task.status,
            video_url=render_task.output_file_path,
            error=render_task.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_render_status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get render status: {str(e)}"
        )

# Add new Update endpoint
@router.put("/{project_id}", response_model=Dict[str, Any])
async def update_project_by_id(
    project_id: str,
    project_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Update a project by ID
    """
    try:
        # Validate project exists
        validate_project_exists(db, project_id)
        
        # Update project
        updated_project = update_project(db, project_id, project_data)
        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        return get_project_details(project_id, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )

# Add new Patch endpoint for partial updates
@router.patch("/{project_id}", response_model=Dict[str, Any])
async def patch_project(
    project_id: str,
    project_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Partially update a project by ID
    """
    try:
        # Validate project exists
        validate_project_exists(db, project_id)
        
        # Update project
        updated_project = update_project(db, project_id, project_data)
        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        return get_project_details(project_id, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error patching project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to patch project: {str(e)}"
        )

# Add new Delete endpoint
@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_by_id(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a project by ID
    """
    try:
        # Validate project exists
        validate_project_exists(db, project_id)
        
        # Delete project
        success = delete_project(db, project_id)
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