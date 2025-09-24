import os
import httpx
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Callable
import logging
from datetime import datetime
import uuid

# MoviePy imports
from moviepy import (
    VideoFileClip, 
    AudioFileClip, 
    TextClip,
    CompositeVideoClip, 
    CompositeAudioClip,
    concatenate_videoclips,
    concatenate_audioclips
)

from app.config import (
    GROQ_API_KEY, PEXELS_API_KEY, PIXABAY_API_KEY,
    GROQ_API_URL, PEXELS_API_URL, PIXABAY_API_URL,
    TEMP_DIR, OUTPUT_DIR, AUDIO_DIR,
    DEFAULT_SOURCE_LANGUAGE, TARGET_LANGUAGE
)
from app.schemas import Sentence, MusicRecommendation
from app.video_editor import VideoEditor

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

async def transcribe_audio(audio_path: str) -> List[Sentence]:
    """
    Transcribe audio file using Groq API (Whisper model) and return sentences with timestamps.
    Also translates each sentence to English for better search results.
    """
    try:
        # Set up Groq API request
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }
        
        # For file uploads, we need to use multipart/form-data
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
                    f"{GROQ_API_URL}/audio/transcriptions",
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
                        start=segment["start"],
                        end=segment["end"]
                    )
                    sentences.append(sentence)
                    # Create translation tasks for each sentence
                    translation_tasks.append(translate_text(segment["text"]))
                
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

async def find_footage_for_sentence(text: str, translated_text: str = None) -> str:
    """
    Find relevant video footage for a sentence using Pexels API.
    Uses translated_text for search if provided, otherwise translates on-demand.
    """
    try:
        # Use provided translation or translate on-demand
        if not translated_text:
            translated_text = await translate_text(text)
        
        # Extract keywords from the translated sentence
        keywords = translated_text.lower().split()
        # Filter out common words
        common_words = {"the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "in", "on", "at", "to", "for"}
        keywords = [word for word in keywords if word not in common_words]
        
        # Use the first few keywords for the search
        search_query = " ".join(keywords[:3]) if keywords else "general"
        
        logger.info(f"Searching footage with query: '{search_query}' (translated from: '{text}')")
        
        headers = {"Authorization": PEXELS_API_KEY}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PEXELS_API_URL}/search?query={search_query}&per_page=1&orientation=landscape",
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

async def find_background_music(sentence_texts: List[str] = None) -> List[MusicRecommendation]:
    """
    Find background music from the local audio directory.
    Optionally accepts sentence_texts to analyze for mood-appropriate music.
    """
    try:
        # Get all available music files from the AUDIO_DIR
        music_files = list(AUDIO_DIR.glob("*.mp3"))
        
        if not music_files:
            logger.warning("No music files found in audio directory")
            return []
        
        # Create music recommendations from available files
        music_recommendations = []
        for i, music_file in enumerate(music_files):
            music_id = f"music-{i+1}"
            name = music_file.stem  # Use filename without extension as the name
            
            # Create full file path
            file_path = str(music_file)
            
            music_recommendations.append(
                MusicRecommendation(
                    id=music_id,
                    name=name,
                    url=file_path
                )
            )
            
            logger.info(f"Added music file: {name} at {file_path}")
        
        return music_recommendations
    except Exception as e:
        logger.error(f"Error finding background music: {str(e)}")
        return []

