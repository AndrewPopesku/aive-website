import os
import uuid
import httpx
import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime

from ....core.domain.entities.sentence import Sentence
from ....core.domain.services.video_rendering_service import VideoRenderingService
from ....config import TEMP_DIR, OUTPUT_DIR

logger = logging.getLogger(__name__)


class MoviePyVideoRenderingService(VideoRenderingService):
    """MoviePy implementation of VideoRenderingService."""
    
    def __init__(self):
        self._temp_dir = TEMP_DIR
        self._output_dir = OUTPUT_DIR
    
    async def render_video(
        self,
        project_id: str,
        sentences: List[Sentence],
        music_url: str,
        voice_over_path: str,
        add_subtitles: bool = True,
        include_audio: bool = True,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> str:
        """Render the final video using MoviePy."""
        render_task_id = f"render-{project_id}-{uuid.uuid4()}"
        project_temp_dir = self._temp_dir / render_task_id
        footage_paths = {}
        video_clips = []
        
        try:
            logger.info(f"[{render_task_id}] Starting video rendering process")
            
            # Create temp directory for project
            project_temp_dir.mkdir(exist_ok=True, parents=True)
            logger.info(f"[{render_task_id}] Created temp directory: {project_temp_dir}")
            
            # Convert sentences to render segments format
            render_segments = []
            for sentence in sentences:
                if sentence.has_footage():
                    render_segments.append({
                        "text": sentence.text,
                        "start_time": sentence.start_time,
                        "end_time": sentence.end_time,
                        "footage_url": sentence.get_footage_url()
                    })
            
            # Download all footage files
            for i, segment in enumerate(render_segments):
                footage_url = segment.get("footage_url")
                if not footage_url:
                    logger.warning(f"[{render_task_id}] No footage URL for segment {i}, skipping")
                    continue
                    
                try:
                    footage_path = project_temp_dir / f"segment_{i}.mp4"
                    await self._download_file(footage_url, footage_path)
                    footage_paths[i] = footage_path
                    
                    # Update progress
                    if progress_callback:
                        progress = int((i + 1) / len(render_segments) * 50)  # First 50% for downloading
                        await progress_callback(progress)
                        
                except Exception as e:
                    logger.error(f"[{render_task_id}] Failed to download footage for segment {i}: {str(e)}")
                    continue
            
            logger.info(f"[{render_task_id}] Downloaded {len(footage_paths)} footage files")
            
            if not footage_paths:
                raise ValueError("No footage files were successfully downloaded")
            
            # Create video using MoviePy
            try:
                from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
                
                # Create clips for each segment
                for i, segment in enumerate(render_segments):
                    if i in footage_paths:
                        try:
                            duration = segment["end_time"] - segment["start_time"]
                            video_path = footage_paths[i]
                            
                            # Create video clip
                            video_clip = VideoFileClip(str(video_path))
                            
                            # Handle duration
                            if video_clip.duration < duration:
                                video_clip = video_clip.loop(duration=duration)
                            else:
                                video_clip = video_clip.subclipped(0, duration)
                            
                            # Resize to standard resolution
                            target_size = (1920, 1080)
                            video_clip = video_clip.resized(target_size)
                            
                            video_clips.append(video_clip)
                            
                            # Update progress
                            if progress_callback:
                                progress = 50 + int((i + 1) / len(render_segments) * 30)  # Next 30% for processing
                                await progress_callback(progress)
                                
                        except Exception as e:
                            logger.error(f"[{render_task_id}] Error creating clip for segment {i}: {str(e)}")
                
                if not video_clips:
                    raise ValueError("No video clips created")
                
                # Concatenate clips
                final_clip = concatenate_videoclips(video_clips)
                
                # Add audio if specified
                if music_url and include_audio:
                    try:
                        audio_clip = AudioFileClip(music_url)
                        
                        # Apply volume adjustment (simple ducking)
                        def volume_adjust(t):
                            return 0.3  # Simple volume reduction
                        
                        audio_clip = audio_clip.fl(lambda gf, t: volume_adjust(t) * gf(t))
                        final_clip = final_clip.with_audio(audio_clip)
                        
                    except Exception as e:
                        logger.error(f"[{render_task_id}] Error adding audio: {str(e)}")
                
                # Generate output filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self._output_dir / f"{project_id}_{timestamp}.mp4"
                
                # Write final video
                final_clip.write_videofile(
                    str(output_path),
                    codec="libx264",
                    audio_codec="aac",
                    temp_audiofile=str(project_temp_dir / "temp_audio.m4a"),
                    remove_temp=True,
                    threads=4,
                    fps=24,
                    logger=None
                )
                
                # Update final progress
                if progress_callback:
                    await progress_callback(100)
                
                logger.info(f"[{render_task_id}] Video rendering completed: {output_path}")
                return str(output_path)
                
            except ImportError:
                raise RuntimeError("MoviePy is not installed. Please install it to use video rendering.")
            
        except Exception as e:
            logger.error(f"[{render_task_id}] Error rendering video: {str(e)}")
            raise
        
        finally:
            # Cleanup temp files
            try:
                for clip in video_clips:
                    try:
                        clip.close()
                    except:
                        pass
                
                for path in footage_paths.values():
                    try:
                        if path.exists():
                            path.unlink()
                    except:
                        pass
                        
                if project_temp_dir.exists():
                    try:
                        project_temp_dir.rmdir()
                    except:
                        pass
            except Exception as e:
                logger.warning(f"[{render_task_id}] Error during cleanup: {str(e)}")
    
    async def _download_file(self, url: str, destination: Path) -> None:
        """Download a file from URL to destination."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            
            with open(destination, 'wb') as f:
                f.write(response.content)
