import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx

from base.config import get_settings

# Import MoviePy components
if TYPE_CHECKING:
    from moviepy import (
        AudioFileClip,
        CompositeAudioClip,
        CompositeVideoClip,
        TextClip,
        VideoFileClip,
        concatenate_audioclips,
        concatenate_videoclips,
    )
else:
    try:
        # MoviePy 2.x uses direct imports from moviepy package
        from moviepy import (
            AudioFileClip,
            CompositeAudioClip,
            CompositeVideoClip,
            TextClip,
            VideoFileClip,
            concatenate_audioclips,
            concatenate_videoclips,
        )

        MOVIEPY_AVAILABLE = True
    except ImportError:
        # Define placeholder classes for runtime when MoviePy is not available
        class VideoFileClip:  # type: ignore
            pass

        class AudioFileClip:  # type: ignore
            pass

        class TextClip:  # type: ignore
            pass

        class CompositeVideoClip:  # type: ignore
            pass

        class CompositeAudioClip:  # type: ignore
            pass

        def concatenate_videoclips(*args, **kwargs):  # type: ignore
            pass

        def concatenate_audioclips(*args, **kwargs):  # type: ignore
            pass

        MOVIEPY_AVAILABLE = False
        logging.warning("MoviePy not available. Video rendering will be disabled.")

logger = logging.getLogger(__name__)
settings = get_settings()


async def download_video_file(url: str, destination: Path) -> bool:
    """Download a video file from URL to destination path."""
    try:
        logger.info(f"Downloading video from {url} to {destination}")

        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True, timeout=60.0)
            response.raise_for_status()

            with open(destination, "wb") as f:
                f.write(response.content)

            logger.info(f"Successfully downloaded video to {destination}")
            return True

    except Exception as e:
        logger.error(f"Error downloading video from {url}: {str(e)}")
        return False


