from __future__ import annotations

from typing import Optional, Final
from datetime import datetime
from dataclasses import dataclass, field
import uuid


@dataclass
class Project:
    """Project domain entity representing a video creation project."""
    
    id: str = field(default_factory=lambda: f"proj-{str(uuid.uuid4())}")
    title: str = ""
    description: Optional[str] = None
    audio_file_path: Optional[str] = None
    total_duration: Optional[float] = None
    overall_mood: Optional[str] = None
    video_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def update_video_url(self, video_url: str) -> None:
        """Update the video URL when rendering is complete.
        
        Args:
            video_url: The URL of the rendered video
        """
        self.video_url = video_url
        self.updated_at = datetime.utcnow()
    
    def update_duration(self, duration: float) -> None:
        """Update the total duration of the project.
        
        Args:
            duration: The total duration in seconds
        
        Raises:
            ValueError: If duration is negative
        """
        if duration < 0:
            raise ValueError("Duration cannot be negative")
        self.total_duration = duration
        self.updated_at = datetime.utcnow()
    
    def update_mood(self, mood: str) -> None:
        """Update the overall mood of the project.
        
        Args:
            mood: The mood descriptor (e.g., 'happy', 'sad', 'energetic')
        """
        if not mood.strip():
            raise ValueError("Mood cannot be empty")
        self.overall_mood = mood.strip()
        self.updated_at = datetime.utcnow()
    
    def is_ready_for_render(self) -> bool:
        """Check if the project is ready for rendering.
        
        Returns:
            True if project has audio file and duration, False otherwise
        """
        return bool(self.audio_file_path and self.total_duration)
