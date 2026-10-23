"""
Restore legacy alert channels component.
"""

from typing import Any

from loguru import logger

from grafana_backup.v2.components.restore_base import BaseRestoreComponent, RestoreConfig


class AlertChannelsRestoreConfig(RestoreConfig):
    """Configuration for legacy alert channels restore."""

    overwrite: bool = False


class AlertChannelsRestoreComponent(BaseRestoreComponent):
    """Async legacy alert channels restore component."""

    @property
    def component_name(self) -> str:
        return "alert-channels"

    @property
    def directory_name(self) -> str:
        return "alert_channels"

    def __init__(self, config: AlertChannelsRestoreConfig, backup_dir, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.alert_channels_config = config

    async def restore_item(self, item: dict, client: Any) -> str | None:
        """Restore a single legacy alert notification channel."""
        try:
            name = item.get("name")
            if not name:
                logger.warning("Alert channel has no name, skipping")
                return None

            restore_data = {
                "name": name,
                "type": item.get("type"),
                "isDefault": item.get("isDefault", False),
                "sendReminder": item.get("sendReminder", False),
                "frequency": item.get("frequency", ""),
                "settings": item.get("settings", {}),
                "disableResolveMessage": item.get("disableResolveMessage", False),
            }

            uid = item.get("uid")
            if uid:
                status, existing = await client.get(f"/api/alert-notifications/uid/{uid}")
                if status == 200 and existing:
                    if self.alert_channels_config.overwrite:
                        status, result = await client.put(
                            f"/api/alert-notifications/uid/{uid}", json=restore_data
                        )
                        if status == 200:
                            logger.info(f"Updated alert channel: {name}")
                            return uid
                        logger.error(f"Failed to update alert channel {name}: {result}")
                        return None
                    logger.info(f"Alert channel {name} already exists, skipping")
                    return uid

            status, result = await client.post("/api/alert-notifications", json=restore_data)
            if status == 200:
                logger.info(f"Created alert channel: {name}")
                return result.get("uid") or result.get("id")
            logger.error(f"Failed to create alert channel {name}: {result}")
            return None

        except Exception as e:
            logger.error(f"Failed to restore alert channel: {e}")
            return None
