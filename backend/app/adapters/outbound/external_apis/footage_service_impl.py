import httpx
import logging
from typing import List

from ....core.domain.services.footage_service import FootageService
from ....config import PEXELS_API_KEY, PEXELS_API_URL

logger = logging.getLogger(__name__)


class PexelsFootageService(FootageService):
    """Pexels API implementation of FootageService."""
    
    def __init__(self):
        self._api_key = PEXELS_API_KEY
        self._api_url = PEXELS_API_URL
    
    async def find_footage_for_sentence(self, text: str, translated_text: str = None) -> str:
        """Find relevant video footage for a sentence using Pexels API."""
        try:
            # Use translated text if available, otherwise use original
            search_text = translated_text or text
            
            # Extract keywords from the text
            keywords = search_text.lower().split()
            # Filter out common words
            common_words = {"the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "in", "on", "at", "to", "for"}
            keywords = [word for word in keywords if word not in common_words]
            
            # Use the first few keywords for the search
            search_query = " ".join(keywords[:3]) if keywords else "general"
            
            logger.info(f"Searching footage with query: '{search_query}' (from: '{text}')")
            
            headers = {"Authorization": self._api_key}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._api_url}/search?query={search_query}&per_page=1&orientation=landscape",
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Pexels API error: {response.text}")
                    # Return a default/fallback video
                    return "https://www.pexels.com/video/waves-crashing-on-beach-1409899/"
                
                result = response.json()
                videos = result.get("videos", [])
                
                if not videos:
                    return "https://www.pexels.com/video/waves-crashing-on-beach-1409899/"
                
                # Get the video file with the highest quality but reasonable size
                video_files = sorted(
                    videos[0].get("video_files", []),
                    key=lambda x: (x.get("width", 0) * x.get("height", 0)),
                    reverse=True
                )
                
                if video_files:
                    for file in video_files:
                        if file.get("width", 0) <= 1920:  # Limit to Full HD
                            return file.get("link", "")
                
                # Fallback
                return videos[0].get("video_files", [{}])[0].get("link", "")
                
        except Exception as e:
            logger.error(f"Error finding footage: {str(e)}")
            return ""