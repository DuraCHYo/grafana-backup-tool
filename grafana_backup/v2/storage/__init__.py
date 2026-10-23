"""
Cloud storage providers for Grafana backup v2.

Providers are intentionally thin: they only move the finished archive to/from
remote storage. Everything else (building the archive) stays in the backup
coordinator.
"""

from __future__ import annotations

import os

from grafana_backup.v2.config import Settings
from grafana_backup.v2.storage.base import StorageProvider
from grafana_backup.v2.storage.s3 import S3Storage

__all__ = ["S3Storage", "StorageProvider", "get_storage"]


def get_storage(settings: Settings) -> StorageProvider | None:
    """Return the configured remote storage provider, if any.

    S3 is selected when a bucket is configured either in the JSON config
    (``aws.s3_bucket_name``) or via the documented ``AWS_S3_BUCKET_NAME``
    environment variable. Credentials and endpoint follow the standard AWS
    environment variables so EC2/ECS/EKS roles keep working untouched.
    """
    storage = settings.storage

    bucket = storage.s3_bucket or os.getenv("AWS_S3_BUCKET_NAME")
    if not bucket:
        return None

    return S3Storage(
        bucket=bucket,
        prefix=(storage.s3_key or os.getenv("AWS_S3_BUCKET_KEY") or "").strip("/"),
        region=storage.aws_region or os.getenv("AWS_DEFAULT_REGION"),
        endpoint_url=storage.s3_endpoint_url or os.getenv("AWS_ENDPOINT_URL"),
        access_key_id=storage.aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
        secret_access_key=storage.aws_secret_access_key
        or os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
