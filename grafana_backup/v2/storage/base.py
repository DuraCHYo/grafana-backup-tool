"""
Base interface for remote storage providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class StorageProvider(ABC):
    """Moves finished backup archives to and from remote storage."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short provider identifier used in logs/stats (e.g. ``s3``)."""

    @abstractmethod
    def object_key(self, file_name: str) -> str:
        """Return the remote object key for a local file name (incl. prefix)."""

    @abstractmethod
    def upload(self, source_path: Path, destination_name: str) -> str:
        """Upload ``source_path`` and return the remote object key.

        Raises on failure so callers can surface a real error instead of
        silently losing the archive.
        """

    @abstractmethod
    def download(self, source_name: str, target_path: Path) -> Path:
        """Download ``source_name`` to ``target_path`` and return the path."""
