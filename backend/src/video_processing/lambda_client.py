"""
Lambda client for invoking video rendering function.
"""
import json
import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

from base.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LambdaVideoRenderer:
    """Client for invoking Lambda video rendering function."""
    
    def __init__(self) -> None:
        """Initialize Lambda client."""
        from botocore.config import Config
        
        # Configure with longer timeouts for video rendering (up to 15 minutes)
        config = Config(
            read_timeout=900,  # 15 minutes (Lambda max execution time)
            connect_timeout=10,
            retries={'max_attempts': 0}  # No retries for long-running operations
        )
        
        self.lambda_client = boto3.client(
            "lambda",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            config=config,
        )
        self.function_name = settings.lambda_function_name
    
    async def invoke_render(
        self,
        project_data: dict[str, Any],
        audio_url: str,
        music_url: str | None = None,
    ) -> dict[str, Any]:
        """
        Invoke Lambda function to render video.
        
        Args:
            project_data: Project data including sentences and footage
            audio_url: URL to the audio file (must be publicly accessible)
            music_url: Optional URL to background music
        
        Returns:
            dict with video_url, s3_key, and message
        
        Raises:
            RuntimeError: If Lambda invocation fails
        """
        payload = {
            "body": json.dumps({
                "project_data": project_data,
                "audio_url": audio_url,
                "music_url": music_url,
            })
        }
        
        try:
            logger.info(f"Invoking Lambda function: {self.function_name}")
            # Debug: Log the sentences and their selected_footage structure
            if "sentences" in project_data:
                logger.info(f"Number of sentences: {len(project_data['sentences'])}")
                for i, sentence in enumerate(project_data['sentences'][:3]):
                    selected_footage = sentence.get('selected_footage')
                    logger.info(f"Sentence {i} selected_footage type: {type(selected_footage)}")
                    logger.info(f"Sentence {i} selected_footage: {selected_footage}")
                    if selected_footage:
                        logger.info(f"Sentence {i} footage URL: {selected_footage.get('url') if isinstance(selected_footage, dict) else 'NOT A DICT'}")
            
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType="RequestResponse",  # Synchronous invocation
                Payload=json.dumps(payload),
            )
            
            # Parse response
            response_payload = json.loads(response["Payload"].read())
            status_code = response_payload.get("statusCode", 500)
            
            if status_code == 200:
                body = json.loads(response_payload.get("body", "{}"))
                logger.info(f"Video rendering successful: {body.get('video_url')}")
                return body
            else:
                error_body = json.loads(response_payload.get("body", "{}"))
                error_msg = error_body.get("error", "Unknown error")
                logger.error(f"Lambda invocation failed with status {status_code}: {error_msg}")
                raise RuntimeError(f"Lambda function returned error: {error_msg}")
        
        except ClientError as e:
            error_msg = f"AWS client error: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Error invoking Lambda: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    async def invoke_render_async(
        self,
        project_data: dict[str, Any],
        audio_url: str,
        music_url: str | None = None,
    ) -> str:
        """
        Invoke Lambda function asynchronously (fire and forget).
        
        Args:
            project_data: Project data including sentences and footage
            audio_url: URL to the audio file
            music_url: Optional URL to background music
        
        Returns:
            Request ID of the Lambda invocation
        
        Raises:
            RuntimeError: If Lambda invocation fails
        """
        payload = {
            "body": json.dumps({
                "project_data": project_data,
                "audio_url": audio_url,
                "music_url": music_url,
            })
        }
        
        try:
            logger.info(f"Invoking Lambda function asynchronously: {self.function_name}")
            
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType="Event",  # Asynchronous invocation
                Payload=json.dumps(payload),
            )
            
            request_id = response.get("ResponseMetadata", {}).get("RequestId", "unknown")
            logger.info(f"Lambda invoked asynchronously with request ID: {request_id}")
            return request_id
        
        except ClientError as e:
            error_msg = f"AWS client error: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Error invoking Lambda: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e


async def render_video_via_lambda(
    project_data: dict[str, Any],
    audio_url: str,
    music_url: str | None = None,
) -> dict[str, Any]:
    """
    Convenience function to render video via Lambda.
    
    Args:
        project_data: Project data including sentences and footage
        audio_url: URL to the audio file
        music_url: Optional URL to background music
    
    Returns:
        dict with video_url, s3_key, and message
    """
    renderer = LambdaVideoRenderer()
    return await renderer.invoke_render(project_data, audio_url, music_url)
