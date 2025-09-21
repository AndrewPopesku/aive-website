from abc import ABC, abstractmethod
from typing import List


class FootageService(ABC):
    """Abstract service for finding and managing video footage."""
    
    @abstractmethod
    async def find_footage_for_sentence(self, text: str, translated_text: str = None) -> str:
        """Find relevant video footage URL for a sentence."""
        pass