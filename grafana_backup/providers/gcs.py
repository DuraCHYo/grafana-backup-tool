import io
from google.cloud import storage

from google.api_core import exceptions as google_exceptions
from .base import BaseStorageProvider


class GCSProvider(BaseStorageProvider):
    def __init__(self, settings):
        super().__init__(settings)
        self.bucket_name = settings.get("GCS_BUCKET_NAME")
        self.bucket_path = settings.get("GCS_BUCKET_PATH", "").strip("/")
        self.storage_client = storage.Client()

    def _get_blob(self, blob_name):
        bucket = self.storage_client.bucket(self.bucket_name)
        full_path = (
            blob_name if not self.bucket_path else f"{self.bucket_path}/{blob_name}"
        )
        return bucket.blob(full_path)

    def upload(self, source_path, destination_name):
        try:
            blob = self._get_blob(destination_name)
            blob.upload_from_filename(source_path)
            print(f"Upload to GCS bucket '{self.bucket_name}' was successful")
            return True
        except google_exceptions.Forbidden as e:
            print(f"GCS Permission denied: {e}")
        except google_exceptions.NotFound:
            print(f"GCS Bucket '{self.bucket_name}' not found")
        except Exception as e:
            print(f"GCS Upload Error: {e}")
        return False

    def download(self, target_name):
        try:
            blob = self._get_blob(target_name)
            data = blob.download_as_bytes()
            return io.BytesIO(data)
        except google_exceptions.NotFound:
            print(f"GCS File or Bucket not found: {target_name}")
        except google_exceptions.Forbidden as e:
            print(f"GCS Permission denied: {e}")
        except Exception as e:
            print(f"GCS Download Error: {e}")
        return None
