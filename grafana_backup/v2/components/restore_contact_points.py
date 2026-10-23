"""
Restore contact points component.
"""

from typing import Any

from loguru import logger

from grafana_backup.v2.components.restore_base import BaseRestoreComponent, RestoreConfig


class ContactPointsRestoreConfig(RestoreConfig):
    """Configuration for contact points restore."""

    overwrite: bool = False  # Whether to overwrite existing contact points


class ContactPointsRestoreComponent(BaseRestoreComponent):
    """Async contact points restore component."""

    @property
    def component_name(self) -> str:
        return "contact-points"

    @property
    def directory_name(self) -> str:
        return "contact_points"

    def __init__(self, config: ContactPointsRestoreConfig, backup_dir, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.contact_points_config = config

    async def restore_item(self, item: dict, client: Any) -> str | None:
        """Restore contact points (saved as single file)."""
        try:
            # For contact points, the item is a list of contact points
            if isinstance(item, list):
                contact_points = item
            else:
                contact_points = [item]

            restored_count = 0
            for contact_point in contact_points:
                try:
                    # Clean up the contact point data for restore
                    restore_data = {
                        "name": contact_point.get("name"),
                        "type": contact_point.get("type"),
                        "settings": contact_point.get("settings", {}),
                        "disableResolveMessage": contact_point.get("disableResolveMessage", False),
                    }

                    # Check if contact point already exists
                    contact_point_name = contact_point.get("name")
                    status, existing = await client.get("/api/v1/provisioning/contact-points")

                    if status == 200 and existing:
                        existing_names = [cp.get("name") for cp in existing]
                        if contact_point_name in existing_names:
                            if self.contact_points_config.overwrite:
                                # Update existing contact point
                                uid = next(
                                    cp.get("uid")
                                    for cp in existing
                                    if cp.get("name") == contact_point_name
                                )
                                status, result = await client.put(
                                    f"/api/v1/provisioning/contact-points/{uid}", json=restore_data
                                )
                                if status == 200:
                                    logger.info(f"Updated contact point: {contact_point_name}")
                                    restored_count += 1
                                else:
                                    logger.error(
                                        f"Failed to update contact point {contact_point_name}: {result}"
                                    )
                            else:
                                logger.info(
                                    f"Contact point {contact_point_name} already exists, skipping"
                                )
                                restored_count += 1
                        else:
                            # Create new contact point
                            status, result = await client.post(
                                "/api/v1/provisioning/contact-points", json=restore_data
                            )
                            if status == 200:
                                logger.info(f"Created contact point: {contact_point_name}")
                                restored_count += 1
                            else:
                                logger.error(
                                    f"Failed to create contact point {contact_point_name}: {result}"
                                )
                    else:
                        # Create new contact point
                        status, result = await client.post(
                            "/api/v1/provisioning/contact-points", json=restore_data
                        )
                        if status == 200:
                            logger.info(f"Created contact point: {contact_point_name}")
                            restored_count += 1
                        else:
                            logger.error(
                                f"Failed to create contact point {contact_point_name}: {result}"
                            )

                except Exception as e:
                    logger.error(f"Failed to restore contact point: {e}")

            return str(restored_count) if restored_count > 0 else None

        except Exception as e:
            logger.error(f"Failed to restore contact points: {e}")
            return None
