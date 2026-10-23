"""
Restore organizations component.
"""

from typing import Any

from loguru import logger

from grafana_backup.v2.components.restore_base import BaseRestoreComponent, RestoreConfig


class OrganizationsRestoreConfig(RestoreConfig):
    """Configuration for organizations restore."""
    overwrite: bool = False


class OrganizationsRestoreComponent(BaseRestoreComponent):
    """Async organizations restore component."""

    @property
    def component_name(self) -> str:
        return "organizations"

    def __init__(self, config: OrganizationsRestoreConfig, backup_dir, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.organizations_config = config

    async def restore_item(self, item: dict, client: Any) -> str | None:
        """Restore a single organization."""
        try:
            name = item.get("name")
            if not name:
                logger.warning("Organization has no name, skipping")
                return None

            # Check for an existing organization with the same name.
            status, orgs = await client.get("/api/orgs")
            if status == 200 and isinstance(orgs, list):
                for org in orgs:
                    if org.get("name") == name:
                        logger.info(f"Organization {name} already exists, reusing")
                        return str(org.get("id"))

            restore_data = {"name": name}
            status, result = await client.post("/api/orgs", json=restore_data)
            if status == 200:
                org_id = result.get("orgId") or result.get("id")
                logger.info(f"Created organization: {name}")

                # Restore the preferred main org name if present.
                address = item.get("address")
                if address:
                    logger.debug(f"Organization {name} address is not restored by the API")
                return str(org_id)

            logger.error(f"Failed to create organization {name}: {result}")
            return None

        except Exception as e:
            logger.error(f"Failed to restore organization: {e}")
            return None
