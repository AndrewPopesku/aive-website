from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import uuid


@dataclass
class SelectedFootage:
    """Selected footage for a sentence."""
    
    id: str
    title: str
    description: str
    thumbnail: str
    duration: float
    tags: list[str]
    category: str
    mood: str
    relevance_score: int
    url: str


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
        """Calculate the duration of this sentence."""
        return self.end_time - self.start_time
    
    def set_selected_footage(self, footage: SelectedFootage) -> None:
        """Set the selected footage for this sentence."""
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
        """Check if this sentence has selected footage."""
        return bool(self.selected_footage and self.selected_footage.get("url"))
    
    def get_footage_url(self) -> Optional[str]:
        """Get the footage URL if available."""
        if self.selected_footage:
            return self.selected_footage.get("url")
        return None
    
    def is_valid(self) -> bool:
        """Check if the sentence has valid timing and text."""
        return bool(self.text.strip() and self.start_time < self.end_time)