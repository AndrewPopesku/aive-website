from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from base.controller import BaseController
from projects.models import FootageChoice, MusicRecommendation, Project, Sentence
from projects.repository import (
    FootageChoiceRepository,
    MusicRecommendationRepository,
    ProjectRepository,
    SentenceRepository,
)
from projects.schemas import (
    FootageChoiceCreate,
    MusicRecommendationCreate,
    ProjectCreate,
    SelectedFootage,
    SentenceCreate,
)


class ProjectController(BaseController[ProjectRepository]):
    """Controller for project business logic."""

    def __init__(self) -> None:
        super().__init__(ProjectRepository())
        self.sentence_repo = SentenceRepository()
        self.footage_repo = FootageChoiceRepository()
        self.music_repo = MusicRecommendationRepository()

    async def create_project_with_audio(
        self, session: AsyncSession, project_data: ProjectCreate
    ) -> Project:
        """Create a new project with audio file."""
        # Validate audio file path exists
        if not project_data.audio_file_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file path is required",
            )

        # Check if project with same title already exists and make it unique
        original_title = project_data.title
        counter = 1
        while True:
            existing_project = await self.repository.get_by_title(
                session, project_data.title
            )
            if not existing_project:
                break
            # Append counter to make title unique
            counter += 1
            project_data.title = f"{original_title} ({counter})"

        # Create the project
        project_dict = project_data.model_dump()
        return await self.repository.create(session, project_dict)

    async def get_project_with_details(
        self, session: AsyncSession, project_id: str
    ) -> dict[str, Any]:
        """Get project with all related data (sentences, footage choices, music)."""
        # Get the project
        project: Project = await self.get_entity(session, project_id)

        # Get all related data
        sentences = await self.sentence_repo.get_by_project_id(session, project_id)
        footage_choices = await self.footage_repo.get_by_project_id(session, project_id)
        music_recommendations = await self.music_repo.get_by_project_id(
            session, project_id
        )

        # Convert to response format
        project_dict = {
            "id": project.id,
            "project_id": project.id,
            "title": project.title,
            "description": project.description,
            "audio_file_path": project.audio_file_path,
            "total_duration": project.total_duration,
            "overall_mood": project.overall_mood,
            "video_url": project.video_url,
            "videoUrl": project.video_url,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "sentences": [self._sentence_to_dict(s) for s in sentences],
            "total_sentences": len(sentences),
            "footage_choices": [
                self._footage_choice_to_dict(fc) for fc in footage_choices
            ],
            "music_recommendations": [
                self._music_recommendation_to_dict(mr) for mr in music_recommendations
            ],
        }

        # Calculate total duration from sentences if not set
        if not project_dict["total_duration"] and sentences:
            project_dict["total_duration"] = sum(
                s.end_time - s.start_time for s in sentences
            )

        return project_dict

    async def add_sentences_to_project(
        self,
        session: AsyncSession,
        project_id: str,
        sentences_data: list[SentenceCreate],
    ) -> list[dict[str, Any]]:
        """Add sentences to a project."""
        # Validate project exists
        await self.validate_entity_exists(session, project_id)
        # Convert to dict format
        sentences_dict = [s.model_dump() for s in sentences_data]
        # Create sentences
        sentences = await self.sentence_repo.create_multiple(
            session, project_id, sentences_dict
        )
        return [self._sentence_to_dict(s) for s in sentences]

    async def add_footage_choices(
        self,
        session: AsyncSession,
        project_id: str,
        footage_choices_data: list[FootageChoiceCreate],
    ) -> list[dict[str, Any]]:
        """Add footage choices to a project."""
        # Validate project exists
        await self.validate_entity_exists(session, project_id)
        # Convert to dict format
        choices_dict = [fc.model_dump() for fc in footage_choices_data]
        # Create footage choices
        choices = await self.footage_repo.create_multiple(
            session, project_id, choices_dict
        )
        return [self._footage_choice_to_dict(fc) for fc in choices]

    async def add_music_recommendations(
        self,
        session: AsyncSession,
        project_id: str,
        music_data: list[MusicRecommendationCreate],
    ) -> list[dict[str, Any]]:
        """Add music recommendations to a project."""
        # Validate project exists
        await self.validate_entity_exists(session, project_id)
        # Convert to dict format
        music_dict = [m.model_dump() for m in music_data]
        # Create music recommendations
        recommendations = await self.music_repo.create_multiple(
            session, project_id, music_dict
        )
        return [self._music_recommendation_to_dict(mr) for mr in recommendations]

    async def update_sentence_footage(
        self, session: AsyncSession, sentence_id: str, selected_footage: SelectedFootage
    ) -> dict[str, Any] | None:
        """Update selected footage for a sentence."""
        sentence = await self.sentence_repo.update_selected_footage(
            session, sentence_id, selected_footage
        )
        if not sentence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sentence with ID {sentence_id} not found",
            )
        return self._sentence_to_dict(sentence)

    def _sentence_to_dict(self, sentence: Sentence) -> dict[str, Any]:
        """Convert sentence model to dict."""
        return {
            "id": sentence.id,
            "project_id": sentence.project_id,
            "text": sentence.text,
            "translated_text": sentence.translated_text,
            "start_time": sentence.start_time,
            "end_time": sentence.end_time,
            "selected_footage": sentence.selected_footage,
        }

    def _footage_choice_to_dict(self, footage_choice: FootageChoice) -> dict[str, Any]:
        """Convert footage choice model to dict."""
        return {
            "id": footage_choice.id,
            "project_id": footage_choice.project_id,
            "sentence_id": footage_choice.sentence_id,
            "footage_options": footage_choice.footage_options,
        }

    def _music_recommendation_to_dict(
        self, music_rec: MusicRecommendation
    ) -> dict[str, Any]:
        """Convert music recommendation model to dict."""
        return {
            "id": music_rec.id,
            "project_id": music_rec.project_id,
            "title": music_rec.title,
            "artist": music_rec.artist,
            "genre": music_rec.genre,
            "mood": music_rec.mood,
            "energy_level": music_rec.energy_level,
            "url": music_rec.url,
            "duration": music_rec.duration,
        }
