from sqlalchemy.orm import Session
from functools import lru_cache

from ..core.application.services.project_service import ProjectService
from ..core.application.services.render_service import RenderService

from ..adapters.outbound.persistence.project_repository_impl import DatabaseProjectRepository
from ..adapters.outbound.persistence.sentence_repository_impl import DatabaseSentenceRepository
from ..adapters.outbound.persistence.music_repository_impl import DatabaseMusicRepository
from ..adapters.outbound.persistence.render_task_repository_impl import DatabaseRenderTaskRepository

from ..adapters.outbound.external_apis.transcription_service_impl import GroqTranscriptionService
from ..adapters.outbound.external_apis.footage_service_impl import PexelsFootageService
from ..adapters.outbound.file_system.music_service_impl import LocalMusicService
from ..adapters.outbound.file_system.video_rendering_service_impl import MoviePyVideoRenderingService

from ..adapters.inbound.rest.project_controller import ProjectController


class DependencyContainer:
    """Dependency injection container for the application."""
    
    def __init__(self):
        self._instances = {}
    
    def get_project_service(self, db: Session) -> ProjectService:
        """Get or create ProjectService instance."""
        return ProjectService(
            project_repository=self.get_project_repository(db),
            sentence_repository=self.get_sentence_repository(db),
            music_repository=self.get_music_repository(db),
            transcription_service=self.get_transcription_service(),
            footage_service=self.get_footage_service(),
            music_service=self.get_music_service()
        )
    
    def get_render_service(self, db: Session) -> RenderService:
        """Get or create RenderService instance."""
        return RenderService(
            project_repository=self.get_project_repository(db),
            sentence_repository=self.get_sentence_repository(db),
            music_repository=self.get_music_repository(db),
            render_task_repository=self.get_render_task_repository(db),
            video_rendering_service=self.get_video_rendering_service()
        )
    
    def get_project_repository(self, db: Session) -> DatabaseProjectRepository:
        """Get or create ProjectRepository instance."""
        return DatabaseProjectRepository(db)
    
    def get_sentence_repository(self, db: Session) -> DatabaseSentenceRepository:
        """Get or create SentenceRepository instance."""
        return DatabaseSentenceRepository(db)
    
    def get_music_repository(self, db: Session) -> DatabaseMusicRepository:
        """Get or create MusicRepository instance."""
        return DatabaseMusicRepository(db)
    
    def get_render_task_repository(self, db: Session) -> DatabaseRenderTaskRepository:
        """Get or create RenderTaskRepository instance."""
        return DatabaseRenderTaskRepository(db)
    
    @lru_cache(maxsize=1)
    def get_transcription_service(self) -> GroqTranscriptionService:
        """Get or create TranscriptionService instance."""
        return GroqTranscriptionService()
    
    @lru_cache(maxsize=1)
    def get_footage_service(self) -> PexelsFootageService:
        """Get or create FootageService instance."""
        return PexelsFootageService()
    
    @lru_cache(maxsize=1)
    def get_music_service(self) -> LocalMusicService:
        """Get or create MusicService instance."""
        return LocalMusicService()
    
    @lru_cache(maxsize=1)
    def get_video_rendering_service(self) -> MoviePyVideoRenderingService:
        """Get or create VideoRenderingService instance."""
        return MoviePyVideoRenderingService()
    
    def get_project_controller(self, db: Session) -> ProjectController:
        """Get or create ProjectController instance."""
        return ProjectController(
            project_service=self.get_project_service(db),
            render_service=self.get_render_service(db)
        )


# Global container instance
container = DependencyContainer()