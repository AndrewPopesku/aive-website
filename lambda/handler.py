"""
AWS Lambda handler for video rendering.
This function receives project data and renders videos using MoviePy.
"""
import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import boto3
import httpx

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import MoviePy components
try:
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
    MOVIEPY_AVAILABLE = False
    logger.error("MoviePy not available. Video rendering will fail.")


async def download_file(url: str, destination: Path) -> bool:
    """Download a file from URL to destination path."""
    try:
        logger.info(f"Downloading file from {url}")
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            # Add headers to avoid potential blocking
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "*/*",
            }
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            with open(destination, "wb") as f:
                f.write(response.content)
            
            file_size = destination.stat().st_size
            logger.info(f"Successfully downloaded {file_size} bytes to {destination}")
            return True
    except Exception as e:
        logger.error(f"Error downloading from {url}: {str(e)}")
        return False


async def download_footage(sentences: list[dict[str, Any]], temp_dir: Path) -> None:
    """Download all footage files for the sentences."""
    logger.info(f"Starting footage download for {len(sentences)} sentences")
    download_tasks = []
    sentence_to_task_index = {}  # Map sentence index to download task index
    
    for i, sentence in enumerate(sentences):
        logger.info(f"Processing sentence {i}: {sentence.get('text', '')[:50] if sentence.get('text') else 'NO TEXT'}...")
        selected_footage = sentence.get("selected_footage")
        logger.info(f"Sentence {i} selected_footage type: {type(selected_footage)}")
        logger.info(f"Sentence {i} selected_footage value: {selected_footage}")
        
        if not selected_footage:
            logger.error(f"Sentence {i} has no selected_footage object - this is required!")
            raise ValueError(f"Sentence {i} is missing selected_footage")
        
        if not isinstance(selected_footage, dict):
            logger.error(f"Sentence {i} selected_footage is not a dict! Type: {type(selected_footage)}")
            raise ValueError(f"Sentence {i} selected_footage must be a dictionary")
        
        footage_url = selected_footage.get("url")
        logger.info(f"Sentence {i} footage_url: {footage_url}")
        
        if not footage_url:
            logger.error(f"Sentence {i} has no footage URL in selected_footage")
            logger.error(f"Sentence {i} selected_footage keys: {list(selected_footage.keys())}")
            raise ValueError(f"Sentence {i} is missing footage URL in selected_footage")
        
        logger.info(f"Sentence {i}: URL = {footage_url[:100]}...")
        
        file_extension = ".mp4"
        if "." in footage_url.split("/")[-1]:
            file_extension = "." + footage_url.split(".")[-1].split("?")[0]
        
        filename = f"footage_{i}_{sentence.get('id', i)}{file_extension}"
        local_path = temp_dir / filename
        
        sentence["_local_footage_path"] = str(local_path)
        sentence["_sentence_index"] = i  # Store index for error reporting
        logger.info(f"Sentence {i}: Will download to {local_path}")
        
        if not local_path.exists():
            task_index = len(download_tasks)
            sentence_to_task_index[i] = task_index
            download_tasks.append(download_file(footage_url, local_path))
        else:
            logger.info(f"Sentence {i}: File already exists, skipping download")
    
    logger.info(f"Queued {len(download_tasks)} footage downloads")
    
    if not download_tasks:
        logger.info("All footage files already exist locally")
        return
    
    # Download all files
    results = await asyncio.gather(*download_tasks, return_exceptions=True)
    successful = sum(1 for r in results if r and not isinstance(r, Exception))
    failed = len(results) - successful
    logger.info(f"Download results: {successful} successful, {failed} failed")
    
    if failed > 0:
        logger.error(f"{failed} footage downloads failed out of {len(download_tasks)}")
        failed_sentences = []
        for sent_idx, task_idx in sentence_to_task_index.items():
            if not results[task_idx] or isinstance(results[task_idx], Exception):
                error = results[task_idx] if isinstance(results[task_idx], Exception) else "Unknown error"
                logger.error(f"Sentence {sent_idx} download failed: {error}")
                failed_sentences.append(sent_idx)
        
        if failed_sentences:
            raise RuntimeError(f"Failed to download footage for {len(failed_sentences)} sentences: {failed_sentences}")
    
    # Verify all expected files exist
    missing_files = []
    for i, sentence in enumerate(sentences):
        local_path = sentence.get("_local_footage_path")
        if local_path and not Path(local_path).exists():
            missing_files.append(i)
            logger.error(f"Sentence {i}: Expected file not found at {local_path}")
    
    if missing_files:
        raise RuntimeError(f"Expected footage files missing for sentences: {missing_files}")


