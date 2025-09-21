from typing import List, Optional, Dict, Any, Callable
from ...domain.entities.project import Project
from ...domain.entities.sentence import Sentence
from ...domain.entities.render_task import RenderTask, RenderStatus
from ...domain.entities.music import MusicRecommendation
from ...domain.repositories.project_repository import ProjectRepository
from ...domain.repositories.sentence_repository import SentenceRepository
from ...domain.repositories.music_repository import MusicRepository
from ...domain.repositories.render_task_repository import RenderTaskRepository
from ...domain.services.video_rendering_service import VideoRenderingService


class RenderService:
    """Application service for video rendering use cases."""
    
    def __init__(
        self,
        project_repository: ProjectRepository,
        sentence_repository: SentenceRepository,
        music_repository: MusicRepository,
        render_task_repository: RenderTaskRepository,
        video_rendering_service: VideoRenderingService
    ):
        self._project_repository = project_repository
        self._sentence_repository = sentence_repository
        self._music_repository = music_repository
        self._render_task_repository = render_task_repository
        self._video_rendering_service = video_rendering_service
    
    async def start_render(
        self, 
        project_id: str, 
        add_subtitles: bool = True, 
        include_audio: bool = True
    ) -> RenderTask:
        """Start the rendering process for a project."""
        # Verify project exists
        project = await self._project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Get sentences and verify they have footage
        sentences = await self._sentence_repository.get_by_project_id(project_id)
        if not sentences:
            raise ValueError(f"No sentences found for project {project_id}")
        
        # Check if all sentences have selected footage
        sentences_without_footage = [s for s in sentences if not s.has_footage()]
        if sentences_without_footage:
            raise ValueError("Not all sentences have selected footage. Please select footage for all sentences.")
        
        # Get music recommendations
        music_recs = await self._music_repository.get_by_project_id(project_id)
        music_url = music_recs[0].url if music_recs else None
        
        # Create render task
        render_task = RenderTask(project_id=project_id)
        created_task = await self._render_task_repository.create(render_task)
        
        return created_task
    
    async def process_render(
        self,
        task_id: str,
        add_subtitles: bool = True,
        include_audio: bool = True
    ) -> str:
        """Process the actual rendering (to be called in background)."""
        # Get render task
        render_task = await self._render_task_repository.get_by_id(task_id)
        if not render_task:
            raise ValueError(f"Render task {task_id} not found")
        
        try:
            # Mark task as processing
            render_task.start_processing()
            await self._render_task_repository.update(render_task)
            
            # Get project and related data
            project = await self._project_repository.get_by_id(render_task.project_id)
            sentences = await self._sentence_repository.get_by_project_id(render_task.project_id)
            music_recs = await self._music_repository.get_by_project_id(render_task.project_id)
            
            music_url = music_recs[0].url if music_recs else None
            voice_over_path = project.audio_file_path
            
            # Progress callback
            async def progress_callback(progress: int):
                render_task.update_progress(progress)
                await self._render_task_repository.update(render_task)
            
            # Render video
            output_path = await self._video_rendering_service.render_video(
                project_id=render_task.project_id,
                sentences=sentences,
                music_url=music_url,
                voice_over_path=voice_over_path,
                add_subtitles=add_subtitles,
                include_audio=include_audio,
                progress_callback=progress_callback
            )
            
            # Mark task as complete
            render_task.complete(output_path)
            await self._render_task_repository.update(render_task)
            
            # Update project with video URL
            video_url = f"/api/videos/{output_path.split('/')[-1]}"
            project.update_video_url(video_url)
            await self._project_repository.update(project)
            
            return output_path
            
        except Exception as e:
            # Mark task as failed
            render_task.fail(str(e))
            await self._render_task_repository.update(render_task)
            raise
    
    async def get_render_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a render task."""
        render_task = await self._render_task_repository.get_by_id(task_id)
        if not render_task:
            return None
        
        return {
            "status": render_task.status.value,
            "progress": render_task.progress,
            "video_url": render_task.output_file_path,
            "error": render_task.error_message,
            "created_at": render_task.created_at.isoformat(),
            "updated_at": render_task.updated_at.isoformat()
        }