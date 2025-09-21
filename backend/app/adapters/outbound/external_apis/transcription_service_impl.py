import httpx
import asyncio
import logging
from typing import List

from ....core.domain.entities.sentence import Sentence
from ....core.domain.services.transcription_service import TranscriptionService
from ....config import GROQ_API_KEY, GROQ_API_URL

logger = logging.getLogger(__name__)


class GroqTranscriptionService(TranscriptionService):
    """Groq API implementation of TranscriptionService."""
    
    def __init__(self):
        self._api_key = GROQ_API_KEY
        self._api_url = GROQ_API_URL
    
    async def transcribe_audio(self, audio_path: str) -> List[Sentence]:
        """Transcribe audio file using Groq API (Whisper model)."""
        try:
            headers = {
                "Authorization": f"Bearer {self._api_key}"
            }
            
            with open(audio_path, "rb") as audio_file:
                files = {
                    "file": ("audio.mp3", audio_file, "audio/mpeg")
                }
                
                data = {
                    "model": "whisper-large-v3",
                    "response_format": "verbose_json"
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self._api_url}/audio/transcriptions",
                        headers=headers,
                        data=data,
                        files=files,
                        timeout=60.0
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"Groq API error: {response.text}")
                        return []
                    
                    result = response.json()
                    
                    # Process sentences with timestamps
                    sentences = []
                    translation_tasks = []
                    
                    # First create all sentence objects with original text
                    for segment in result.get("segments", []):
                        sentence = Sentence(
                            text=segment["text"],
                            start_time=segment["start"],
                            end_time=segment["end"]
                        )
                        sentences.append(sentence)
                        # Create translation tasks for each sentence
                        translation_tasks.append(self.translate_text(segment["text"]))
                    
                    # Execute all translation tasks concurrently
                    if sentences:
                        translations = await asyncio.gather(*translation_tasks)
                        
                        # Assign translations to sentences
                        for i, translation in enumerate(translations):
                            sentences[i].translated_text = translation
                    
                    return sentences
        
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return []
    
    async def translate_text(self, text: str) -> str:
        """Translate text to English using Groq API (LLM model)."""
        try:
            if not text.strip():
                return text
                
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"Translate the following text to English. Only respond with the translation, nothing else:\n\n{text}"
            
            data = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are a professional translator. Translate the given text to English accurately."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 1024
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._api_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Groq API translation error: {response.text}")
                    return text
                
                result = response.json()
                translation = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                
                if not translation:
                    logger.warning(f"Empty translation result for: {text}")
                    return text
                    
                logger.info(f"Successfully translated text: '{text[:30]}...' → '{translation[:30]}...'")
                return translation
                
        except Exception as e:
            logger.error(f"Error translating text: {str(e)}")
            return text