def create_video_clips(sentences: list[dict[str, Any]]) -> list[Any]:
    """Create video clips with subtitles for each sentence."""
    logger.info(f"Creating video clips for {len(sentences)} sentences")
    clips = []
    errors = []
    
    for i, sentence in enumerate(sentences):
        local_footage_path = sentence.get("_local_footage_path")
        logger.info(f"Sentence {i}: Processing clip, local_path={local_footage_path}")
        
        if not local_footage_path:
            error_msg = f"Sentence {i}: No _local_footage_path set!"
            logger.error(error_msg)
            errors.append(error_msg)
            continue
            
        if not os.path.exists(local_footage_path):
            error_msg = f"Sentence {i}: File does not exist at {local_footage_path}"
            logger.error(error_msg)
            errors.append(error_msg)
            continue
        
        try:
            start_time = sentence.get("start_time", 0)
            end_time = sentence.get("end_time", start_time + 5)
            duration = end_time - start_time
            
            video_clip = VideoFileClip(local_footage_path)
            
            if video_clip.duration > duration:
                video_clip = video_clip.subclipped(0, duration)
            else:
                if duration > video_clip.duration * 2:
                    times_to_loop = int(duration / video_clip.duration) + 1
                    video_clip = concatenate_videoclips([video_clip] * times_to_loop).subclipped(0, duration)
                else:
                    video_clip = video_clip.with_duration(duration)
            
            # Resize to HD
            if video_clip.w != 1920 or video_clip.h != 1080:
                video_clip = video_clip.resized(newsize=(1920, 1080))
            
            # Add subtitle
            text = sentence.get("text", "").strip()
            if text:
                try:
                    subtitle = TextClip(
                        text=text,
                        font_size=50,
                        color="white",
                        font="Arial",
                        stroke_color="black",
                        stroke_width=2,
                        size=(1800, None),
                        method="caption",
                    ).with_duration(duration)
                    
                    subtitle = subtitle.with_position(("center", "bottom"))
                    video_clip = CompositeVideoClip([video_clip, subtitle])
                except Exception as e:
                    logger.warning(f"Could not add subtitle '{text}': {str(e)}")
            
            clips.append(video_clip)
            logger.info(f"Sentence {i}: Clip created successfully")
        
        except Exception as e:
            error_msg = f"Sentence {i}: Error creating clip: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            continue
    
    logger.info(f"Created {len(clips)} video clips out of {len(sentences)} sentences")
    
    if errors:
        logger.warning(f"Encountered {len(errors)} errors during clip creation:")
        for error in errors:
            logger.warning(f"  - {error}")
    
    if not clips:
        error_summary = "\n".join(errors) if errors else "Unknown reason"
        raise ValueError(f"Failed to create any video clips. Errors:\n{error_summary}")
    
    return clips


