"""
Base restore component class for Grafana restore operations.
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import aiofiles
from loguru import logger
from pydantic import BaseModel


class RestoreConfig(BaseModel):
    """Configuration for a restore component."""

    enabled: bool = True
    retry_attempts: int = 3
    retry_delay: float = 1.0


# Maps a component's on-disk directory name to the file extension used by the
# v1 tool. Restore scans both ``*.json`` (v2) and these extensions (v1) so that
# archives produced by either version can be restored.
V1_FILE_EXTENSIONS: dict[str, str] = {
    "dashboards": "dashboard",
    "datasources": "datasource",
    "folders": "folder",
    "alert_rules": "alert_rule",
    "alert_channels": "alert_channel",
    "contact_points": "contact_point",
    "notification_policies": "notification_policies",
    "users": "user",
    "annotations": "annotation",
    "teams": "team",
    "team_members": "team_member",
    "organizations": "organization",
    "library-elements": "library_element",
    "snapshots": "snapshot",
    "dashboard_versions": "dashboard_version",
}


class BaseRestoreComponent(ABC):
    """
    Base class for all Grafana restore components.

    Provides async operations, error handling, and common functionality.
    """

    def __init__(self, config: RestoreConfig, backup_dir: Path, timestamp: str):
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

        Defaults to :attr:`component_name`. Must match the backup component's
        ``directory_name`` so restore finds the files written by backup.
        """
        return self.component_name

    @abstractmethod
    async def restore_item(self, item: dict, client: Any) -> str | None:
        """Restore a single item to Grafana. Returns ID if successful."""

    async def restore(self, client: Any) -> dict[str, Any]:
        """
        Main restore method for the component.

        Returns statistics about the restore operation.
        """
        logger.info(f"Starting restore of {self.component_name}")

        # Check if component directory exists
        if not self.component_dir.exists():
            logger.warning(f"No {self.component_name} found to restore")
            return {
                "component": self.component_name,
                "total": 0,
                "restored": 0,
                "failed": 0,
            }

        files = self._collect_files()

        if not files:
            logger.warning(f"No {self.component_name} files found to restore")
            return {
                "component": self.component_name,
                "total": 0,
                "restored": 0,
                "failed": 0,
            }

        logger.info(f"Found {len(files)} {self.component_name} files to restore")

        # Restore each item
        restored_count = 0
        failed_count = 0

        for file_path in files:
            try:
                # Load item from file
                async with aiofiles.open(file_path, "r") as f:
                    content = await f.read()
                    item = json.loads(content)

                # Restore item
                result = await self.restore_item(item, client)
                if result:
                    restored_count += 1
                    logger.debug(f"Restored {self.component_name} from {file_path}")
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Failed to restore {self.component_name} from {file_path}: {e}")
                failed_count += 1

        stats = {
            "component": self.component_name,
            "total": len(files),
            "restored": restored_count,
            "failed": failed_count,
        }

        logger.info(f"Restore of {self.component_name} completed: {stats}")
        return stats

    def _collect_files(self) -> list[Path]:
        """Collect restorable files (v2 ``*.json`` plus v1 extensions).

        Recurses into subdirectories so components that store items per-parent
        (e.g. ``dashboard-versions``) are picked up as well.
        """
        files: list[Path] = list(self.component_dir.rglob("*.json"))

        v1_extension = V1_FILE_EXTENSIONS.get(self.directory_name)
        if v1_extension:
            for path in self.component_dir.rglob(f"*.{v1_extension}"):
                # Skip auxiliary files such as folder permission exports.
                if path.name.endswith(
                    (f"_permission.{v1_extension}", f"_permissions.{v1_extension}")
                ):
                    continue
                files.append(path)

        # De-duplicate while preserving deterministic order.
        return sorted(set(files))
