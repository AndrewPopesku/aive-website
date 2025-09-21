from typing import Optional
from dataclasses import dataclass, field
import uuid


@dataclass
class MusicRecommendation:
    """Music recommendation domain entity."""
    
    id: str = field(default_factory=lambda: f"music-{str(uuid.uuid4())}")
    project_id: str = ""
    title: str = ""
    artist: str = ""
    genre: Optional[str] = None
    mood: Optional[str] = None
    energy_level: Optional[int] = None
    url: str = ""
    duration: Optional[float] = None
    
    def is_valid(self) -> bool:
        """Check if the music recommendation has all required fields."""
        return bool(self.title and self.artist and self.url)
    
    def matches_mood(self, target_mood: str) -> bool:
        """Check if this music matches a target mood."""
        if not self.mood or not target_mood:
            return True  # Default to match if no mood specified
        return self.mood.lower() == target_mood.lower()