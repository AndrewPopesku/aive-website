import os
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from projects.controller import ProjectController
from projects.schemas import (
    FootageChoices,
    MusicResponse,
    ProjectCreate,
)

router = APIRouter()
controller = ProjectController()


@router.get("/", response_model=list[dict[str, Any]])
async def get_all_projects(
    skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session)
):
    """Get a list of all projects."""
    projects = await controller.get_entities(session, skip, limit)

    # Convert to response format with additional details
    result = []
    for project in projects:
        project_details = await controller.get_project_with_details(session, project.id)
        result.append(project_details)

    return result


@router.get("/{project_id}", response_model=dict[str, Any])
async def get_project_details(
    project_id: str, session: AsyncSession = Depends(get_session)
):
    """Get details for a specific project."""
    return await controller.get_project_with_details(session, project_id)


@router.post("/", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_project(
    audio_file: UploadFile = File(...), session: AsyncSession = Depends(get_session)
):
    """Create a new project with audio file upload, transcription, and footage recommendations."""
    import os
    import shutil

    from base.config import get_settings
    from projects.schemas import SelectedFootage, SentenceCreate, generate_id
    from video_processing.services import find_footage_for_sentence, transcribe_audio

    settings = get_settings()

    # Validate audio file
    if audio_file.content_type not in settings.allowed_audio_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Supported types: {settings.allowed_audio_types}",
        )

    # Generate project ID and save audio file
    project_id = generate_id("proj")
    audio_path = settings.temp_dir / f"{project_id}_{audio_file.filename}"

    try:
        # Save the audio file
        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)

        # Transcribe audio to get sentences with timestamps
        sentences_data = await transcribe_audio(str(audio_path))

        if not sentences_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to transcribe audio",
            )

        # For each sentence, find recommended footage and set as selected by default
        sentences_create = []
        for sentence_data in sentences_data:
            # Find footage for this sentence
            footage_url = await find_footage_for_sentence(
                sentence_data["text"], sentence_data.get("translated_text")
            )

            # Create default selected footage from recommendation
            selected_footage = None
            if footage_url:
                selected_footage = SelectedFootage(
                    id=f"footage-{len(sentences_create)}-recommended",
                    title=f"{sentence_data['text'][:35]}{'...' if len(sentence_data['text']) > 35 else ''}",
                    description="AI-recommended footage from Pexels based on content analysis",
                    thumbnail="/placeholder.svg",
                    duration=sentence_data["end"] - sentence_data["start"],
                    tags=["ai-recommended", "pexels", "relevant"],
                    category="recommended",
                    mood="neutral",
                    relevance_score=95,
                    url=str(
                        footage_url
                    ),  # Convert to string to avoid HttpUrl serialization issues
                )

            # Create sentence object
            sentence_create = SentenceCreate(
                text=sentence_data["text"],
                translated_text=sentence_data.get("translated_text"),
                start_time=sentence_data["start"],
                end_time=sentence_data["end"],
                selected_footage=selected_footage,
            )
            sentences_create.append(sentence_create)

        # Create project data
        project_data = ProjectCreate(
            id=project_id,
            title=f"Project {project_id}",
            audio_file_path=str(audio_path),
        )

        # Create the project
        project = await controller.create_project_with_audio(session, project_data)

        # Add sentences to the project
        await controller.add_sentences_to_project(session, project_id, sentences_create)

        # Add background music recommendations
        from projects.schemas import MusicRecommendationCreate
        from video_processing.services import find_background_music

        music_tracks = await find_background_music([])

        if music_tracks:
            music_recs_create = []
            for track in music_tracks:
                music_rec = MusicRecommendationCreate(
                    title=track["name"],
                    artist="Local Audio",
                    genre="Background",
                    mood="Neutral",
                    energy_level=5,
                    url=track["url"],
                    duration=60.0,  # Default duration
                )
                music_recs_create.append(music_rec)

            await controller.add_music_recommendations(
                session, project_id, music_recs_create
            )

        # Return project details with sentences and music
        return await controller.get_project_with_details(session, project.id)

    except Exception as e:
        # Clean up any created files
        if os.path.exists(audio_path):
            os.remove(audio_path)

        if isinstance(e, HTTPException):
            raise

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}",
        ) from e


@router.put("/{project_id}", response_model=dict[str, Any])
async def update_project(
    project_id: str,
    project_data: dict[str, Any],
    session: AsyncSession = Depends(get_session),
):
    """Update a project by ID."""
    await controller.update_entity(session, project_id, project_data)
    return await controller.get_project_with_details(session, project_id)


@router.patch("/{project_id}", response_model=dict[str, Any])
async def patch_project(
    project_id: str,
    project_data: dict[str, Any],
    session: AsyncSession = Depends(get_session),
):
    """Partially update a project by ID."""
    await controller.update_entity(session, project_id, project_data)
    return await controller.get_project_with_details(session, project_id)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, session: AsyncSession = Depends(get_session)):
    """Delete a project by ID."""
    await controller.delete_entity(session, project_id)
    return None


