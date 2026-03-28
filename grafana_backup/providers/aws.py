import boto3
from io import BytesIO
from botocore.exceptions import NoCredentialsError, ClientError
from .base import BaseStorageProvider

# Импортируем типы только для проверки (не влияют на работу)
from typing import Any


class S3Provider(BaseStorageProvider):
    def __init__(self, settings):
        super().__init__(settings)
        self.bucket_name = settings.get("AWS_S3_BUCKET_NAME")
        self.bucket_key = settings.get("AWS_S3_BUCKET_KEY", "").strip("/")

        self.s3_resource: Any = self._init_s3_resource()

    def _init_s3_resource(self):
        aws_access_key = self.settings.get("AWS_ACCESS_KEY_ID")
        aws_secret_key = self.settings.get("AWS_SECRET_ACCESS_KEY")
        aws_default_region = self.settings.get("AWS_DEFAULT_REGION")
        endpoint_url = self.settings.get("AWS_ENDPOINT_URL")

        session = boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_default_region,
        )

        return session.resource(service_name="s3", endpoint_url=endpoint_url)

    def _get_s3_object(self, file_name: str):
        full_key = f"{self.bucket_key}/{file_name}" if self.bucket_key else file_name
        return self.s3_resource.Object(self.bucket_name, full_key)

    def upload(self, source_path: str, destination_name: str) -> bool:
        try:
            s3_obj = self._get_s3_object(destination_name)
            with open(source_path, "rb") as data:
                s3_obj.put(Body=data)
            print(f"Successfully uploaded to S3: {s3_obj.key}")
            return True
        except (NoCredentialsError, ClientError, FileNotFoundError) as e:
            print(f"S3 Upload error: {e}")
            return False

    def download(self, target_name: str) -> BytesIO | None:
        try:
            s3_obj = self._get_s3_object(target_name)
            body = s3_obj.get()["Body"].read()
            return BytesIO(body)
        except Exception as e:
            print(f"S3 Download error: {e}")
            return None
