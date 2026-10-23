"""
Modern async notification policies backup component.

The unified-alerting notification policy tree is served from the provisioning
API (``/api/v1/provisioning/policies``). It is a single document, so it is saved
as one file, matching the v1 layout.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .base import BaseComponent, ComponentConfig


class NotificationPoliciesConfig(ComponentConfig):
    """Configuration for notification policies backup."""

    file_extension: str = "notification_policies"
    save_as_single_file: bool = True


class NotificationPoliciesComponent(BaseComponent):
    """Async notification policies backup component."""

    @property
    def component_name(self) -> str:
        return "notification-policy"

    @property
    def directory_name(self) -> str:
        # Preserve the legacy on-disk directory name used by v1 archives.
        return "notification_policies"

    def __init__(self, config: NotificationPoliciesConfig, backup_dir: Path, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.notification_config = config

    async def fetch_data(self, client: Any) -> list[dict]:
        """Fetch the notification policy tree (a single document)."""
        status, content = await client.get("/api/v1/provisioning/policies")

        if status == 404:
            logger.info("Notification policies endpoint not available, skipping")
            return []

        if status != 200:
            logger.error(f"Failed to fetch notification policies: {content}")
            return []

        if not content:
            return []

        # Wrap the single document in a list so base ``save_as_single_file``
        # logic saves it verbatim under a predictable filename.
        return [content]

    async def save_item(self, item: dict, client: Any) -> str | None:
        """Save the notification policy document."""
        try:
            return await self._save_json(item, "notification_policies")
        except Exception as e:
            logger.error(f"Failed to save notification policies: {e}")
            return None
