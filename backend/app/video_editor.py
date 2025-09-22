import logging
import os
import uuid
import httpx
import asyncio
from pathlib import Path
from typing import List, Dict, Any
import aiohttp

from datetime import datetime
from moviepy.editor import (
    VideoFileClip, 
    AudioFileClip, 
    TextClip,
    CompositeVideoClip, 
    CompositeAudioClip,
    concatenate_videoclips,
    concatenate_audioclips,
    afx,
    vfx
)

logger = logging.getLogger(__name__)

async def download_file(url: str, destination: Path) -> Path:
    """
    Download a file from a URL to a local destination.
    """
    try:
        # Convert Pydantic HttpUrl to string if needed
        if hasattr(url, '__str__'):
            url = str(url)
        
        logger.info(f"Downloading file from {url} to {destination}")
        
        async with httpx.AsyncClient() as client:
            # Use a reasonable timeout to avoid hanging
            response = await client.get(url, follow_redirects=True, timeout=30.0)
            response.raise_for_status()
            
            with open(destination, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Successfully downloaded file: {destination}")
            return destination
    except httpx.TimeoutException:
        logger.error(f"Timeout downloading file from {url}")
        raise
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error downloading file from {url}: {e.response.status_code} {e.response.reason_phrase}")
        raise
    except Exception as e:
        logger.error(f"Error downloading file from {url}: {str(e)}")
        raise


class VideoEditor:
    """
    A class to edit and render a video based on project data.

    This class handles downloading footage, creating video clips with subtitles,
    and combining them with a voice-over and background music.
    """

    def __init__(self, temp_dir=None, output_dir=None, project_data=None, voice_over_path=None, background_music_path=None):
        """
        Initialize the VideoEditor with required directories or project data.
        
        Supports both the old and new constructor signatures for backward compatibility.
        
        Old signature:
            temp_dir: Directory for temporary files
            output_dir: Directory for output videos
        
        New signature:
            project_data: A dictionary containing the project details
            voice_over_path: The file path to the voice-over audio
            background_music_path: The file path to the background music
        """
        # Support for the old constructor signature
        if temp_dir is not None and output_dir is not None:
            self.temp_dir = temp_dir
            self.output_dir = output_dir
            self.project_data = None
            self.voice_over_path = None
            self.background_music_path = None
        # Support for the new constructor signature
        elif project_data is not None:
            self.project_data = project_data
            self.voice_over_path = voice_over_path
            self.background_music_path = background_music_path
            self.temp_dir = Path("temp_footage")
            os.makedirs(self.temp_dir, exist_ok=True)
            self.output_dir = Path("output")
            os.makedirs(self.output_dir, exist_ok=True)
        else:
            raise ValueError("Invalid constructor arguments. Either provide temp_dir and output_dir, or project_data.")

    async def _download_file(self, session: aiohttp.ClientSession, url: str, path: str):
        """Asynchronously downloads a file from a URL."""
        async with session.get(url) as response:
            response.raise_for_status()
            with open(path, 'wb') as f:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    f.write(chunk)

    async def _download_footage(self):
        """Downloads all the video footage required for the project."""
        tasks = []
        async with aiohttp.ClientSession() as session:
            for sentence in self.project_data["sentences"]:
                footage_url = sentence["selected_footage"]["url"]
                file_name = os.path.basename(footage_url)
                local_path = os.path.join(self.temp_dir, file_name)
                sentence["selected_footage"]["local_path"] = local_path
                if not os.path.exists(local_path):
                    tasks.append(self._download_file(session, footage_url, local_path))
            await asyncio.gather(*tasks)

    def _create_clips(self) -> List[VideoFileClip]:
        """Creates individual video clips for each sentence with subtitles."""
        clips = []
        
        for sentence in self.project_data["sentences"]:
            local_path = sentence["selected_footage"]["local_path"]
            start_time = sentence["start"]
            end_time = sentence["end"]
            duration = end_time - start_time
            
            # Load the video clip
            video_clip = VideoFileClip(local_path).subclipped(0, duration)
            
            # Scale to full width while maintaining aspect ratio
            # This may result in cropping top/bottom if the ratio differs
            target_width = 1920  # Standard full HD width
            scale_factor = target_width / video_clip.w
            new_height = int(video_clip.h * scale_factor)
            
            # Resize the clip to target width, maintaining aspect ratio
            video_clip = video_clip.resized(width=target_width)
            
            # Create subtitle for this sentence
            if "text" in sentence:
                # Create a TextClip with the sentence text
                txt_clip = TextClip(
                    text=sentence["text"],
                    font=None,  # Use default font
                    font_size=40,  # Reduced font size to prevent cropping
                    color='white',
                    stroke_color='black',
                    stroke_width=2,
                    size=(int(target_width * 0.9), None),  # Convert float to integer
                    method='caption',
                    text_align='center'
                )
                
                # Set duration to match video clip
                txt_clip = txt_clip.with_duration(duration)
                
                # Position the text higher on the screen with explicit numerical coordinates
                # 'center' for horizontal alignment, and place it 80% down the screen
                txt_clip = txt_clip.with_position(('center', 0.75), relative=True)
                
                # Composite the video and subtitle
                composed_clip = CompositeVideoClip([video_clip, txt_clip])
            else:
                # If no text is available, just use the video clip
                composed_clip = CompositeVideoClip([video_clip])
            
            clips.append(composed_clip)

        return clips

    async def render_video_new(self, output_path: str = "output.mp4"):
        """
        Renders the final video by combining all clips, audio, and subtitles.

        Args:
            output_path (str): The path to save the final rendered video.

        Returns:
            str: The path to the rendered video file.
        """
        print("Downloading footage...")
        await self._download_footage()

        print("Creating video clips...")
        video_clips = self._create_clips()

        if not video_clips:
            raise ValueError("No video clips were created. Check the project data.")

        # Get last sentence end time and add 2 seconds
        last_sentence_end = self.project_data["sentences"][-1]["end"]
        total_duration = last_sentence_end + 2.0  # Add 2 seconds fadeout
        
        # Create a composite clip with the exact duration we need
        final_clip = concatenate_videoclips(video_clips, method="compose")
        final_clip = final_clip.with_duration(total_duration)  # Force specific duration
        
        print(f"Final video duration will be: {total_duration} seconds")

        # Add audio
        voice_over = AudioFileClip(self.voice_over_path)
        background_music = AudioFileClip(self.background_music_path)

        # Ensure voice-over matches the final clip duration
        voice_over = voice_over.with_duration(total_duration)

        # Ensure background music matches the final clip duration (trim or loop as needed)
        if background_music.duration < total_duration:
            # Loop the background music if it's too short
            n_loops = int(total_duration / background_music.duration) + 1
            background_music = background_music.loop(n_loops)
        # Trim to exact duration needed
        background_music = background_music.with_duration(total_duration)
        
        # Apply volume adjustment and fade-out effect to background music
        background_music = background_music.with_effects([
            lambda c: c.with_volume(0.1),  # Adjust volume to 10%
            lambda c: c.with_audio_fadeout(2.0)  # Fade out last 2 seconds
        ])
        
        final_audio = CompositeAudioClip([voice_over, background_music])
        final_clip = final_clip.with_audio(final_audio)

        print(f"Rendering video to {output_path}...")
        final_clip.write_videofile(output_path, 
                                   codec="libx264", 
                                   audio_codec="aac", 
                                   temp_audiofile='temp-audio.m4a',
                                   remove_temp=True)

        # Clean up temporary files
        print("Cleaning up...")
        for clip in video_clips:
            clip.close()

        voice_over.close()
        background_music.close()
        final_clip.close()

        for sentence in self.project_data["sentences"]:
            if "local_path" in sentence["selected_footage"] and os.path.exists(
                    sentence["selected_footage"]["local_path"]):
                try:
                    os.remove(sentence["selected_footage"]["local_path"])
                except OSError as e:
                    print(f"Error removing file {sentence['selected_footage']['local_path']}: {e}")

        try:
            # Check if directory is empty before removing
            if not os.listdir(self.temp_dir):
                os.rmdir(self.temp_dir)
        except OSError as e:
            print(f"Error removing directory {self.temp_dir}: {e}")

        print("Video rendering complete.")
        return output_path

    def _format_project_data(self, project_id: str, render_segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format the render segments into the structure expected by the rendering functions
        """
        sentences = []
        
        for i, segment in enumerate(render_segments):
            sentence = {
                "sentence_id": segment.get("id", f"sent-{i}"),
                "text": segment.get("text", ""),
                "start": segment.get("start_time", 0),
                "end": segment.get("end_time", 0),
                "selected_footage": {
                    "url": segment.get("footage_url", ""),
                    "local_path": ""  # Will be filled during download
                }
            }
            sentences.append(sentence)
        
        return {
            "project_id": project_id,
            "sentences": sentences
        }

    async def _download_footage_legacy(self, project_data: Dict[str, Any], project_temp_dir: Path):
        """
        Download all the video footage required for the project
        """
        tasks = []
        
        for sentence in project_data["sentences"]:
            footage_url = sentence["selected_footage"]["url"]
            if not footage_url:
                continue
                
            file_name = Path(footage_url).name
            local_path = project_temp_dir / file_name
            sentence["selected_footage"]["local_path"] = str(local_path)
            
            if not local_path.exists():
                tasks.append(download_file(footage_url, local_path))
        
        if tasks:
            await asyncio.gather(*tasks)
        
        logger.info(f"Downloaded {len(tasks)} footage files")

    def _create_clips_legacy(self, project_data: Dict[str, Any], add_subtitles: bool) -> List:
        """
        Create video clips for each segment with subtitles if requested
        """
        clips = []
        
        for sentence in project_data["sentences"]:
            try:
                local_path = sentence["selected_footage"]["local_path"]
                if not local_path or not Path(local_path).exists():
                    logger.warning(f"Skipping segment with missing footage: {sentence['sentence_id']}")
                    continue
                    
                start_time = sentence["start"]
                end_time = sentence["end"]
                duration = end_time - start_time
                
                # Load the video clip
                video_clip = VideoFileClip(local_path).subclipped(0, duration)
                
                # Scale to full width while maintaining aspect ratio
                target_width = 1920  # Standard full HD width
                scale_factor = target_width / video_clip.w
                new_height = int(video_clip.h * scale_factor)
                
                # Resize the clip to target width, maintaining aspect ratio
                video_clip = video_clip.resized(width=target_width)
                
                # Create subtitle for this sentence if requested
                if add_subtitles and "text" in sentence and sentence["text"]:
                    try:
                        # Create a TextClip with the sentence text
                        # Try different fonts in order of preference
                        fonts_to_try = ["Arial", "Helvetica", "DejaVu-Sans", None]  # None uses default
                        txt_clip = None
                        
                        for font in fonts_to_try:
                            try:
                                txt_clip = TextClip(
                                    text=sentence["text"],
                                    font=font,
                                    font_size=40,
                                    color='white',
                                    stroke_color='black',
                                    stroke_width=2,
                                    size=(int(target_width * 0.9), None),
                                    method='caption',
                                    text_align='center'
                                )
                                break  # If successful, break out of loop
                            except Exception as font_error:
                                logger.debug(f"Font {font} failed: {font_error}")
                                continue
                        
                        if txt_clip is None:
                            logger.warning(f"All fonts failed for segment {sentence['sentence_id']}, skipping subtitles")
                            composed_clip = CompositeVideoClip([video_clip])
                        else:
                            # Set duration to match video clip
                            txt_clip = txt_clip.with_duration(duration)
                            
                            # Position the text higher on the screen
                            txt_clip = txt_clip.with_position(('center', 0.75), relative=True)
                            
                            # Composite the video and subtitle
                            composed_clip = CompositeVideoClip([video_clip, txt_clip])
                    except Exception as subtitle_error:
                        logger.warning(f"Subtitle creation failed for segment {sentence['sentence_id']}: {subtitle_error}")
                        composed_clip = CompositeVideoClip([video_clip])
                else:
                    # If no text or subtitles not requested, just use the video clip
                    composed_clip = CompositeVideoClip([video_clip])
                
                clips.append(composed_clip)
                logger.info(f"Created clip for segment {sentence['sentence_id']}, duration: {duration}s")
                
            except Exception as e:
                logger.error(f"Error creating clip for segment {sentence.get('sentence_id')}: {str(e)}")
        
        return clips

    def _add_audio(self, video_clip, voice_over_path, music_url, duration, render_segments):
        """
        Add audio tracks (voice-over and background music) to the video
        
        Args:
            video_clip: The video clip to add audio to
            voice_over_path: Path to the voice-over audio file
            music_url: URL or path to background music
            duration: Target duration of the final video
            render_segments: Original render segments with timing info
            
        Returns:
            Video clip with audio tracks added
        """
        try:
            audio_tracks = []
            
            # Add voice-over if available
            if voice_over_path and Path(voice_over_path).exists():
                logger.info(f"Adding voice-over audio from {voice_over_path}")
                voice_over = AudioFileClip(voice_over_path)
                
                # Fix synchronization issue by adjusting the start time
                # If voice-over is delayed by 2 seconds, we need to start it 2 seconds earlier
                voice_over = voice_over.with_start(-2.0)  # Start 2 seconds earlier to compensate for delay
                
                # Keep original volume for voice-over
                audio_tracks.append(voice_over)
            
            # Add background music if available
            if music_url:
                try:
                    # If it's a URL, download it first
                    if music_url.startswith('http'):
                        music_temp_path = self.temp_dir / f"bgm_{uuid.uuid4()}.mp3"
                        # Use synchronous download for simplicity
                        with httpx.Client() as client:
                            response = client.get(music_url, follow_redirects=True)
                            response.raise_for_status()
                            with open(music_temp_path, 'wb') as f:
                                f.write(response.content)
                        music_path = music_temp_path
                    else:
                        music_path = music_url
                    
                    if Path(music_path).exists():
                        logger.info(f"Adding background music from {music_path}")
                        background_music = AudioFileClip(music_path)
                        
                        # Loop music if it's shorter than the video
                        if background_music.duration < duration:
                            # Calculate how many times to loop
                            loops_needed = int(duration / background_music.duration) + 1
                            # Create a list of the music clip repeated
                            music_clips = [background_music] * loops_needed
                            # Concatenate the clips
                            background_music = concatenate_audioclips(music_clips)
                        
                        # Cut to match video duration - use proper method for AudioFileClip
                        if background_music.duration > duration:
                            # For AudioFileClip, we need to create a new clip with the right duration
                            background_music = background_music.with_duration(duration)
                        
                        # Lower the volume of background music (30% of original)
                        # AudioFileClip doesn't have volumex method
                        # Use direct multiplication which is supported for audio clips
                        background_music = background_music.with_effects(
                            [afx.MultiplyVolume(0.1), afx.AudioFadeOut(2.0)]
                        )
                        
                        audio_tracks.append(background_music)
                except Exception as music_error:
                    logger.error(f"Error adding background music: {str(music_error)}")
            
            # Add audio to the video clip if we have any audio tracks
            if audio_tracks:
                # Combine all audio tracks
                combined_audio = CompositeAudioClip(audio_tracks)
                # Set the audio of the video clip
                video_clip = video_clip.with_audio(combined_audio)
            
            return video_clip
            
        except Exception as e:
            logger.error(f"Error adding audio to video: {str(e)}")
            # Return original clip if there was an error
            return video_clip

    def _cleanup_render_files(self, project_data, project_temp_dir, video_clips):
        """
        Clean up temporary files after rendering is complete
        
        Args:
            project_data: Project data containing file paths
            project_temp_dir: Directory containing temporary files
            video_clips: List of video clips that may need cleanup
        """
        try:
            logger.info(f"Cleaning up temporary files in {project_temp_dir}")
            
            # Close any open video clips to release file handles
            if video_clips:
                for clip in video_clips:
                    try:
                        clip.close()
                    except Exception:
                        pass
            
            # Delete the temporary directory and all its contents
            # Only attempt if the directory exists
            if project_temp_dir and project_temp_dir.exists():
                # Use a safer approach - delete files first, then directory
                for file_path in project_temp_dir.glob("*"):
                    try:
                        if file_path.is_file():
                            file_path.unlink()
                    except Exception as file_error:
                        logger.warning(f"Failed to delete temporary file {file_path}: {str(file_error)}")
                
                try:
                    # Try to remove the directory after files are deleted
                    project_temp_dir.rmdir()
                    logger.info(f"Successfully removed temporary directory {project_temp_dir}")
                except Exception as dir_error:
                    logger.warning(f"Failed to remove temporary directory {project_temp_dir}: {str(dir_error)}")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    async def render_video(
        self,
        project_id: str = None,
        render_segments: List[Dict[str, Any]] = None,
        music_url: str = None,
        voice_over_path: str = None,
        add_subtitles: bool = True,
        include_audio: bool = True,
    ) -> str:
        """
        Render a video from segments with background music and voice-over
        
        Args:
            project_id: Unique identifier for the project
            render_segments: List of segments with timing and footage info
            music_url: URL or path to background music
            voice_over_path: Path to voice-over audio file
            add_subtitles: Whether to add subtitles to the video
            include_audio: Whether to include background music
            
        Returns:
            Path to the rendered video file
        """
        # If using the new API with project_data already set, use the new render method
        if self.project_data is not None:
            output_path = os.path.join(self.output_dir, f"{self.project_data['project_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
            return await self.render_video_new(output_path)
            
        # Otherwise, use the legacy render method
        render_task_id = f"render-{project_id}-{uuid.uuid4()}"
        project_temp_dir = self.temp_dir / render_task_id
        project_temp_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"Starting video rendering process for {project_id}")
        
        try:
            # Format the segments to match the expected structure
            project_data = self._format_project_data(project_id, render_segments)
            
            # Download footage files
            await self._download_footage_legacy(project_data, project_temp_dir)
            
            # Create video clips from footage with subtitles
            video_clips = self._create_clips_legacy(project_data, add_subtitles)
            if not video_clips:
                logger.error("No video clips created")
                return ""
            
            # Calculate total duration
            last_segment_end = max([segment.get("end_time", 0) for segment in render_segments])
            initial_duration = last_segment_end + 2.0  # Add 2 seconds fadeout
            
            # Create a composite clip with the initial duration
            final_clip = concatenate_videoclips(video_clips, method="compose")
            final_clip = final_clip.with_duration(initial_duration)
            
            logger.info(f"Initial video clip created with duration: {initial_duration}s")
            
            # Add audio tracks if requested (this may adjust the final duration)
            if include_audio:
                final_clip = self._add_audio(final_clip, voice_over_path, music_url, initial_duration, render_segments)
                logger.info(f"Final clip duration after audio processing: {final_clip.duration}s")
            
            # Generate output path and write video
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"{project_id}_{timestamp}.mp4"
            
            logger.info(f"Writing video to {output_path}")
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
            
            logger.info(f"Video export completed: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error rendering video: {str(e)}")
            return ""
            
        finally:
            self._cleanup_render_files(project_data, project_temp_dir, video_clips)
