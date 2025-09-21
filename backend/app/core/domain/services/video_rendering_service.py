from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from ..entities.sentence import Sentence


class VideoRenderingService(ABC):
    """Abstract service for video rendering."""
    
    @abstractmethod
    async def render_video(
        self,
        project_id: str,
        sentences: List[Sentence],
        music_url: str,
        voice_over_path: str,
        add_subtitles: bool = True,
        include_audio: bool = True,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> str:
        """Render the final video and return the output file path."""
        pass