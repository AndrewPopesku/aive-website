from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.music import MusicRecommendation


class MusicRepository(ABC):
    """Abstract repository for MusicRecommendation entities."""
    
    @abstractmethod
    async def create_many(self, music_recs: List[MusicRecommendation]) -> List[MusicRecommendation]:
        """Create multiple music recommendations for a project."""
        pass
    
    @abstractmethod
    async def get_by_project_id(self, project_id: str) -> List[MusicRecommendation]:
        """Get all music recommendations for a project."""
        pass
    
    @abstractmethod
    async def get_by_id(self, music_id: str) -> Optional[MusicRecommendation]:
        """Get a music recommendation by its ID."""
        pass
    
    @abstractmethod
    async def delete_by_project_id(self, project_id: str) -> bool:
        """Delete all music recommendations for a project."""
        pass