from abc import ABC, abstractmethod
from datetime import timedelta
from io import BytesIO
from typing import BinaryIO, TYPE_CHECKING
import uuid

from minio import Minio
import httpx

from src.config import settings
from src.logging_config import get_logger

if TYPE_CHECKING:
    from supabase import Client

logger = get_logger(__name__)


class StorageService(ABC):
    @abstractmethod
    async def upload_file(
        self, file: BinaryIO, bucket: str, object_name: str, content_type: str = "application/octet-stream"
    ) -> str:
        pass

    @abstractmethod
    async def get_presigned_url(self, bucket: str, object_name: str, expiry: int = 3600) -> str:
        pass

    @abstractmethod
    async def delete_file(self, bucket: str, object_name: str) -> None:
        pass


class SupabaseStorageService(StorageService):
    def __init__(self):
        try:
            from supabase import create_client
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        except ImportError:
            raise ImportError("supabase-py is required for Supabase mode. Install it with: pip install supabase")

    async def upload_file(
        self, file: BinaryIO, bucket: str, object_name: str, content_type: str = "application/octet-stream"
    ) -> str:
        try:
            file_bytes = file.read()
            result = self.client.storage.from_(bucket).upload(
                object_name,
                file_bytes,
                {"content-type": content_type}
            )
            logger.info("File uploaded to Supabase", bucket=bucket, object_name=object_name)
            return object_name
        except Exception as e:
            logger.error("Failed to upload to Supabase", error=str(e))
            raise

    async def get_presigned_url(self, bucket: str, object_name: str, expiry: int = 3600) -> str:
        try:
            url = self.client.storage.from_(bucket).create_signed_url(object_name, expiry)
            return url['signedURL']
        except Exception as e:
            logger.error("Failed to generate signed URL", error=str(e))
            raise

    async def delete_file(self, bucket: str, object_name: str) -> None:
        try:
            self.client.storage.from_(bucket).remove([object_name])
            logger.info("File deleted from Supabase", bucket=bucket, object_name=object_name)
        except Exception as e:
            logger.error("Failed to delete from Supabase", error=str(e))
            raise


class LocalStorageService(StorageService):
    """Local filesystem storage for development when MinIO is unavailable."""
    
    def __init__(self):
        import os
        self.base_path = os.path.join(os.getcwd(), "storage")
        self._ensure_directories()
        logger.info("Local storage initialized", base_path=self.base_path)
    
    def _ensure_directories(self):
        import os
        buckets = [settings.MINIO_BUCKET, settings.STORAGE_CROPS_BUCKET]
        for bucket in buckets:
            bucket_path = os.path.join(self.base_path, bucket)
            os.makedirs(bucket_path, exist_ok=True)
    
    async def upload_file(
        self, file: BinaryIO, bucket: str, object_name: str, content_type: str = "application/octet-stream"
    ) -> str:
        import os
        file_path = os.path.join(self.base_path, bucket, object_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(file.read())
        
        logger.info("File uploaded to local storage", bucket=bucket, object_name=object_name)
        return object_name
    
    async def get_presigned_url(self, bucket: str, object_name: str, expiry: int = 3600) -> str:
        import os
        file_path = os.path.join(self.base_path, bucket, object_name)
        return f"file://{file_path}"
    
    async def delete_file(self, bucket: str, object_name: str) -> None:
        import os
        file_path = os.path.join(self.base_path, bucket, object_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info("File deleted from local storage", bucket=bucket, object_name=object_name)


class MinioStorageService(StorageService):
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self._ensure_buckets()

    def _ensure_buckets(self):
        buckets = [settings.MINIO_BUCKET, settings.STORAGE_CROPS_BUCKET]
        for bucket in buckets:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
                logger.info("Created MinIO bucket", bucket=bucket)

    async def upload_file(
        self, file: BinaryIO, bucket: str, object_name: str, content_type: str = "application/octet-stream"
    ) -> str:
        try:
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)

            self.client.put_object(
                bucket,
                object_name,
                file,
                file_size,
                content_type=content_type,
            )
            logger.info("File uploaded to MinIO", bucket=bucket, object_name=object_name)
            return object_name
        except Exception as e:
            logger.error("Failed to upload to MinIO", error=str(e))
            raise

    async def get_presigned_url(self, bucket: str, object_name: str, expiry: int = 3600) -> str:
        try:
            url = self.client.presigned_get_object(
                bucket, object_name, expires=timedelta(seconds=expiry)
            )
            return url
        except Exception as e:
            logger.error("Failed to generate presigned URL", error=str(e))
            raise

    async def delete_file(self, bucket: str, object_name: str) -> None:
        try:
            self.client.remove_object(bucket, object_name)
            logger.info("File deleted from MinIO", bucket=bucket, object_name=object_name)
        except Exception as e:
            logger.error("Failed to delete from MinIO", error=str(e))
            raise

            
def get_storage_service():
    use_supabase = (
        settings.MODE.lower() == "supabase"
        and bool(settings.SUPABASE_URL)
        and bool(settings.SUPABASE_SERVICE_KEY)
    )
    
    if use_supabase:
        return SupabaseStorageService()
    
    try:
        return MinioStorageService()
    except Exception as e:
        logger.warning("MinIO not available, using local storage", error=str(e))
        return LocalStorageService()

