"""
Modern async legacy alert channels backup component.

This covers the legacy (pre-unified) alerting notification channels exposed at
``/api/alert-notifications``. On Grafana 9+ these may be absent or empty; the
component then simply yields zero channels.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .base import BaseComponent, ComponentConfig


class AlertChannelsConfig(ComponentConfig):
    """Configuration for legacy alert channels backup."""

    file_extension: str = "alert_channel"


class AlertChannelsComponent(BaseComponent):
    """Async legacy alert channels backup component."""

    @property
    def component_name(self) -> str:
        return "alert-channels"

    @property
    def directory_name(self) -> str:
        # Preserve the legacy on-disk directory name used by v1 archives.
        return "alert_channels"

    def __init__(self, config: AlertChannelsConfig, backup_dir: Path, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.alert_channels_config = config

    async def fetch_data(self, client: Any) -> list[dict]:
        """Fetch all legacy alert notification channels."""
        status, content = await client.get("/api/alert-notifications")

        if status == 404:
            logger.info("Legacy alert channels endpoint not available (Grafana 9+?), skipping")
            return []

        if status != 200:
            logger.error(f"Failed to fetch alert channels: {content}")
            return []

        if not content:
            return []

        channels = [c for c in content if isinstance(c, dict) and (c.get("uid") or c.get("id"))]
        logger.info(f"Found {len(channels)} alert channels")
        return channels

    async def save_item(self, item: dict, client: Any) -> str | None:
        """Save a single alert channel."""
        try:
            identifier = item.get("uid") or item.get("id")
            if not identifier:
                logger.warning(f"Alert channel {item.get('name')} has no uid/id, skipping")
                return None

            filename = str(identifier).replace("/", "_").replace("\\", "_")
            return await self._save_json(item, filename)

        except Exception as e:
            logger.error(f"Failed to save alert channel {item.get('name')}: {e}")
            return None
