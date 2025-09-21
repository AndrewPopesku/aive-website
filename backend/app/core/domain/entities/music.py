from __future__ import annotations

from typing import Optional, Literal, Union
from dataclasses import dataclass, field
import uuid


# Type aliases for better type safety
EnergyLevel = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
MoodType = Literal[
    "happy", "sad", "energetic", "calm", "upbeat", "melancholic", 
    "dramatic", "romantic", "mysterious", "triumphant", "peaceful"
]
GenreType = Literal[
    "ambient", "classical", "electronic", "pop", "rock", "jazz", 
    "cinematic", "orchestral", "acoustic", "experimental"
]


@dataclass
class MusicRecommendation:
    """Music recommendation domain entity.
    
    Attributes:
        id: Unique identifier for the music recommendation
        project_id: ID of the associated project
        title: Title/name of the music track
        artist: Artist or composer name
        genre: Genre classification (optional)
        mood: Mood descriptor (optional)
        energy_level: Energy level from 1-10 (optional)
        url: URL or path to the music file
        duration: Duration in seconds (optional)
    """
    
    id: str = field(default_factory=lambda: f"music-{str(uuid.uuid4())}")
    project_id: str = ""
    title: str = ""
    artist: str = ""
    genre: Optional[Union[GenreType, str]] = None
    mood: Optional[Union[MoodType, str]] = None
    energy_level: Optional[Union[EnergyLevel, int]] = None
    url: str = ""
    duration: Optional[float] = None
    
    def __post_init__(self) -> None:
        """Validate music recommendation data after initialization."""
        if self.energy_level is not None:
            if not isinstance(self.energy_level, int) or not (1 <= self.energy_level <= 10):
                raise ValueError("Energy level must be an integer between 1 and 10")
        
        if self.duration is not None and self.duration < 0:
            raise ValueError("Duration cannot be negative")
    
    def is_valid(self) -> bool:
        """Check if the music recommendation has all required fields.
        
        Returns:
            True if title, artist, and url are non-empty, False otherwise
        """
        return bool(
            self.title.strip() 
            and self.artist.strip() 
            and self.url.strip()
        )
    
    def matches_mood(self, target_mood: Optional[Union[MoodType, str]]) -> bool:
        """Check if this music matches a target mood.
        
        Args:
            target_mood: The mood to match against (case-insensitive)
            
        Returns:
            True if moods match or if either mood is None/empty, False otherwise
        """
        if not self.mood or not target_mood:
            return True  # Default to match if no mood specified
        return self.mood.lower().strip() == target_mood.lower().strip()
    
    def get_energy_description(self) -> str:
        """Get a human-readable description of the energy level.
        
        Returns:
            Description string for the energy level
        """
        if self.energy_level is None:
            return "Unknown energy"
        
        energy_descriptions = {
            1: "Very low energy", 2: "Low energy", 3: "Calm", 4: "Moderate",
            5: "Balanced", 6: "Energetic", 7: "High energy", 8: "Very high energy",
            9: "Intense", 10: "Maximum energy"
        }
        return energy_descriptions.get(self.energy_level, "Unknown energy")
    
    def format_duration(self) -> str:
        """Format duration as MM:SS string.
        
        Returns:
            Formatted duration string or 'Unknown' if duration is None
        """
        if self.duration is None:
            return "Unknown"
        
        minutes = int(self.duration // 60)
        seconds = int(self.duration % 60)
        return f"{minutes:02d}:{seconds:02d}"
