"""
Restore annotations component.
"""

from typing import Any

from loguru import logger

from grafana_backup.v2.components.restore_base import BaseRestoreComponent, RestoreConfig


class AnnotationsRestoreConfig(RestoreConfig):
    """Configuration for annotations restore."""

    overwrite: bool = False  # Whether to remove existing annotations first


class AnnotationsRestoreComponent(BaseRestoreComponent):
    """Async annotations restore component."""

    @property
    def component_name(self) -> str:
        return "annotations"

    def __init__(
        self, config: AnnotationsRestoreConfig, backup_dir, timestamp: str
    ):
        super().__init__(config, backup_dir, timestamp)
        self.annotations_config = config

    async def restore_item(self, item: dict, client: Any) -> str | None:
        """Restore a single annotation."""
        try:
            if not item.get("text"):
                logger.warning("Annotation has no text, skipping")
                return None

            restore_data: dict[str, Any] = {
                "text": item.get("text"),
                "tags": item.get("tags", []),
            }

            # Carry over optional scoping fields when present.
            if item.get("time"):
                restore_data["time"] = item["time"]
            if item.get("timeEnd"):
                restore_data["timeEnd"] = item["timeEnd"]
            if item.get("panelId"):
                restore_data["panelId"] = item["panelId"]
            if item.get("dashboardId"):
                restore_data["dashboardId"] = item["dashboardId"]

            # Create new annotation
            status, result = await client.post("/api/annotations", json=restore_data)

            if status == 200:
                text = (restore_data.get("text") or "")[:50]
                logger.info(f"Created annotation: {text}...")
                return str(result.get("id"))

            logger.error(f"Failed to create annotation: {result}")
            return None

        except Exception as e:
            logger.error(f"Failed to restore annotation: {e}")
            return None
