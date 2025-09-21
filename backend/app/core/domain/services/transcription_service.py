from abc import ABC, abstractmethod
from typing import List
from ..entities.sentence import Sentence


class TranscriptionService(ABC):
    """Abstract service for audio transcription."""
    
    @abstractmethod
    async def transcribe_audio(self, audio_path: str) -> List[Sentence]:
        """Transcribe audio file to sentences with timestamps."""
        pass
    
    @abstractmethod
    async def translate_text(self, text: str) -> str:
        """Translate text to English for better search results."""
        pass