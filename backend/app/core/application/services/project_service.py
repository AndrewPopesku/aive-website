from __future__ import annotations

from typing import List, Optional, Dict, Any, Union, TypedDict
import logging
from pathlib import Path

from ...domain.entities.project import Project
from ...domain.entities.sentence import Sentence, SelectedFootage
from ...domain.entities.music import MusicRecommendation
from ...domain.repositories.project_repository import ProjectRepository
from ...domain.repositories.sentence_repository import SentenceRepository
from ...domain.repositories.music_repository import MusicRepository
from ...domain.services.transcription_service import TranscriptionService
from ...domain.services.footage_service import FootageService
from ...domain.services.music_service import MusicService
from ...domain.exceptions import (
    EntityNotFoundError, 
    ValidationError, 
    BusinessRuleViolationError
)

logger = logging.getLogger(__name__)


# TypedDict classes for better type safety
class ProjectCreationResult(TypedDict):
    """Result of project creation operation."""
    project_id: str
    project: Project
    sentences: List[Sentence]


class ProjectSummary(TypedDict):
    """Summary information about a project."""
    id: str
    project_id: str
    title: str
    description: Optional[str]
    audio_file_path: Optional[str]
    created_at: str
    updated_at: str
    total_duration: Optional[float]
    overall_mood: Optional[str]
    videoUrl: Optional[str]
    sentences: int
    total_sentences: int


class ProjectDetails(TypedDict):
    """Detailed project information."""
    id: str
    project_id: str
    title: str
    description: Optional[str]
    audio_file_path: Optional[str]
    created_at: str
    updated_at: str
    total_duration: Optional[float]
    overall_mood: Optional[str]
    videoUrl: Optional[str]
    sentences: List[Dict[str, Any]]
    total_sentences: int


class FootageChoice(TypedDict):
    """Footage selection choice."""
    sentence_id: str
    footage_url: str


