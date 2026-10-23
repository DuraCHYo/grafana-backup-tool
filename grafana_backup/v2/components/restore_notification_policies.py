"""
Restore notification policies component.

The policy tree is a single provisioning document. Restoring means PUTting the
backed-up tree via the provisioning API.
"""

from typing import Any

from loguru import logger

from grafana_backup.v2.components.restore_base import BaseRestoreComponent, RestoreConfig


class NotificationPoliciesRestoreConfig(RestoreConfig):
    """Configuration for notification policies restore."""

    overwrite: bool = True


class NotificationPoliciesRestoreComponent(BaseRestoreComponent):
    """Async notification policies restore component."""

    @property
    def component_name(self) -> str:
        return "notification-policy"

    @property
    def directory_name(self) -> str:
        return "notification_policies"

    def __init__(self, config: NotificationPoliciesRestoreConfig, backup_dir, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.notification_config = config

    async def restore_item(self, item: dict, client: Any) -> str | None:
        """Restore the notification policy document."""
        try:
            # The backed-up file is either the policy document or a list wrapping it.
            if isinstance(item, list):
                if not item:
                    return None
                policy = item[0]
            else:
                policy = item

            if not isinstance(policy, dict):
                logger.warning("Notification policy payload is not a dict, skipping")
                return None

            # Strip read-only fields that the provisioning API rejects.
            restore_data = {k: v for k, v in policy.items() if k not in {"id", "provenance"}}

            status, result = await client.put("/api/v1/provisioning/policies", json=restore_data)
            if status in (200, 202):
                logger.info("Restored notification policies")
                return "notification-policy"
            logger.error(f"Failed to restore notification policies: {result}")
            return None

        except Exception as e:
            logger.error(f"Failed to restore notification policies: {e}")
            return None
