"""
Restore dashboards component.
"""

from typing import Any

from loguru import logger

from grafana_backup.v2.components.restore_base import BaseRestoreComponent, RestoreConfig


class DashboardsRestoreConfig(RestoreConfig):
    """Configuration for dashboards restore."""
    overwrite: bool = False  # Whether to overwrite existing dashboards
    import_overwrite: bool = True  # Grafana import overwrite flag


class DashboardsRestoreComponent(BaseRestoreComponent):
    """Async dashboards restore component."""
    
    @property
    def component_name(self) -> str:
        return "dashboards"
    
    def __init__(self, config: DashboardsRestoreConfig, backup_dir, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.dashboard_config = config
    
    async def restore_item(self, item: dict, client: Any) -> str | None:
        """Restore a single dashboard."""
        try:
            # Extract dashboard data from backup format
            # v2 backup saves the full dashboard object
            dashboard_data = item.get("dashboard", item)
            
            # Clean up the dashboard data for restore
            restore_data = {
                "dashboard": dashboard_data,
                "overwrite": self.dashboard_config.import_overwrite,
                "message": "Restored from backup",
            }
            
            # Check if dashboard already exists
            dashboard_uid = dashboard_data.get("uid")
            if dashboard_uid:
                status, existing = await client.get(f"/api/dashboards/uid/{dashboard_uid}")
                
                if status == 200 and existing:
                    if self.dashboard_config.overwrite:
                        logger.info(f"Updating existing dashboard: {dashboard_uid}")
                    else:
                        logger.info(f"Dashboard {dashboard_uid} already exists, skipping")
                        return dashboard_uid
            
            # Create/update dashboard
            status, result = await client.post(
                "/api/dashboards/db",
                json=restore_data
            )
            
            if status == 200:
                restored_uid = result.get("uid")
                logger.info(f"Restored dashboard: {restored_uid}")
                return restored_uid
            else:
                logger.error(f"Failed to restore dashboard: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to restore dashboard: {e}")
            return None