async def render_video(
    project_data: dict[str, Any],
    audio_url: str,
    music_url: str | None,
    temp_dir: Path,
    output_path: Path,
) -> str:
    """Render the complete video."""
    if not MOVIEPY_AVAILABLE:
        raise RuntimeError("MoviePy is not available")
    
    try:
        # Download audio file
        logger.info("Downloading audio file...")
        audio_path = temp_dir / "audio.mp3"
        await download_file(audio_url, audio_path)
        
        if not audio_path.exists():
            raise ValueError("Failed to download audio file")
        
        # Download footage
        logger.info("Downloading footage files...")
        await download_footage(project_data["sentences"], temp_dir)
        
        # Create video clips
        logger.info("Creating video clips...")
        video_clips = create_video_clips(project_data["sentences"])
        
        if not video_clips:
            raise ValueError("No video clips were created")
        
        # Combine clips
        logger.info("Combining video clips...")
        final_video = concatenate_videoclips(video_clips, method="compose")
        
        # Add voice-over
        logger.info("Adding voice-over audio...")
        voice_audio = AudioFileClip(str(audio_path))
        final_video = final_video.with_audio(voice_audio)
        
        # Add background music
        if music_url:
            logger.info("Adding background music...")
            music_path = temp_dir / "music.mp3"
            await download_file(music_url, music_path)
            
            if music_path.exists():
                music_audio = AudioFileClip(str(music_path))
                # Adjust music volume to 30% using MoviePy 2.0 API
                music_audio_scaled = music_audio.with_volume_scaled(0.3)
                
                if music_audio_scaled and music_audio_scaled.duration < final_video.duration:
                    times_to_loop = int(final_video.duration / music_audio_scaled.duration) + 1
                    music_audio = concatenate_audioclips([music_audio_scaled] * times_to_loop).subclipped(0, final_video.duration)
                elif music_audio_scaled:
                    music_audio = music_audio_scaled.subclipped(0, final_video.duration)
                else:
                    logger.warning("Failed to scale music volume, using original")
                    music_audio = music_audio
                
                if final_video.audio:
                    composite_audio = CompositeAudioClip([final_video.audio, music_audio])
                    final_video = final_video.with_audio(composite_audio)
                else:
                    final_video = final_video.with_audio(music_audio)
        
        # Export video
        logger.info(f"Exporting final video to {output_path}...")
        final_video.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(temp_dir / "temp-audio.m4a"),
            remove_temp=True,
        )
        
        final_video.close()
        logger.info("Video rendering completed")
        return str(output_path)
    
    except Exception as e:
        logger.error(f"Error rendering video: {str(e)}")
        raise



async def upload_to_s3(file_path: str, bucket: str, key: str) -> str:
    """Upload rendered video to S3 and return presigned URL."""
    try:
        s3_client = boto3.client("s3")
        logger.info(f"Uploading {file_path} to s3://{bucket}/{key}")
        
        # Upload file to S3
        s3_client.upload_file(file_path, bucket, key)
        logger.info(f"Upload complete: s3://{bucket}/{key}")
        
        # Generate presigned URL valid for 7 days
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=604800  # 7 days in seconds
        )
        
        logger.info(f"Generated presigned URL (valid for 7 days)")
        return presigned_url
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        raise


def lambda_handler(event, context):
    """Lambda handler function."""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Parse input
        body = json.loads(event.get("body", "{}")) if isinstance(event.get("body"), str) else event.get("body", {})
        
        project_data = body.get("project_data")
        audio_url = body.get("audio_url")
        music_url = body.get("music_url")
        project_id = project_data.get("id")
        s3_bucket = os.environ.get("S3_BUCKET")
        
        if not project_data or not audio_url:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required parameters"})
            }
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            output_path = temp_dir / f"{project_id}_final_video.mp4"
            
            # Render video
            loop = asyncio.get_event_loop()
            video_path = loop.run_until_complete(
                render_video(project_data, audio_url, music_url, temp_dir, output_path)
            )
            
            # Upload to S3
            s3_key = f"videos/{project_id}/{Path(video_path).name}"
            video_url = loop.run_until_complete(
                upload_to_s3(video_path, s3_bucket, s3_key)
            )
            
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "video_url": video_url,
                    "s3_key": s3_key,
                    "message": "Video rendered successfully"
                })
            }
    
    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
