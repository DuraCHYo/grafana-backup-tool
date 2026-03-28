import io
from azure.storage.blob import BlobServiceClient
from .base import BaseStorageProvider


class AzureProvider(BaseStorageProvider):
    def __init__(self, settings):
        super().__init__(settings)
        self.connection_string = settings.get("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = settings.get("AZURE_STORAGE_CONTAINER_NAME")
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )

    def _get_blob_client(self, blob_name):
        return self.blob_service_client.get_blob_client(
            container=self.container_name, blob=blob_name
        )

    def upload(self, source_path, destination_name):
        try:
            blob_client = self._get_blob_client(destination_name)
            with open(source_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            print(f"Upload to Azure Storage ({destination_name}) was successful")
            return True
        except FileNotFoundError:
            print(f"Error: Local file {source_path} not found")
            return False
        except Exception as e:
            print(f"Azure Upload Error: {str(e)}")
            return False

    def download(self, target_name):
        try:
            blob_client = self._get_blob_client(target_name)
            azure_storage_bytes = blob_client.download_blob().readall()
            print(f"Download from Azure Storage ({target_name}) was successful")
            return io.BytesIO(azure_storage_bytes)
        except Exception as e:
            print(f"Azure Download Error: {str(e)}")
            return None