async def translate_text(text: str) -> str:
    """
    Translate text to English using Groq API (LLM model) for better search results.
    """
    try:
        if not text.strip():
            return text
            
        # Set up Groq API request
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Prepare the prompt for translation
        prompt = f"Translate the following text to English. Only respond with the translation, nothing else:\n\n{text}"
        
        data = {
            "model": "llama-3.3-70b-versatile",  # Using a smaller model for translation is sufficient
            "messages": [
                {"role": "system", "content": "You are a professional translator. Translate the given text to English accurately."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,  # Low temperature for more deterministic results
            "max_tokens": 1024
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GROQ_API_URL}/chat/completions",
                headers=headers,
                json=data,
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error(f"Groq API translation error: {response.text}")
                return text  # Return original text on error
            
            result = response.json()
            translation = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
            if not translation:
                logger.warning(f"Empty translation result for: {text}")
                return text
                
            logger.info(f"Successfully translated text: '{text[:30]}...' → '{translation[:30]}...'")
            return translation
                
    except Exception as e:
        logger.error(f"Error translating text: {str(e)}")
        return text  # Return original text on error

async def render_final_video(
    project_id: str, 
    render_segments: List[Dict[str, Any]], 
    music_url: str, 
    add_subtitles: bool = True,
    include_audio: bool = True,
    progress_callback: Optional[Callable[[int], None]] = None
) -> str:
    """
    Render the final video using MoviePy.
    Returns the output file path
    """
    render_task_id = f"render-{project_id}-{uuid.uuid4()}"
    project_temp_dir = TEMP_DIR / render_task_id
    footage_paths = {}
    video_clips = []
    
    try:
        logger.info(f"[{render_task_id}] Starting video rendering process")
        logger.info(f"[{render_task_id}] Project details: {project_id}, {len(render_segments)} segments")
        logger.info(f"[{render_task_id}] Render settings: add_subtitles={add_subtitles}, include_audio={include_audio}")
        
        # Create temp directory for project
        project_temp_dir.mkdir(exist_ok=True, parents=True)  # Ensure parent directories exist too
        logger.info(f"[{render_task_id}] Created temp directory: {project_temp_dir}")
        
        # Download all footage files
        for i, segment in enumerate(render_segments):
            footage_url = segment.get("footage_url")
            if not footage_url:
                logger.warning(f"[{render_task_id}] No footage URL for segment {i}, skipping")
                continue
                
            try:
                footage_path = project_temp_dir / f"segment_{i}.mp4"
                await download_file(footage_url, footage_path)
                footage_paths[i] = footage_path
            except Exception as e:
                logger.error(f"[{render_task_id}] Failed to download footage for segment {i}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                # Continue with other footage files
        
        logger.info(f"[{render_task_id}] Downloaded {len(footage_paths)} footage files")
        
        # If we still don't have any footage paths after all our attempts, we can't proceed
        if not footage_paths:
            logger.error(f"[{render_task_id}] No footage files were successfully downloaded")
            return ""
        
        # Create clips for each sentence
        logger.info(f"[{render_task_id}] Starting to create video clips for each sentence")
        for i, segment in enumerate(render_segments):
            try:
                # Extract text and timing information from segment
                text = segment.get("text")
                start_time = segment.get("start_time")
                end_time = segment.get("end_time")
                footage_url = segment.get("footage_url")
                
                if None in (start_time, end_time):
                    logger.warning(f"[{render_task_id}] Segment {i} is missing time info, skipping")
                    continue
                
                duration = end_time - start_time
                
                logger.info(f"[{render_task_id}] Processing segment {i+1}/{len(render_segments)}, duration {duration:.2f}s")
                
                # Get footage file path by index
                if i in footage_paths:
                    try:
                        # Create video clip from the downloaded file
                        video_path = footage_paths[i]
                        logger.info(f"[{render_task_id}] Creating video clip from {video_path}")
                        video_clip = VideoFileClip(str(video_path))
                        
                        # Make sure the clip is long enough, otherwise loop it
                        if video_clip.duration < duration:
                            logger.warning(f"[{render_task_id}] Video clip too short ({video_clip.duration}s < {duration}s), will loop it")
                            video_clip = video_clip.loop(duration=duration)
                        else:
                            # Just use the required duration
                            video_clip = video_clip.subclipped(0, duration)
                        
                        # Resize all videos to a standard 1920x1080 resolution
                        target_size = (1920, 1080)
                        video_clip = video_clip.resized(target_size)
                        
                        logger.info(f"[{render_task_id}] Created video clip: {video_clip.size}, {video_clip.duration}s")
                        
                        # Add subtitles if requested
                        if add_subtitles and text:
                            logger.info(f"[{render_task_id}] Adding subtitles to clip: {text[:30]}...")
                            try:
                                # Skip subtitles for now due to compatibility issues
                                logger.info(f"[{render_task_id}] Skipping subtitles due to compatibility issues")
                                # Keeping the original video clip as is
                            except Exception as e:
                                logger.error(f"[{render_task_id}] Error adding subtitles: {str(e)}")
                                # Continue without subtitles
                        
                        logger.info(f"[{render_task_id}] Adding clip to sequence")
                        video_clips.append(video_clip)
                    except Exception as e:
                        logger.error(f"[{render_task_id}] Error creating clip for segment {i}: {str(e)}")
                        import traceback
                        logger.error(traceback.format_exc())
                else:
                    logger.warning(f"[{render_task_id}] No footage found for segment {i}")
            except Exception as e:
                logger.error(f"[{render_task_id}] Unexpected error processing segment {i}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
        if not video_clips:
            logger.error(f"[{render_task_id}] No video clips created, aborting")
            return ""
        
        # Concatenate all clips
        logger.info(f"[{render_task_id}] Concatenating {len(video_clips)} clips")
        final_clip = concatenate_videoclips(video_clips)
        logger.info(f"[{render_task_id}] Final clip created: {final_clip.size}, {final_clip.duration}s")
        
        # Add audio track
        if music_url and include_audio:
            try:
                logger.info(f"[{render_task_id}] Adding audio track from {music_url}")
                audio_clip = AudioFileClip(music_url)
                
                # Create voiceover markers for ducking
                # Assuming render_segments has start_time and end_time in seconds
                ducking_points = []
                for segment in render_segments:
                    start_time = segment.get("start_time", 0)
                    end_time = segment.get("end_time", 0)
                    if None not in (start_time, end_time):
                        ducking_points.append((start_time, end_time))
                
                # Sort and merge overlapping ducking points
                ducking_points.sort()
                merged_points = []
                if ducking_points:
                    current_start, current_end = ducking_points[0]
                    for start, end in ducking_points[1:]:
                        if start <= current_end:
                            # Overlapping segments, merge them
                            current_end = max(current_end, end)
                        else:
                            # Non-overlapping, add the previous segment and start a new one
                            merged_points.append((current_start, current_end))
                            current_start, current_end = start, end
                    merged_points.append((current_start, current_end))
                
                logger.info(f"[{render_task_id}] Found {len(merged_points)} voiceover segments for audio ducking")
                
                # Function to apply audio ducking
                def volume_adjust(t):
                    # Default volume level for background music (when no voiceover)
                    default_volume = 0.7
                    # Reduced volume during voiceover
                    ducked_volume = 0.2
                    # Fade duration (seconds)
                    fade_duration = 0.3
                    
                    # Find if we're in a voiceover segment
                    for start, end in merged_points:
                        # If time is within a voiceover segment, reduce volume
                        if start - fade_duration <= t <= end + fade_duration:
                            # Apply fade in/out at segment boundaries
                            if t < start:
                                # Fading in to ducked volume
                                ratio = (start - t) / fade_duration
                                return default_volume - (default_volume - ducked_volume) * (1 - ratio)
                            elif t > end:
                                # Fading out from ducked volume
                                ratio = (t - end) / fade_duration
                                return ducked_volume + (default_volume - ducked_volume) * ratio
                            else:
                                # Within voiceover, use ducked volume
                                return ducked_volume
                    
                    # If outside any segment, use the default volume
                    return default_volume
                
                # Calculate the final usable duration
                last_voiceover_end = 0
                if merged_points:
                    # Get the end time of the last voiceover segment
                    last_voiceover_end = merged_points[-1][1]
                
                # Cut the audio clip to end shortly after the last voiceover
                fade_out_duration = 2.0  # 2 seconds fade out after last voiceover
                if last_voiceover_end > 0:
                    end_time = last_voiceover_end + fade_out_duration
                    
                    # Make sure end_time doesn't exceed the total video duration
                    if end_time > final_clip.duration:
                        end_time = final_clip.duration
                    
                    # For audio clip trimming, we need to create a mask or manually handle duration
                    # Instead of trying to cut the audio clip directly, we'll add it to the video
                    # and let the video duration control the audio length
                    
                    # Add fade out at the end part of the audio
                    try:
                        # Use fadeout() instead of audio_fadeout() for AudioFileClip
                        audio_clip = audio_clip.fadeout(min(fade_out_duration, audio_clip.duration))
                        logger.info(f"[{render_task_id}] Added audio fadeout effect")
                    except Exception as e:
                        logger.warning(f"[{render_task_id}] Could not add audio fadeout: {str(e)}")
                
                # Apply volume adjustment to the audio clip
                try:
                    # Function to create dynamic volume adjustment
                    def adjust_volume(get_frame, t):
                        # Get the original audio frame
                        frame = get_frame(t)
                        # Determine volume level at this time
                        vol = volume_adjust(t)
                        # Apply volume factor to the frame
                        return vol * frame
                    
                    # Apply custom frame transform to implement ducking
                    audio_clip = audio_clip.fl(adjust_volume)
                    logger.info(f"[{render_task_id}] Applied audio ducking to background music")
                except Exception as e:
                    logger.warning(f"[{render_task_id}] Could not apply volume adjustment: {str(e)}")
                
                # Apply the adjusted audio to the final clip
                final_clip = final_clip.with_audio(audio_clip)
                logger.info(f"[{render_task_id}] Audio track added with ducking")
                
                # If we need to trim the video/audio, set the end time of the final clip
                if last_voiceover_end > 0:
                    # This will automatically trim both video and audio
                    final_clip = final_clip.subclip(0, end_time)
                    logger.info(f"[{render_task_id}] Trimmed final clip to end {fade_out_duration}s after last voiceover")
            except Exception as e:
                logger.error(f"[{render_task_id}] Error adding audio: {str(e)}")
                logger.info(f"[{render_task_id}] Continuing without audio due to error")
                # Continue without audio
        else:
            logger.info(f"[{render_task_id}] No audio track added (music_url: {music_url}, include_audio: {include_audio})")
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / f"{project_id}_{timestamp}.mp4"
        logger.info(f"[{render_task_id}] Writing final video to {output_path}")
        
        # Write the final video
        logger.info(f"[{render_task_id}] Starting video export process with MoviePy")
        
        try:
            final_clip.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=str(project_temp_dir / "temp_audio.m4a"),
                remove_temp=True,
                threads=4,
                fps=24,
                logger=None  # Set to None to reduce console spam
            )
            
            # Check timeout after the fact
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise TimeoutError("Video rendering timed out or produced an empty file")
                
        except TimeoutError:
            logger.error(f"[{render_task_id}] Video rendering timed out")
            return ""
        except Exception as e:
            logger.error(f"[{render_task_id}] Error during video export: {str(e)}")
            return ""
        
        logger.info(f"[{render_task_id}] Video export completed: {output_path}")
        return str(output_path)
        
    except Exception as e:
        logger.error(f"[{render_task_id}] Error rendering video: {str(e)}")
        return ""
        
    finally:
        # Clean up temp files
        try:
            logger.info(f"[{render_task_id}] Cleaning up temporary files")
            # Close all video clips to release file handles
            for clip in video_clips:
                try:
                    logger.info(f"[{render_task_id}] Closing video clip")
                    clip.close()
                except Exception as e:
                    logger.warning(f"[{render_task_id}] Error closing clip: {str(e)}")
                
            # Remove all downloaded files
            for path in footage_paths.values():
                try:
                    if path.exists():
                        logger.info(f"[{render_task_id}] Removing file: {path}")
                        path.unlink()
                except Exception as e:
                    logger.warning(f"[{render_task_id}] Error removing file {path}: {str(e)}")
            
            # Remove the temp directory
            if project_temp_dir.exists():
                try:
                    logger.info(f"[{render_task_id}] Removing temp directory: {project_temp_dir}")
                    project_temp_dir.rmdir()
                except Exception as e:
                    logger.warning(f"[{render_task_id}] Error removing temp directory: {str(e)}")
        except Exception as e:
            logger.error(f"[{render_task_id}] Error cleaning up render files: {str(e)}")
        logger.info(f"[{render_task_id}] Rendering process completed") 