"""Tests for the v2 S3 storage provider."""

from pathlib import Path

import boto3
import pytest
from moto import mock_aws

from grafana_backup.v2.config import Settings
from grafana_backup.v2.config.settings import StorageSettings
from grafana_backup.v2.storage import S3Storage, get_storage


@pytest.fixture
def s3_bucket(monkeypatch):
    """Create an in-memory S3 bucket and point boto3 at moto."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

    with mock_aws():
        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="backups")
        yield "backups"


def test_object_key_applies_prefix():
    storage = S3Storage(bucket="b", prefix="/grafana/")
    assert storage.object_key("2026-10-23-22-00.tgz") == "grafana/2026-10-23-22-00.tgz"

    no_prefix = S3Storage(bucket="b")
    assert no_prefix.object_key("archive.tgz") == "archive.tgz"


def test_upload_and_download_roundtrip(s3_bucket, tmp_path: Path):
    source = tmp_path / "2026-10-23-22-00.tgz"
    source.write_bytes(b"backup-bytes")

    storage = S3Storage(bucket=s3_bucket, prefix="grafana-backup")
    key = storage.upload(source, source.name)
    assert key == "grafana-backup/2026-10-23-22-00.tgz"

    # The object really exists in the bucket under the prefixed key.
    objects = boto3.client("s3", region_name="us-east-1").list_objects_v2(
        Bucket=s3_bucket, Prefix="grafana-backup/"
    )
    assert [o["Key"] for o in objects.get("Contents", [])] == [key]

    target = tmp_path / "downloads" / source.name
    downloaded = storage.download(source.name, target)
    assert downloaded == target
    assert target.read_bytes() == b"backup-bytes"


def test_upload_missing_file_raises(s3_bucket, tmp_path: Path):
    storage = S3Storage(bucket=s3_bucket)
    with pytest.raises(FileNotFoundError):
        storage.upload(tmp_path / "missing.tgz", "missing.tgz")


def test_get_storage_none_without_bucket(monkeypatch):
    monkeypatch.delenv("AWS_S3_BUCKET_NAME", raising=False)
    settings = Settings(storage=StorageSettings())
    assert get_storage(settings) is None


def test_get_storage_from_env(monkeypatch):
    monkeypatch.setenv("AWS_S3_BUCKET_NAME", "env-bucket")
    monkeypatch.setenv("AWS_S3_BUCKET_KEY", "prefix")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-central-1")
    monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:9000")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    storage = get_storage(Settings(storage=StorageSettings()))
    assert isinstance(storage, S3Storage)
    assert storage.bucket == "env-bucket"
    assert storage.prefix == "prefix"
    assert storage.region == "eu-central-1"
    assert storage.endpoint_url == "http://localhost:9000"
    assert storage.access_key_id == "key"
    assert storage.secret_access_key == "secret"


def test_get_storage_from_config_prefers_config(monkeypatch):
    monkeypatch.setenv("AWS_S3_BUCKET_NAME", "env-bucket")
    settings = Settings(
        storage=StorageSettings(
            s3_bucket="config-bucket",
            s3_key="backups",
            aws_region="us-west-2",
        )
    )
    storage = get_storage(settings)
    assert storage is not None
    assert storage.bucket == "config-bucket"
    assert storage.prefix == "backups"
    assert storage.region == "us-west-2"
