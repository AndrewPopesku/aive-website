import logging
from pathlib import Path
from typing import List

from ....core.domain.entities.music import MusicRecommendation
from ....core.domain.services.music_service import MusicService
from ....config import AUDIO_DIR

logger = logging.getLogger(__name__)


class LocalMusicService(MusicService):
    """Local file system implementation of MusicService."""
    
    def __init__(self):
        self._audio_dir = AUDIO_DIR
    
    async def find_background_music(self, sentence_texts: List[str] = None) -> List[MusicRecommendation]:
        """Find background music from the local audio directory."""
        try:
            # Get all available music files from the AUDIO_DIR
            music_files = list(self._audio_dir.glob("*.mp3"))
            
            if not music_files:
                logger.warning("No music files found in audio directory")
                return []
            
            # Create music recommendations from available files
            music_recommendations = []
            for i, music_file in enumerate(music_files):
                name = music_file.stem  # Use filename without extension as the name
                file_path = str(music_file)
                
                music_recommendation = MusicRecommendation(
                    title=name,
                    artist="Local File",
                    genre="Ambient",
                    mood="Neutral",
                    energy_level=5,
                    url=file_path,
                    duration=60.0  # Default duration, would need audio analysis for actual duration
                )
                music_recommendations.append(music_recommendation)
                
                logger.info(f"Added music file: {name} at {file_path}")
            
            return music_recommendations
            
        except Exception as e:
            logger.error(f"Error finding background music: {str(e)}")
            return []