import asyncio
import logging
from pathlib import Path
from typing import Any

import httpx

from base.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def transcribe_audio(audio_path: str) -> list[dict[str, Any]]:
    """Transcribe audio file using Groq API (Whisper model) and return sentences with timestamps."""
    try:
        headers = {"Authorization": f"Bearer {settings.groq_api_key}"}

        with open(audio_path, "rb") as audio_file:
            files = {"file": ("audio.mp3", audio_file, "audio/mpeg")}

            data = {"model": "whisper-large-v3", "response_format": "verbose_json"}

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.groq_api_url}/audio/transcriptions",
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=60.0,
                )

                if response.status_code != 200:
                    logger.error(f"Groq API error: {response.text}")
                    return []

                result = response.json()

                # Process sentences with timestamps
                sentences = []
                translation_tasks = []

                for segment in result.get("segments", []):
                    sentence_data = {
                        "text": segment["text"],
                        "start": segment["start"],
                        "end": segment["end"],
                    }
                    sentences.append(sentence_data)
                    translation_tasks.append(translate_text(segment["text"]))

                # Execute translations concurrently
                if sentences:
                    translations = await asyncio.gather(
                        *translation_tasks, return_exceptions=True
                    )

                    for i, translation in enumerate(translations):
                        if not isinstance(translation, Exception):
                            sentences[i]["translated_text"] = translation
                        else:
                            sentences[i]["translated_text"] = sentences[i][
                                "text"
                            ]  # Fallback to original

                return sentences

    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        return []


async def translate_text(text: str) -> str:
    """Translate text to English using Groq API for better search results."""
    try:
        if not text.strip():
            return text

        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        prompt = f"Translate the following text to English. Only respond with the translation, nothing else:\n\n{text}"

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional translator. Translate the given text to English accurately.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.groq_api_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30.0,
            )

            if response.status_code != 200:
                logger.error(f"Groq API translation error: {response.text}")
                return text

            result = response.json()
            translation = (
                result.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )

            if not translation:
                logger.warning(f"Empty translation result for: {text}")
                return text

            logger.info(
                f"Successfully translated: '{text[:30]}...' → '{translation[:30]}...'"
            )
            return translation

    except Exception as e:
        logger.error(f"Error translating text: {str(e)}")
        return text


async def generate_project_title(sentences: list[str]) -> str:
    """Generate a concise project title using Groq based on the content."""
    try:
        if not sentences:
            return "Untitled Project"

        # Combine first few sentences for context (limit to avoid token issues)
        content_sample = " ".join(sentences[:3])[:500]

        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        prompt = f"""Based on the following content, generate a short, catchy title (maximum 5 words) that captures the main topic.

Content: {content_sample}

Respond with ONLY the title, nothing else."""

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional content editor. Create short, engaging titles that capture the essence of content.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 50,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.groq_api_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=15.0,
            )

            if response.status_code != 200:
                logger.error(f"Groq API title generation error: {response.text}")
                return "Untitled Project"

            result = response.json()
            title = (
                result.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
                .replace('"', '')  # Remove quotes if present
            )

            if not title or len(title) > 100:  # Sanity check
                logger.warning(f"Invalid title generated: {title}")
                return "Untitled Project"

            logger.info(f"Successfully generated title: '{title}'")
            return title

    except Exception as e:
        logger.error(f"Error generating project title: {str(e)}")
        return "Untitled Project"


async def find_footage_for_sentence(
    text: str, translated_text: str | None = None
) -> str:
    """Find relevant video footage for a sentence using Pexels API."""
    try:
        # Use provided translation or translate on-demand
        if not translated_text:
            translated_text = await translate_text(text)

        # Extract keywords from the translated sentence
        keywords = translated_text.lower().split()
        # Filter out common words
        common_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "is",
            "are",
            "was",
            "were",
            "in",
            "on",
            "at",
            "to",
            "for",
        }
        keywords = [word for word in keywords if word not in common_words]

        # Use the first few keywords for the search
        search_query = " ".join(keywords[:3]) if keywords else "general"

        logger.info(
            f"Searching footage with query: '{search_query}' (translated from: '{text}')"
        )

        headers = {"Authorization": settings.pexels_api_key}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.pexels_api_url}/search?query={search_query}&per_page=1&orientation=landscape",
                headers=headers,
            )

            if response.status_code != 200:
                logger.error(f"Pexels API error: {response.text}")
                return "https://www.pexels.com/video/waves-crashing-on-beach-1409899/"

            result = response.json()
            videos = result.get("videos", [])

            if not videos:
                return "https://www.pexels.com/video/waves-crashing-on-beach-1409899/"

            # Get the video file with the highest quality but reasonable size
            video_files = sorted(
                videos[0].get("video_files", []),
                key=lambda x: (x.get("width", 0) * x.get("height", 0)),
                reverse=True,
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


async def find_background_music(
    sentence_texts: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Find background music from the local audio directory."""
    try:
        # Get all available music files from the audio directory
        music_files = list(settings.audio_dir.glob("*.mp3"))

        if not music_files:
            logger.warning("No music files found in audio directory")
            return []

        # Create music recommendations from available files
        music_recommendations = []
        for i, music_file in enumerate(music_files):
            music_id = f"music-{i + 1}"
            name = music_file.stem  # Use filename without extension as the name

            # Create URL that can be served by the static files endpoint
            relative_path = music_file.relative_to(settings.audio_dir)
            audio_url = f"/api/audio/{relative_path}"

            music_recommendations.append(
                {"id": music_id, "name": name, "url": audio_url}
            )

            logger.info(f"Added music file: {name} at {music_file}")

        return music_recommendations
    except Exception as e:
        logger.error(f"Error finding background music: {str(e)}")
        return []


async def download_file(url: str, destination: Path) -> bool:
    """Download a file from URL to destination path."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=60.0)
            response.raise_for_status()

            with open(destination, "wb") as f:
                f.write(response.content)

            logger.info(f"Successfully downloaded file to {destination}")
            return True

    except Exception as e:
        logger.error(f"Error downloading file from {url}: {str(e)}")
        return False
