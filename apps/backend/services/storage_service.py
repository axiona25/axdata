"""Storage service for S3-compatible storage."""
import boto3
import logging
from typing import Optional
from botocore.config import Config
from core.config import settings

logger = logging.getLogger(__name__)

# Initialize S3 client
s3_client = boto3.client(
    's3',
    endpoint_url=settings.s3_endpoint_url,
    aws_access_key_id=settings.s3_access_key_id,
    aws_secret_access_key=settings.s3_secret_access_key,
    region_name=settings.s3_region,
    config=Config(signature_version='s3v4')
)


def save_to_storage(
    data: bytes,
    s3_key: str,
    content_type: str = "application/octet-stream"
) -> str:
    """
    Save data to S3-compatible storage.
    
    Args:
        data: Data to save (bytes)
        s3_key: S3 key (path)
        content_type: Content type
    
    Returns:
        S3 key
    """
    try:
        s3_client.put_object(
            Bucket=settings.s3_bucket,
            Key=s3_key,
            Body=data,
            ContentType=content_type
        )
        
        logger.info(f"Saved to {s3_key}")
        return s3_key
    
    except Exception as e:
        logger.error(f"Error saving to storage: {e}", exc_info=True)
        raise


def save_bundle_to_storage(
    bundle_data: bytes,
    dataset_id: str,
    bucket: str,
    s3_client_instance
) -> str:
    """
    Save bundle to S3-compatible storage.
    
    Args:
        bundle_data: ZIP bundle data
        dataset_id: Dataset ID
        bucket: S3 bucket name
        s3_client_instance: Boto3 S3 client instance
    
    Returns:
        S3 key (path) of saved bundle
    """
    s3_key = f"datasets/{dataset_id}/bundle.zip"
    
    s3_client_instance.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=bundle_data,
        ContentType="application/zip"
    )
    
    logger.info(f"Saved bundle to {s3_key}")
    return s3_key


def generate_signed_url(
    s3_key: str,
    expiration: int = 3600
) -> str:
    """
    Generate signed URL for download.
    
    Args:
        s3_key: S3 key (path)
        expiration: Expiration time in seconds
    
    Returns:
        Signed URL
    """
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.s3_bucket,
                'Key': s3_key
            },
            ExpiresIn=expiration
        )
        
        return url
    
    except Exception as e:
        logger.error(f"Error generating signed URL: {e}", exc_info=True)
        raise

