"""
Amazon S3 (and S3-compatible: MinIO, Garage, AIStor, R2, ...) provider.
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from grafana_backup.v2.storage.base import StorageProvider


class S3Storage(StorageProvider):
    """Uploads/downloads backup archives with ``boto3``."""

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        region: str | None = None,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ):
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.region = region
        self.endpoint_url = endpoint_url
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self._client = None

    @property
    def name(self) -> str:
        return "s3"

    def object_key(self, file_name: str) -> str:
        return f"{self.prefix}/{file_name}" if self.prefix else file_name

    def _get_client(self):
        if self._client is not None:
            return self._client

        try:
            import boto3
        except ImportError as e:  # pragma: no cover - depends on install extras
            raise RuntimeError(
                "boto3 is required for S3 uploads. Install it with "
                "`pip install boto3` (or `pip install grafana-backup-tool[cloud]`)."
            ) from e

        client_kwargs = {}
        if self.region:
            client_kwargs["region_name"] = self.region
        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url
        if self.access_key_id and self.secret_access_key:
            client_kwargs["aws_access_key_id"] = self.access_key_id
            client_kwargs["aws_secret_access_key"] = self.secret_access_key

        self._client = boto3.client("s3", **client_kwargs)
        return self._client

    def upload(self, source_path: Path, destination_name: str) -> str:
        key = self.object_key(destination_name)
        logger.info(f"Uploading {source_path} to s3://{self.bucket}/{key}")
        self._get_client().upload_file(str(source_path), self.bucket, key)
        logger.info(f"Uploaded to S3: s3://{self.bucket}/{key}")
        return key

    def download(self, source_name: str, target_path: Path) -> Path:
        key = self.object_key(source_name)
        logger.info(f"Downloading s3://{self.bucket}/{key} to {target_path}")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        self._get_client().download_file(self.bucket, key, str(target_path))
        return target_path
