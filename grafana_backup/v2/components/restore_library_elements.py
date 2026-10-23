"""
Restore library elements component.
"""

from typing import Any

from loguru import logger

from grafana_backup.v2.components.restore_base import BaseRestoreComponent, RestoreConfig


class LibraryElementsRestoreConfig(RestoreConfig):
    """Configuration for library elements restore."""
    overwrite: bool = False


class LibraryElementsRestoreComponent(BaseRestoreComponent):
    """Async library elements restore component."""

    @property
    def component_name(self) -> str:
        return "library-elements"

    def __init__(self, config: LibraryElementsRestoreConfig, backup_dir, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.library_config = config

    async def restore_item(self, item: dict, client: Any) -> str | None:
        """Restore a single library element."""
        try:
            uid = item.get("uid")
            name = item.get("name")

            # Resolve target folder: prefer uid, fall back to name lookup.
            folder_uid = item.get("folderUid")
            if not folder_uid and item.get("folderId"):
                status, folder = await client.get(f"/api/folders/id/{item.get('folderId')}")
                if status == 200 and isinstance(folder, dict):
                    folder_uid = folder.get("uid")

            restore_data = {
                "name": name,
                "kind": item.get("kind", 1),
                "model": item.get("model"),
                "folderUid": folder_uid or "",
            }
            if uid:
                restore_data["uid"] = uid

            # Check whether the element already exists.
            if uid:
                status, existing = await client.get(f"/api/library-elements/{uid}")
                if status == 200 and existing:
                    if self.library_config.overwrite:
                        status, result = await client.patch(
                            f"/api/library-elements/{uid}", json=restore_data
                        )
                        if status == 200:
                            logger.info(f"Updated library element: {name}")
                            return uid
                        logger.error(f"Failed to update library element {name}: {result}")
                        return None
                    logger.info(f"Library element {name} already exists, skipping")
                    return uid

            status, result = await client.post("/api/library-elements", json=restore_data)
            if status in (200, 201):
                restored_uid = result.get("result", {}).get("uid", uid)
                logger.info(f"Created library element: {name}")
                return restored_uid
            logger.error(f"Failed to create library element {name}: {result}")
            return None

        except Exception as e:
            logger.error(f"Failed to restore library element: {e}")
            return None
