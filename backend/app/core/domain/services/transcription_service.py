from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Literal
from pathlib import Path
from ..entities.sentence import Sentence


# Type aliases for supported formats and languages
SupportedAudioFormat = Literal[".mp3", ".wav", ".m4a", ".flac", ".aac"]
SupportedLanguage = Literal[
    "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "ar", "hi", "uk"
]


class TranscriptionService(ABC):
    """Abstract service for audio transcription and translation.
    
    This service provides methods for converting audio files to text with
    timestamps and translating text between languages. Implementations
    should handle the specific details of audio processing and API integration.
    """
    
    @abstractmethod
    async def transcribe_audio(
        self, 
        audio_path: str, 
        source_language: Optional[SupportedLanguage] = None
    ) -> List[Sentence]:
        """Transcribe audio file to sentences with timestamps.
        
        Args:
            audio_path: Path to the audio file to transcribe
            source_language: Source language code (auto-detect if None)
            
        Returns:
            List of Sentence entities with text, timing, and translations
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If audio format is unsupported or file is corrupted
            TranscriptionError: If transcription service fails
        """
        # Validate input parameters
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        if audio_file.suffix.lower() not in [".mp3", ".wav", ".m4a", ".flac", ".aac"]:
            raise ValueError(f"Unsupported audio format: {audio_file.suffix}")
        
        ...
    
    @abstractmethod
    async def translate_text(
        self, 
        text: str, 
        target_language: SupportedLanguage = "en",
        source_language: Optional[SupportedLanguage] = None
    ) -> str:
        """Translate text to target language.
        
        Args:
            text: Text to translate
            target_language: Target language code (default: English)
            source_language: Source language code (auto-detect if None)
            
        Returns:
            Translated text string
            
        Raises:
            ValueError: If text is empty or languages are invalid
            TranslationError: If translation service fails
        """
        if not text.strip():
            raise ValueError("Text to translate cannot be empty")
        
        if len(text) > 10000:  # Reasonable limit for API calls
            raise ValueError("Text too long for translation (max 10,000 characters)")
        
        ...
    
    @abstractmethod
    async def get_supported_languages(self) -> List[SupportedLanguage]:
        """Get list of supported languages for transcription and translation.
        
        Returns:
            List of supported language codes
        """
        ...
    
    @abstractmethod
    async def detect_language(self, text: str) -> Optional[SupportedLanguage]:
        """Detect the language of the given text.
        
        Args:
            text: Text to analyze for language detection
            
        Returns:
            Detected language code or None if detection fails
            
        Raises:
            ValueError: If text is empty or too short for detection
        """
        if not text.strip() or len(text.strip()) < 10:
            raise ValueError("Text must be at least 10 characters for language detection")
        
        ...
