from minio import Minio
from minio.error import S3Error
from backend.app.core.config import settings
import io

class MinioService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(settings.MINIO_BUCKET_DOCUMENTS):
                self.client.make_bucket(settings.MINIO_BUCKET_DOCUMENTS)
                # Enable versioning
                self.client.set_bucket_versioning(
                    settings.MINIO_BUCKET_DOCUMENTS,
                    {"Status": "Enabled"}
                )
        except S3Error as e:
            print(f"MinIO Connection Error: {e}")

    def upload_file(self, file_data: bytes, object_name: str, content_type: str) -> str:
        """
        Uploads a file and returns the version ID.
        """
        result = self.client.put_object(
            settings.MINIO_BUCKET_DOCUMENTS,
            object_name,
            io.BytesIO(file_data),
            len(file_data),
            content_type=content_type
        )
        return result.version_id

    def get_file(self, object_name: str, version_id: str = None):
        try:
            response = self.client.get_object(
                settings.MINIO_BUCKET_DOCUMENTS,
                object_name,
                version_id=version_id
            )
            return response.read()
        finally:
            # response.close()
            # response.release_conn()
            pass

    def delete_file(self, object_name: str):
        self.client.remove_object(settings.MINIO_BUCKET_DOCUMENTS, object_name)

minio_client = MinioService()
