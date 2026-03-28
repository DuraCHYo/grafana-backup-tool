from abc import ABC, abstractmethod


class BaseStorageProvider(ABC):
    def __init__(self, settings):
        self.settings = settings

    @abstractmethod
    def upload(self, source_path, destination_name):
        pass

    @abstractmethod
    def download(self, target_name):
        pass
