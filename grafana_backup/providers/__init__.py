from .aws import S3Provider
from .azure import AzureProvider
from .gcs import GCSProvider


def get_provider(settings):
    """Defines which cloud to use"""
    if settings.get("AWS_S3_BUCKET_NAME"):
        return S3Provider(settings)

    if settings.get("AZURE_STORAGE_CONTAINER_NAME"):
        return AzureProvider(settings)

    if settings.get("GCS_BUCKET_NAME"):
        return GCSProvider(settings)
    return None
