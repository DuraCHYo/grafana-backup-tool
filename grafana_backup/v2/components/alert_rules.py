"""
Modern async alert rules backup component.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .base import BaseComponent, ComponentConfig


class AlertRulesConfig(ComponentConfig):
    """Configuration for alert rules backup."""

    minimum_grafana_version: str = "9.0.0"
    file_extension: str = "alert_rule"


class AlertRulesComponent(BaseComponent):
    """Async alert rules backup component."""

    @property
    def component_name(self) -> str:
        return "alert-rules"

    @property
    def directory_name(self) -> str:
        # Preserve the legacy on-disk directory name used by v1 archives.
        return "alert_rules"

    def __init__(self, config: AlertRulesConfig, backup_dir: Path, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.alert_rules_config = config

    async def fetch_data(self, client: Any) -> list[dict]:
        """Fetch all alert rules from Grafana."""
        status, content = await client.get("/api/v1/provisioning/alert-rules")

        if status != 200:
            logger.error(f"Failed to fetch alert rules: {content}")
            return []

        if not content:
            return []

        logger.info(f"Found {len(content)} alert rules")
        return content

    async def save_item(self, item: dict, client: Any) -> str | None:
        """Save a single alert rule."""
        try:
            # Generate filename from UID
            uid = item.get("uid")
            if not uid:
                logger.warning(f"Alert rule {item.get('title')} has no UID, skipping")
                return None

            # Clean up filename
            filename = uid.replace("/", "_").replace("\\", "_")

            # Save to file
            return await self._save_json(item, filename)

        except Exception as e:
            logger.error(f"Failed to save alert rule {item.get('title')}: {e}")
            return None