@router.post("/{project_id}/footage", response_model=MusicResponse)
async def submit_footage_choices(
    project_id: str,
    footage_choices: FootageChoices,
    session: AsyncSession = Depends(get_session),
):
    """Submit footage choices for sentences and get music recommendations."""
    from projects.schemas import FootageChoiceCreate, MusicRecommendationCreate
    from video_processing.services import find_background_music

    # Validate project exists
    await controller.validate_entity_exists(session, project_id)

    # Process footage choices and update sentences
    for choice in footage_choices.footage_choices:
        # Create selected footage object
        selected_footage = {
            "id": f"footage-{choice.sentence_id}-selected",
            "title": f"User-selected footage for sentence {choice.sentence_id}",
            "description": "User-selected footage from Pexels",
            "thumbnail": "/placeholder.svg",
            "duration": 10.0,  # Default duration
            "tags": ["user-selected", "pexels"],
            "category": "user-selected",
            "mood": "neutral",
            "relevance_score": 100,  # User selected is always most relevant
            "url": choice.footage_url,
        }

        # Update the sentence with the selected footage
        from projects.schemas import SelectedFootage

        selected_footage_obj = SelectedFootage(**selected_footage)
        await controller.update_sentence_footage(
            session, choice.sentence_id, selected_footage_obj
        )

    # Create and save footage choices to database
    footage_choices_create = []
    for choice in footage_choices.footage_choices:
        footage_choice_create = FootageChoiceCreate(
            sentence_id=choice.sentence_id,
            footage_options=[{"url": choice.footage_url, "selected": True}],
        )
        footage_choices_create.append(footage_choice_create)

    await controller.add_footage_choices(session, project_id, footage_choices_create)

    # Get all sentences to find background music
    project_details = await controller.get_project_with_details(session, project_id)
    sentence_texts = [s["text"] for s in project_details["sentences"]]

    # Find background music recommendations
    music_tracks = await find_background_music(sentence_texts)

    # Save music recommendations to database
    if music_tracks:
        music_recs_create = []
        for track in music_tracks:
            music_rec = MusicRecommendationCreate(
                title=track["name"],
                artist="AI Generated",
                genre="Ambient",
                mood="Neutral",
                energy_level=5,
                url=track["url"],
                duration=60.0,  # Default duration
            )
            music_recs_create.append(music_rec)

        await controller.add_music_recommendations(
            session, project_id, music_recs_create
        )

    # Convert music tracks to response format
    from projects.schemas import MusicRecommendation

    music_recommendations = []
    for track in music_tracks:
        music_rec = MusicRecommendation(
            id=track["id"], name=track["name"], url=track["url"]
        )
        music_recommendations.append(music_rec)

    return MusicResponse(project_id=project_id, recommended_music=music_recommendations)


@router.post("/{project_id}/render", status_code=status.HTTP_202_ACCEPTED)
async def render_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Start rendering a video for a project."""
    from render.controller import RenderController
    from render.schemas import RenderRequest

    # Create a minimal render request (can be enhanced later)
    render_request = RenderRequest()
    render_controller = RenderController()

    # Validate project exists and get project data
    project_details = await controller.get_project_with_details(session, project_id)

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
    render_task = await render_controller.create_render_task(
        session, project_id, render_request
    )

    # Define the background rendering function
    async def render_video_task():
        # Create a new session for the background task
        from database.session import async_session_factory

        async with async_session_factory() as bg_session:
            try:
                # Update status to processing
                await render_controller.update_render_status(
                    bg_session, render_task.id, "processing", progress=10
                )

                # Get audio file path from project
                audio_file_path = project_details["audio_file_path"]
                if not audio_file_path or not os.path.exists(audio_file_path):
                    await render_controller.update_render_status(
                        bg_session,
                        render_task.id,
                        "failed",
                        error_message="Audio file not found",
                    )
                    return

                # Update progress
                await render_controller.update_render_status(
                    bg_session, render_task.id, "processing", progress=25
                )

                # Update progress
                await render_controller.update_render_status(
                    bg_session, render_task.id, "processing", progress=40
                )

                # Create a mock video URL (replace with actual rendering later)
                output_filename = f"{project_id}_final_video.mp4"
                relative_path = f"/api/videos/{output_filename}"

                # Update status to complete
                await render_controller.update_render_status(
                    bg_session,
                    render_task.id,
                    "complete",
                    progress=100,
                    video_url=relative_path,
                )

                # Update project with video URL
                await controller.update_entity(
                    bg_session, project_id, {"video_url": relative_path}
                )

            except Exception as e:
                import logging

                logging.getLogger(__name__).error(
                    f"Error in render task {render_task.id}: {str(e)}"
                )
                await render_controller.update_render_status(
                    bg_session, render_task.id, "failed", error_message=str(e)
                )

    # Add the rendering task to background tasks
    background_tasks.add_task(render_video_task)

    # Return response
    return {
        "render_task_id": render_task.id,
        "status_url": f"/api/v1/render/status/{render_task.id}",
        "message": "Render task started successfully",
    }


@router.get("/render/status/{task_id}")
async def get_project_render_status(
    task_id: str, session: AsyncSession = Depends(get_session)
):
    """Get the status of a render task (project-scoped route)."""
    from render.controller import RenderController

    render_controller = RenderController()
    status_info = await render_controller.get_render_status(session, task_id)

    return {
        "status": status_info["status"],
        "video_url": status_info["video_url"],
        "error": status_info["error"],
        "progress": status_info["progress"],
    }
