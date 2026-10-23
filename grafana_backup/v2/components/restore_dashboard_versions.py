"""
Restore dashboard versions component.

Version history is managed by Grafana itself; the meaningful restoration action
is to make the latest backed-up version the current dashboard. This component
reads per-dashboard subdirectories and re-imports the highest version number.
"""

from typing import Any

from loguru import logger

from grafana_backup.v2.components.restore_base import BaseRestoreComponent, RestoreConfig


class DashboardVersionsRestoreConfig(RestoreConfig):
    """Configuration for dashboard versions restore."""

    overwrite: bool = True
    import_overwrite: bool = True


class DashboardVersionsRestoreComponent(BaseRestoreComponent):
    """Async dashboard versions restore component."""

    @property
    def component_name(self) -> str:
        return "dashboard-versions"

    @property
    def directory_name(self) -> str:
        return "dashboard_versions"

    def __init__(
        self, config: DashboardVersionsRestoreConfig, backup_dir, timestamp: str
    ):
        super().__init__(config, backup_dir, timestamp)
        self.versions_config = config

    async def restore_item(self, item: dict, client: Any) -> str | None:
        """Restore a single dashboard version document."""
        try:
            # A version document from /versions/{n} is {dashboard, meta}.
            dashboard = item.get("dashboard", item)
            if not isinstance(dashboard, dict) or not dashboard.get("uid"):
                return None

            restore_data = {
                "dashboard": dashboard,
                "overwrite": self.versions_config.import_overwrite,
                "message": "Restored from backup (version)",
            }

            status, result = await client.post("/api/dashboards/db", json=restore_data)
            if status == 200:
                uid = result.get("uid")
                version = result.get("version")
                logger.info(f"Restored dashboard version for {uid} (v{version})")
                return uid
            logger.error(f"Failed to restore dashboard version: {result}")
            return None

        except Exception as e:
            logger.error(f"Failed to restore dashboard version: {e}")
            return None