class ProjectService:
    """Application service for project-related use cases.
    
    This service orchestrates project creation, management, and related operations
    by coordinating between domain entities, repositories, and domain services.
    It implements use cases and business workflows while maintaining clean
    separation between the application and domain layers.
    """
    
    def __init__(
        self,
        project_repository: ProjectRepository,
        sentence_repository: SentenceRepository,
        music_repository: MusicRepository,
        transcription_service: TranscriptionService,
        footage_service: FootageService,
        music_service: MusicService
    ) -> None:
        """Initialize the project service with required dependencies.
        
        Args:
            project_repository: Repository for project persistence
            sentence_repository: Repository for sentence persistence
            music_repository: Repository for music recommendation persistence
            transcription_service: Service for audio transcription
            footage_service: Service for footage search and selection
            music_service: Service for background music recommendations
            
        Raises:
            TypeError: If any dependency is None or invalid type
        """
        if not all([
            project_repository, sentence_repository, music_repository,
            transcription_service, footage_service, music_service
        ]):
            raise TypeError("All service dependencies must be provided")
            
        self._project_repository = project_repository
        self._sentence_repository = sentence_repository
        self._music_repository = music_repository
        self._transcription_service = transcription_service
        self._footage_service = footage_service
        self._music_service = music_service
    
    async def create_project(
        self, 
        title: str, 
        audio_file_path: str, 
        description: Optional[str] = None
    ) -> ProjectCreationResult:
        """Create a new project with audio transcription and footage recommendations.
        
        Args:
            title: Project title (must be non-empty)
            audio_file_path: Path to the audio file for transcription
            description: Optional project description
            
        Returns:
            ProjectCreationResult with project details and sentences
            
        Raises:
            ValidationError: If input parameters are invalid
            FileNotFoundError: If audio file doesn't exist
            TranscriptionError: If audio transcription fails
            BusinessRuleViolationError: If business rules are violated
        """
        # Validate inputs
        if not title.strip():
            raise ValidationError(
                "title", title, "Title cannot be empty", "Project"
            )
        
        if len(title.strip()) > 200:
            raise ValidationError(
                "title", title, "Title cannot exceed 200 characters", "Project"
            )
        
        audio_file = Path(audio_file_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        logger.info(f"Creating project '{title}' with audio file: {audio_file_path}")
        # Create project entity
        project = Project(
            title=title,
            description=description,
            audio_file_path=audio_file_path
        )
        
        # Save project
        created_project = await self._project_repository.create(project)
        
        # Transcribe audio
        sentences = await self._transcription_service.transcribe_audio(audio_file_path)
        
        # Set project ID for sentences
        for sentence in sentences:
            sentence.project_id = created_project.id
        
        # Find footage for each sentence
        for sentence in sentences:
            footage_url = await self._footage_service.find_footage_for_sentence(
                sentence.text, sentence.translated_text
            )
            
            if footage_url:
                # Create selected footage
                selected_footage = SelectedFootage(
                    id=f"footage-{sentence.id}-recommended",
                    title=f"{sentence.text[:35]}{'...' if len(sentence.text) > 35 else ''}",
                    description="AI-recommended footage from Pexels based on content analysis",
                    thumbnail="/placeholder.svg",
                    duration=sentence.duration,
                    tags=["ai-recommended", "pexels", "relevant"],
                    category="recommended",
                    mood="neutral",
                    relevance_score=95,
                    url=footage_url
                )
                sentence.set_selected_footage(selected_footage)
        
        # Save sentences
        created_sentences = await self._sentence_repository.create_many(sentences)
        
        # Update project duration
        total_duration = sum(s.duration for s in created_sentences)
        created_project.update_duration(total_duration)
        await self._project_repository.update(created_project)
        
        return {
            "project_id": created_project.id,
            "project": created_project,
            "sentences": created_sentences
        }
    
    async def get_all_projects(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all projects with their details."""
        projects = await self._project_repository.get_all(skip, limit)
        
        result = []
        for project in projects:
            sentences = await self._sentence_repository.get_by_project_id(project.id)
            
            project_dict = {
                "id": project.id,
                "project_id": project.id,
                "title": project.title or f"Project {project.id}",
                "description": project.description,
                "audio_file_path": project.audio_file_path,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
                "total_duration": project.total_duration,
                "overall_mood": project.overall_mood,
                "videoUrl": project.video_url,
                "sentences": len(sentences),
                "total_sentences": len(sentences)
            }
            result.append(project_dict)
        
        return result
    
    async def get_project_details(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed project information including sentences."""
        project = await self._project_repository.get_by_id(project_id)
        if not project:
            return None
        
        sentences = await self._sentence_repository.get_by_project_id(project_id)
        
        return {
            "id": project.id,
            "project_id": project.id,
            "title": project.title or f"Project {project.id}",
            "description": project.description,
            "audio_file_path": project.audio_file_path,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "total_duration": project.total_duration,
            "overall_mood": project.overall_mood,
            "videoUrl": project.video_url,
            "sentences": [self._sentence_to_dict(s) for s in sentences],
            "total_sentences": len(sentences)
        }
    
    async def submit_footage_choices(self, project_id: str, footage_choices: List[Dict[str, Any]]) -> List[MusicRecommendation]:
        """Submit footage choices and get music recommendations."""
        # Verify project exists
        project = await self._project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Update sentences with selected footage
        for choice in footage_choices:
            sentence_id = choice.get("sentence_id")
            footage_url = choice.get("footage_url")
            
            sentence = await self._sentence_repository.get_by_id(sentence_id)
            if sentence and footage_url:
                selected_footage = SelectedFootage(
                    id=f"footage-{sentence_id}-selected",
                    title=f"User-selected footage for sentence {sentence_id}",
                    description="User-selected footage from Pexels",
                    thumbnail="/placeholder.svg",
                    duration=sentence.duration,
                    tags=["user-selected", "pexels"],
                    category="user-selected",
                    mood="neutral",
                    relevance_score=100,
                    url=str(footage_url)
                )
                sentence.set_selected_footage(selected_footage)
                await self._sentence_repository.update(sentence)
        
        # Get music recommendations
        sentences = await self._sentence_repository.get_by_project_id(project_id)
        sentence_texts = [s.text for s in sentences]
        music_tracks = await self._music_service.find_background_music(sentence_texts)
        
        # Set project ID for music recommendations
        for track in music_tracks:
            track.project_id = project_id
        
        # Save music recommendations
        saved_music = await self._music_repository.create_many(music_tracks)
        
        return saved_music
    
    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> Optional[Project]:
        """Update a project with new data."""
        project = await self._project_repository.get_by_id(project_id)
        if not project:
            return None
        
        # Update fields
        if "title" in updates:
            project.title = updates["title"]
        if "description" in updates:
            project.description = updates["description"]
        if "video_url" in updates:
            project.update_video_url(updates["video_url"])
        if "overall_mood" in updates:
            project.update_mood(updates["overall_mood"])
        
        return await self._project_repository.update(project)
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project and all related data."""
        # Delete related data first
        await self._sentence_repository.delete_by_project_id(project_id)
        await self._music_repository.delete_by_project_id(project_id)
        
        # Delete project
        return await self._project_repository.delete(project_id)
    
    def _sentence_to_dict(self, sentence: Sentence) -> Dict[str, Any]:
        """Convert sentence entity to dictionary."""
        return {
            "id": sentence.id,
            "project_id": sentence.project_id,
            "text": sentence.text,
            "translated_text": sentence.translated_text,
            "start_time": sentence.start_time,
            "end_time": sentence.end_time,
            "selected_footage": sentence.selected_footage
        }