class VideoEditor:
    """Video editor for creating final rendered videos from project data."""

    def __init__(
        self, temp_dir: Path | None = None, output_dir: Path | None = None
    ) -> None:
        self.temp_dir = temp_dir or settings.temp_dir
        self.output_dir = output_dir or settings.output_dir

        # Ensure directories exist
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def render_project_video(
        self,
        project_data: dict[str, Any],
        audio_file_path: str,
        music_file_path: str | None = None,
        output_filename: str | None = None,
    ) -> str:
        """Render a complete video from project data."""
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("MoviePy is not available. Cannot render video.")

        project_id = project_data["id"]
        if not output_filename:
            output_filename = f"{project_id}_final_video.mp4"

        # Add timestamp to filename to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_parts = output_filename.rsplit(".", 1)
        if len(name_parts) == 2:
            timestamped_filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
        else:
            timestamped_filename = f"{output_filename}_{timestamp}"

        output_path = self.output_dir / timestamped_filename

        try:
            # Step 1: Download all footage
            logger.info("Downloading footage files...")
            await self._download_footage(project_data["sentences"])

            # Step 2: Create video clips with subtitles
            logger.info("Creating video clips...")
            video_clips = self._create_video_clips(project_data["sentences"])

            if not video_clips:
                raise ValueError("No video clips were created")

            # Step 3: Combine video clips
            logger.info("Combining video clips...")
            final_video = concatenate_videoclips(video_clips, method="compose")

            # Step 4: Add audio (voice-over)
            logger.info("Adding voice-over audio...")
            if os.path.exists(audio_file_path):
                voice_audio = AudioFileClip(audio_file_path)
                final_video = final_video.with_audio(voice_audio)  # type: ignore

            # Step 5: Add background music if provided
            if music_file_path and os.path.exists(music_file_path):
                logger.info("Adding background music...")
                music_audio = AudioFileClip(music_file_path)

                # Adjust music volume to be quieter than voice
                music_audio = music_audio.fx(lambda gf, t: 0.3 * gf(t))  # type: ignore

                # Loop music to match video duration if needed
                if music_audio.duration < final_video.duration:  # type: ignore
                    # Loop music by repeating it
                    times_to_loop = int(final_video.duration / music_audio.duration) + 1  # type: ignore
                    music_audio = concatenate_audioclips([music_audio] * times_to_loop).subclipped(0, final_video.duration)  # type: ignore
                else:
                    music_audio = music_audio.subclipped(0, final_video.duration)  # type: ignore

                # Combine voice and music
                if final_video.audio:  # type: ignore
                    composite_audio = CompositeAudioClip(
                        [final_video.audio, music_audio]  # type: ignore
                    )
                    final_video = final_video.with_audio(composite_audio)  # type: ignore
                else:
                    final_video = final_video.with_audio(music_audio)  # type: ignore

            # Step 6: Export final video
            logger.info(f"Exporting final video to {output_path}...")
            final_video.write_videofile(
                str(output_path),
                fps=24,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
            )

            # Clean up
            final_video.close()

            logger.info(f"Video rendering completed: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Error rendering video: {str(e)}")
            raise

    async def _download_footage(self, sentences: list[dict[str, Any]]) -> None:
        """Download all footage files for the sentences."""
        download_tasks = []

        for i, sentence in enumerate(sentences):
            selected_footage = sentence.get("selected_footage")
            if not selected_footage or not selected_footage.get("url"):
                logger.warning(f"Sentence {i} has no selected footage URL")
                continue

            footage_url = selected_footage["url"]
            # Create a unique filename for this footage
            file_extension = ".mp4"  # Default to mp4
            if "." in footage_url.split("/")[-1]:
                file_extension = "." + footage_url.split(".")[-1].split("?")[0]

            filename = f"footage_{i}_{sentence.get('id', i)}{file_extension}"
            local_path = self.temp_dir / filename

            # Store local path for later use
            sentence["_local_footage_path"] = str(local_path)

            # Add download task if file doesn't exist
            if not local_path.exists():
                download_tasks.append(download_video_file(footage_url, local_path))

        # Download all footage concurrently
        if download_tasks:
            results = await asyncio.gather(*download_tasks, return_exceptions=True)
            failed_downloads = sum(
                1 for result in results if not result or isinstance(result, Exception)
            )
            if failed_downloads > 0:
                logger.warning(f"{failed_downloads} footage downloads failed")

    def _create_video_clips(
        self, sentences: list[dict[str, Any]]
    ) -> list[Any]:  # Returns list of VideoFileClip but using Any to avoid type issues
        """Create video clips with subtitles for each sentence."""
        clips = []

        for sentence in sentences:
            local_footage_path = sentence.get("_local_footage_path")
            if not local_footage_path or not os.path.exists(local_footage_path):
                logger.warning(
                    f"Local footage not found for sentence: {sentence.get('text', 'Unknown')}"
                )
                continue

            try:
                # Calculate clip duration from sentence timing
                start_time = sentence.get("start_time", 0)
                end_time = sentence.get("end_time", start_time + 5)
                duration = end_time - start_time

                # Load video clip
                video_clip = VideoFileClip(local_footage_path)

                # Trim to sentence duration (or use full clip if shorter)
                if video_clip.duration > duration:  # type: ignore
                    video_clip = video_clip.subclipped(0, duration)  # type: ignore
                else:
                    # If footage is shorter, loop it or extend
                    if duration > video_clip.duration * 2:  # type: ignore
                        # Loop video by repeating it
                        times_to_loop = int(duration / video_clip.duration) + 1  # type: ignore
                        video_clip = concatenate_videoclips([video_clip] * times_to_loop).subclipped(0, duration)  # type: ignore
                    else:
                        video_clip = video_clip.with_duration(duration)  # type: ignore

                # Resize to standard HD resolution
                if video_clip.w != 1920 or video_clip.h != 1080:  # type: ignore
                    video_clip = video_clip.resized(newsize=(1920, 1080))  # type: ignore

                # Add subtitle if text exists
                text = sentence.get("text", "").strip()
                if text:
                    try:
                        # Create subtitle
                        subtitle = TextClip(
                            text=text,
                            font_size=50,
                            color="white",
                            font="Arial",
                            stroke_color="black",
                            stroke_width=2,
                            size=(1800, None),  # Max width with margins
                            method="caption",
                        ).with_duration(duration)  # type: ignore

                        # Position subtitle at bottom of screen
                        subtitle = subtitle.with_position(("center", "bottom"))  # type: ignore

                        # Composite video with subtitle
                        video_clip = CompositeVideoClip([video_clip, subtitle])

                    except Exception as e:
                        logger.warning(f"Could not add subtitle '{text}': {str(e)}")

                clips.append(video_clip)

            except Exception as e:
                logger.error(
                    f"Error creating clip for sentence '{sentence.get('text', 'Unknown')}': {str(e)}"
                )
                continue

        return clips


async def render_project_video(
    project_data: dict[str, Any],
    audio_file_path: str,
    music_file_path: str | None = None,
    output_filename: str | None = None,
) -> str:
    """Convenience function to render a project video."""
    editor = VideoEditor()
    return await editor.render_project_video(
        project_data=project_data,
        audio_file_path=audio_file_path,
        music_file_path=music_file_path,
        output_filename=output_filename,
    )
