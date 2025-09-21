from abc import ABC, abstractmethod
from typing import List
from ..entities.music import MusicRecommendation


class MusicService(ABC):
    """Abstract service for finding background music."""
    
    @abstractmethod
    async def find_background_music(self, sentence_texts: List[str] = None) -> List[MusicRecommendation]:
        """Find background music recommendations based on sentence texts."""
        pass