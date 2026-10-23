"""
Modern async contact points backup component.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .base import BaseComponent, ComponentConfig


class ContactPointsConfig(ComponentConfig):
    """Configuration for contact points backup."""

    minimum_grafana_version: str = "9.0.0"
    file_extension: str = "contact_point"
    save_as_single_file: bool = True  # Contact points saved as single file


class ContactPointsComponent(BaseComponent):
    """Async contact points backup component."""

    @property
    def component_name(self) -> str:
        return "contact-points"

    @property
    def directory_name(self) -> str:
        return "contact_points"

    def __init__(self, config: ContactPointsConfig, backup_dir: Path, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.contact_points_config = config

    async def fetch_data(self, client: Any) -> list[dict]:
        """Fetch all contact points from Grafana."""
        status, content = await client.get("/api/v1/provisioning/contact-points")

        if status != 200:
            logger.error(f"Failed to fetch contact points: {content}")
            return []

        if not content:
            return []

        logger.info(f"Found {len(content)} contact points")
        return content

    async def save_item(self, item: dict, client: Any) -> str | None:
        """Save a single contact point."""
        try:
            # Generate filename from name
            name = item.get("name", "unknown")
            filename = name.replace("/", "_").replace("\\", "_")

            # Save to file
            return await self._save_json(item, filename)

        except Exception as e:
            logger.error(f"Failed to save contact point {item.get('name')}: {e}")
            return None
