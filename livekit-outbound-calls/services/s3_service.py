import boto3
import logging
from botocore.exceptions import ClientError
from urllib.parse import urlparse
from config import config

logger = logging.getLogger("s3_service")

class S3Service:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None and config.AWS_ACCESS_KEY_ID and config.AWS_SECRET_ACCESS_KEY:
            try:
                cls._client = boto3.client(
                    's3',
                    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                    region_name=config.AWS_REGION
                )
            except Exception as e:
                logger.error(f"Failed to create S3 client: {e}")
        return cls._client

    @classmethod
    def generate_presigned_url(cls, s3_uri: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for an S3 object.
        
        Args:
            s3_uri: S3 URI (s3://bucket/key)
            expiration: Expiration in seconds (default 1 hour)
            
        Returns:
            Presigned URL string, or original URI if generation fails
        """
        if not s3_uri or not s3_uri.startswith("s3://"):
            return s3_uri

        client = cls.get_client()
        if not client:
            return s3_uri

        try:
            parsed = urlparse(s3_uri)
            bucket = parsed.netloc
            key = parsed.path.lstrip('/')

            url = client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return s3_uri
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL: {e}")
            return s3_uri
