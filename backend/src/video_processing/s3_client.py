"""
S3 client for uploading files and generating presigned URLs.
"""
import logging
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError

from base.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class S3Client:
    """Client for S3 operations."""
    
    def __init__(self) -> None:
        """Initialize S3 client."""
        self.s3_client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self.bucket_name = settings.s3_bucket
    
    async def upload_file(
        self,
        file_path: str | Path,
        s3_key: str | None = None,
    ) -> str:
        """
        Upload a file to S3.
        
        Args:
            file_path: Local path to the file to upload
            s3_key: Optional S3 key (path in bucket). If not provided, uses filename
        
        Returns:
            S3 key of the uploaded file
        
        Raises:
            RuntimeError: If upload fails
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise RuntimeError(f"File not found: {file_path}")
        
        # Use filename as S3 key if not provided
        if s3_key is None:
            s3_key = file_path.name
        
        try:
            logger.info(f"Uploading {file_path} to S3 bucket {self.bucket_name}/{s3_key}")
            
            self.s3_client.upload_file(
                str(file_path),
                self.bucket_name,
                s3_key,
            )
            
            logger.info(f"Successfully uploaded to S3: {s3_key}")
            return s3_key
        
        except ClientError as e:
            error_msg = f"Failed to upload file to S3: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Error uploading file to S3: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def generate_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600,
    ) -> str:
        """
        Generate a presigned URL for accessing an S3 object.
        
        Args:
            s3_key: S3 key (path in bucket)
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Presigned URL
        
        Raises:
            RuntimeError: If URL generation fails
        """
        try:
            logger.info(f"Generating presigned URL for {self.bucket_name}/{s3_key}")
            
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": s3_key,
                },
                ExpiresIn=expiration,
            )
            
            logger.info(f"Generated presigned URL: {url[:100]}...")
            return url
        
        except ClientError as e:
            error_msg = f"Failed to generate presigned URL: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Error generating presigned URL: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    async def upload_and_get_url(
        self,
        file_path: str | Path,
        s3_key: str | None = None,
        expiration: int = 3600,
    ) -> tuple[str, str]:
        """
        Upload a file to S3 and generate a presigned URL.
        
        Args:
            file_path: Local path to the file to upload
            s3_key: Optional S3 key (path in bucket)
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Tuple of (s3_key, presigned_url)
        
        Raises:
            RuntimeError: If upload or URL generation fails
        """
        s3_key = await self.upload_file(file_path, s3_key)
        presigned_url = self.generate_presigned_url(s3_key, expiration)
        return s3_key, presigned_url


async def upload_file_to_s3(
    file_path: str | Path,
    s3_key: str | None = None,
) -> str:
    """
    Convenience function to upload a file to S3.
    
    Args:
        file_path: Local path to the file to upload
        s3_key: Optional S3 key (path in bucket)
    
    Returns:
        S3 key of the uploaded file
    """
    client = S3Client()
    return await client.upload_file(file_path, s3_key)


async def get_presigned_url_for_file(
    file_path: str | Path,
    s3_key: str | None = None,
    expiration: int = 3600,
) -> tuple[str, str]:
    """
    Upload a file to S3 and get a presigned URL.
    
    Args:
        file_path: Local path to the file to upload
        s3_key: Optional S3 key (path in bucket)
        expiration: URL expiration time in seconds (default: 1 hour)
    
    Returns:
        Tuple of (s3_key, presigned_url)
    """
    client = S3Client()
    return await client.upload_and_get_url(file_path, s3_key, expiration)
