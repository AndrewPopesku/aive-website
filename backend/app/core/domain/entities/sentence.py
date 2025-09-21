from __future__ import annotations

from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
import uuid


@dataclass
class SelectedFootage:
    """Selected footage for a sentence.
    
    Attributes:
        id: Unique identifier for the footage
        title: Display title of the footage
        description: Detailed description
        thumbnail: URL to thumbnail image
        duration: Duration of the footage in seconds
        tags: List of descriptive tags
        category: Category type (e.g., 'recommended', 'user-selected')
        mood: Mood descriptor (e.g., 'happy', 'energetic')
        relevance_score: Relevance score from 0-100
        url: Direct URL to the video file
    """
    
    id: str
    title: str
    description: str
    thumbnail: str
    duration: float
    tags: List[str]
    category: str
    mood: str
    relevance_score: int
    url: str
    
    def __post_init__(self) -> None:
        """Validate footage data after initialization."""
        if not self.id.strip():
            raise ValueError("Footage ID cannot be empty")
        if self.duration < 0:
            raise ValueError("Duration cannot be negative")
        if not (0 <= self.relevance_score <= 100):
            raise ValueError("Relevance score must be between 0 and 100")
        if not self.url.strip():
            raise ValueError("URL cannot be empty")


@dataclass
class Sentence:
    """Sentence domain entity representing a transcribed sentence with timing."""
    
    id: str = field(default_factory=lambda: f"sent-{str(uuid.uuid4())}")
    project_id: str = ""
    text: str = ""
    translated_text: Optional[str] = None
    start_time: float = 0.0
    end_time: float = 0.0
    selected_footage: Optional[Dict[str, Any]] = None
    
    @property
    def duration(self) -> float:
        """Calculate the duration of this sentence.
        
        Returns:
            Duration in seconds (end_time - start_time)
        """
        return max(0.0, self.end_time - self.start_time)
    
    def set_selected_footage(self, footage: SelectedFootage) -> None:
        """Set the selected footage for this sentence.
        
        Args:
            footage: The SelectedFootage instance to associate with this sentence
            
        Raises:
            TypeError: If footage is not a SelectedFootage instance
        """
        if not isinstance(footage, SelectedFootage):
            raise TypeError("footage must be a SelectedFootage instance")
            
        self.selected_footage = {
            "id": footage.id,
            "title": footage.title,
            "description": footage.description,
            "thumbnail": footage.thumbnail,
            "duration": footage.duration,
            "tags": footage.tags,
            "category": footage.category,
            "mood": footage.mood,
            "relevance_score": footage.relevance_score,
            "url": footage.url
        }
    
    def has_footage(self) -> bool:
        """Check if this sentence has selected footage.
        
        Returns:
            True if sentence has footage with a valid URL, False otherwise
        """
        return bool(
            self.selected_footage 
            and self.selected_footage.get("url") 
            and self.selected_footage["url"].strip()
        )
    
    def get_footage_url(self) -> Optional[str]:
        """Get the footage URL if available.
        
        Returns:
            The footage URL string if available, None otherwise
        """
        if self.selected_footage and "url" in self.selected_footage:
            url = self.selected_footage["url"]
            return url.strip() if url and url.strip() else None
        return None
    
    def is_valid(self) -> bool:
        """Check if the sentence has valid timing and text.
        
        Returns:
            True if sentence has non-empty text and valid timing, False otherwise
        """
        return bool(
            self.text.strip() 
            and self.start_time >= 0
            and self.end_time > self.start_time
        )
