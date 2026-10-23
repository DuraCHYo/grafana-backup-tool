"""
Base component class for Grafana backup operations.
Provides async support and common functionality for all backup components.
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import aiofiles
from loguru import logger
from pydantic import BaseModel


class ComponentConfig(BaseModel):
    """Configuration for a backup component."""

    enabled: bool = True
    pretty_print: bool = False
    retry_attempts: int = 3
    retry_delay: float = 1.0
    file_extension: str = "json"
    save_as_single_file: bool = False  # For components that save all data in one file


class BaseComponent(ABC):
    """
    Base class for all Grafana backup components.

    Provides async operations, error handling, and common functionality.
    """

    def __init__(self, config: ComponentConfig, backup_dir: Path, timestamp: str):
        self.config = config
        self.backup_dir = backup_dir
        self.timestamp = timestamp
        self.component_dir = backup_dir / self.directory_name / timestamp

    @property
    @abstractmethod
    def component_name(self) -> str:
        """Return the component name (e.g., 'dashboards', 'datasources')."""

    @property
    def directory_name(self) -> str:
        """Return the on-disk directory name for this component.

        Defaults to :attr:`component_name`. Components whose v1 archive layout
        differs may override this to keep archive compatibility.
        """
        return self.component_name

    @abstractmethod
    async def fetch_data(self, client: Any) -> list[dict]:
        """Fetch data from Grafana API."""

    @abstractmethod
    async def save_item(self, item: dict, client: Any) -> str | None:
        """Save a single item to disk. Returns file path if successful."""

    async def backup(self, client: Any) -> dict[str, Any]:
        """
        Main backup method for the component.

        Returns statistics about the backup operation.
        """
        logger.info(f"Starting backup of {self.component_name}")

        # Create component directory
        self.component_dir.mkdir(parents=True, exist_ok=True)

        # Fetch data from Grafana
        items = await self.fetch_data(client)

        if not items:
            logger.warning(f"No {self.component_name} found to backup")
            return {
                "component": self.component_name,
                "total": 0,
                "saved": 0,
                "failed": 0,
            }

        logger.info(f"Found {len(items)} {self.component_name} to backup")

        # Handle single file save mode
        if self.config.save_as_single_file:
            filename = f"{self.component_name}_{self.timestamp}"
            file_path = await self._save_json(items, filename)
            saved_count = 1 if file_path else 0
            failed_count = 0 if file_path else 1
        else:
            # Save each item individually
            saved_count = 0
            failed_count = 0

            for item in items:
                try:
                    file_path = await self.save_item(item, client)
                    if file_path:
                        saved_count += 1
                        logger.debug(f"Saved {self.component_name} to {file_path}")
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Failed to save {self.component_name} item: {e}")
                    failed_count += 1

        stats = {
            "component": self.component_name,
            "total": len(items),
            "saved": saved_count,
            "failed": failed_count,
        }

        logger.info(f"Backup of {self.component_name} completed: {stats}")
        return stats

    async def _save_json(self, data: Any, filename: str) -> str:
        """Helper method to save JSON data to file."""
        extension = self.config.file_extension
        file_path = self.component_dir / f"{filename}.{extension}"

        json_content = json.dumps(
            data, indent=4 if self.config.pretty_print else None, ensure_ascii=False
        )

        async with aiofiles.open(file_path, "w") as f:
            await f.write(json_content)

        return str(file_path)
