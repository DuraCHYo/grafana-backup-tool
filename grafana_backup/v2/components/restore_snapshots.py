"""
Restore snapshots component.

Snapshots are immutable point-in-time copies, so "restore" means recreating the
snapshot on the target Grafana via the snapshot create API.
"""

from typing import Any

from loguru import logger

from grafana_backup.v2.components.restore_base import BaseRestoreComponent, RestoreConfig


class SnapshotsRestoreConfig(RestoreConfig):
    """Configuration for snapshots restore."""
    overwrite: bool = False


class SnapshotsRestoreComponent(BaseRestoreComponent):
    """Async snapshots restore component."""

    @property
    def component_name(self) -> str:
        return "snapshots"

    def __init__(self, config: SnapshotsRestoreConfig, backup_dir, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.snapshots_config = config

    async def restore_item(self, item: dict, client: Any) -> str | None:
        """Recreate a snapshot on the target Grafana."""
        try:
            dashboard = item.get("dashboard")
            if dashboard is None:
                logger.warning("Snapshot has no dashboard payload, skipping")
                return None

            restore_data = {
                "dashboard": dashboard,
                "name": item.get("name", "restored-snapshot"),
                "external": item.get("external", False),
                "expires": item.get("expires", 0),
            }

            status, result = await client.post("/api/snapshots", json=restore_data)
            if status == 200:
                key = result.get("key")
                logger.info(f"Created snapshot: {restore_data['name']}")
                return key
            logger.error(f"Failed to create snapshot {restore_data['name']}: {result}")
            return None

        except Exception as e:
            logger.error(f"Failed to restore snapshot: {e}")
            return None
