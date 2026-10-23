"""
Modern async organizations backup component.

Backing up organizations requires Grafana admin (basic auth) credentials;
token-only auth cannot enumerate organizations. When that is not configured the
component logs a warning and yields zero organizations instead of failing the
whole backup.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .base import BaseComponent, ComponentConfig


class OrganizationsConfig(ComponentConfig):
    """Configuration for organizations backup."""
    file_extension: str = "organization"


class OrganizationsComponent(BaseComponent):
    """Async organizations backup component."""

    @property
    def component_name(self) -> str:
        return "organizations"

    def __init__(self, config: OrganizationsConfig, backup_dir: Path, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.organizations_config = config

    async def fetch_data(self, client: Any) -> list[dict]:
        """Fetch all organizations. Requires admin basic auth."""
        if not (client.config.admin_user and client.config.admin_password):
            logger.warning(
                "Skipping organizations: GRAFANA_ADMIN_ACCOUNT / GRAFANA_ADMIN_PASSWORD "
                "are required to back up organizations."
            )
            return []

        status, content = await client.get("/api/orgs")

        if status != 200:
            logger.error(f"Failed to fetch organizations: {content}")
            return []

        if not content:
            return []

        orgs = [o for o in content if isinstance(o, dict) and o.get("id") is not None]
        logger.info(f"Found {len(orgs)} organizations")
        return orgs

    async def save_item(self, item: dict, client: Any) -> str | None:
        """Save a single organization's details."""
        try:
            org_id = item.get("id")
            if org_id is None:
                logger.warning(f"Organization {item.get('name')} has no id, skipping")
                return None

            status, content = await client.get(f"/api/orgs/{org_id}")
            if status != 200:
                logger.error(f"Failed to fetch organization {org_id}: {content}")
                return None

            return await self._save_json(content, str(org_id))

        except Exception as e:
            logger.error(f"Failed to save organization {item.get('name')}: {e}")
            return None
