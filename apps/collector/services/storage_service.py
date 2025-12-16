"""Storage service for raw assets."""
import boto3
import json
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


def save_raw_asset(
    data: dict,
    dataset_step_id: str,
    connector_name: str,
    file_format: str = "json"
) -> str:
    """
    Save raw asset to S3-compatible storage.
    
    Args:
        data: Data to save (will be serialized)
        dataset_step_id: Dataset step ID
        connector_name: Connector name
        file_format: File format (json, csv, etc.)
    
    Returns:
        S3 key (path) of saved file
    """
    # Generate S3 key
    s3_key = f"raw_assets/{dataset_step_id}/{connector_name}.{file_format}"
    
    try:
        # Serialize data
        if file_format == "json":
            content = json.dumps(data, indent=2).encode('utf-8')
            content_type = "application/json"
        else:
            content = str(data).encode('utf-8')
            content_type = "application/octet-stream"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=settings.s3_bucket,
            Key=s3_key,
            Body=content,
            ContentType=content_type
        )
        
        logger.info(f"Saved raw asset to {s3_key}")
        return s3_key
    
    except Exception as e:
        logger.error(f"Error saving raw asset: {e}", exc_info=True)
        raise


def get_raw_asset(s3_key: str) -> dict:
    """
    Retrieve raw asset from storage.
    
    Args:
        s3_key: S3 key (path) of file
    
    Returns:
        Deserialized data
    """
    try:
        response = s3_client.get_object(
            Bucket=settings.s3_bucket,
            Key=s3_key
        )
        
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    
    except Exception as e:
        logger.error(f"Error retrieving raw asset: {e}", exc_info=True)
        raise

