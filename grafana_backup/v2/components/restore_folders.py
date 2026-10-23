"""
Restore folders component.
"""

from typing import Any

from loguru import logger

from grafana_backup.v2.components.restore_base import BaseRestoreComponent, RestoreConfig


class FoldersRestoreConfig(RestoreConfig):
    """Configuration for folders restore."""
    overwrite: bool = False  # Whether to overwrite existing folders
    restore_permissions: bool = True  # Whether to restore folder permissions


class FoldersRestoreComponent(BaseRestoreComponent):
    """Async folders restore component."""
    
    @property
    def component_name(self) -> str:
        return "folders"
    
    def __init__(self, config: FoldersRestoreConfig, backup_dir, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.folder_config = config
    
    async def restore_item(self, item: dict, client: Any) -> str | None:
        """Restore a single folder."""
        try:
            # Clean up the folder data for restore
            restore_data = {
                "title": item.get("title"),
                "uid": item.get("uid"),
            }
            
            # Check if folder already exists
            status, existing = await client.get(f"/api/folders/{restore_data['uid']}")
            
            if status == 200 and existing:
                if self.folder_config.overwrite:
                    # Update existing folder
                    status, result = await client.put(
                        f"/api/folders/{restore_data['uid']}",
                        json=restore_data
                    )
                    if status == 200:
                        logger.info(f"Updated folder: {restore_data['title']}")
                        folder_uid = result.get("uid")
                    else:
                        logger.error(f"Failed to update folder {restore_data['title']}: {result}")
                        return None
                else:
                    logger.info(f"Folder {restore_data['title']} already exists, skipping")
                    folder_uid = existing.get("uid")
            else:
                # Create new folder
                status, result = await client.post(
                    "/api/folders",
                    json=restore_data
                )
                
                if status == 200:
                    logger.info(f"Created folder: {restore_data['title']}")
                    folder_uid = result.get("uid")
                else:
                    logger.error(f"Failed to create folder {restore_data['title']}: {result}")
                    return None
            
            # Restore permissions if requested
            if self.folder_config.restore_permissions and folder_uid:
                await self._restore_permissions(item, folder_uid, client)
            
            return folder_uid
                
        except Exception as e:
            logger.error(f"Failed to restore folder: {e}")
            return None
    
    async def _restore_permissions(self, original_item: dict, folder_uid: str, client: Any):
        """Restore folder permissions."""
        try:
            # Try to find permissions file
            permissions_file = self.component_dir / f"{original_item.get('uid')}_permission.json"
            
            if not permissions_file.exists():
                logger.debug(f"No permissions file found for folder {folder_uid}")
                return
            
            # Read permissions file
            import json

            import aiofiles
            async with aiofiles.open(permissions_file, 'r') as f:
                content = await f.read()
                permissions = json.loads(content)
            
            # Update permissions
            status, result = await client.patch(
                f"/api/folders/{folder_uid}/permissions",
                json={"items": permissions}
            )
            
            if status == 200:
                logger.info(f"Restored permissions for folder {folder_uid}")
            else:
                logger.warning(f"Failed to restore permissions for folder {folder_uid}: {result}")
                
        except Exception as e:
            logger.warning(f"Failed to restore folder permissions: {e}")