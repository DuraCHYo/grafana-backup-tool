"""
Restore alert rules component.
"""

from typing import Any

from loguru import logger

from grafana_backup.v2.components.restore_base import BaseRestoreComponent, RestoreConfig


class AlertRulesRestoreConfig(RestoreConfig):
    """Configuration for alert rules restore."""

    overwrite: bool = False  # Whether to overwrite existing alert rules


class AlertRulesRestoreComponent(BaseRestoreComponent):
    """Async alert rules restore component."""

    @property
    def component_name(self) -> str:
        return "alert-rules"

    @property
    def directory_name(self) -> str:
        return "alert_rules"

    def __init__(self, config: AlertRulesRestoreConfig, backup_dir, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.alert_rules_config = config

    async def restore_item(self, item: dict, client: Any) -> str | None:
        """Restore a single alert rule."""
        try:
            # Clean up the alert rule data for restore
            restore_data = {
                "name": item.get("name"),
                "folderUID": item.get("folderUID"),
                "intervalSeconds": item.get("intervalSeconds", 60),
                "condition": item.get("condition"),
                "data": item.get("data", []),
                "rules": item.get("rules", []),
            }

            # Check if alert rule already exists
            alert_rule_uid = item.get("uid")
            if alert_rule_uid:
                status, existing = await client.get(
                    f"/api/v1/provisioning/alert-rules/{alert_rule_uid}"
                )

                if status == 200 and existing:
                    if self.alert_rules_config.overwrite:
                        # Update existing alert rule
                        status, result = await client.put(
                            f"/api/v1/provisioning/alert-rules/{alert_rule_uid}", json=restore_data
                        )
                        if status == 200:
                            logger.info(f"Updated alert rule: {restore_data['name']}")
                            return alert_rule_uid
                        else:
                            logger.error(
                                f"Failed to update alert rule {restore_data['name']}: {result}"
                            )
                            return None
                    else:
                        logger.info(f"Alert rule {restore_data['name']} already exists, skipping")
                        return alert_rule_uid

            # Create new alert rule
            status, result = await client.post(
                "/api/v1/provisioning/alert-rules", json=restore_data
            )

            if status == 200:
                logger.info(f"Created alert rule: {restore_data['name']}")
                return result.get("uid")
            else:
                logger.error(f"Failed to create alert rule {restore_data['name']}: {result}")
                return None

        except Exception as e:
            logger.error(f"Failed to restore alert rule: {e}")
            return None
