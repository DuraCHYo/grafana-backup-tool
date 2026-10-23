"""
Modern async folders backup component.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .base import BaseComponent, ComponentConfig


class FolderConfig(ComponentConfig):
    """Configuration for folders backup."""
    uid_support: bool = True
    include_permissions: bool = True
    file_extension: str = "folder"


class FoldersComponent(BaseComponent):
    """Async folders backup component."""
    
    @property
    def component_name(self) -> str:
        return "folders"
    
    def __init__(self, config: FolderConfig, backup_dir: Path, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.folder_config = config
    
    async def fetch_data(self, client: Any) -> list[dict]:
        """Fetch all folders from Grafana."""
        status, content = await client.get(
            "/api/search",
            params={"type": "dash-folder"}
        )
        
        if status != 200:
            logger.error(f"Failed to fetch folders: {content}")
            return []
        
        if not content:
            return []
        
        logger.info(f"Found {len(content)} folders")
        return content
    
    async def save_item(self, item: dict, client: Any) -> str | None:
        """Save a single folder with its settings and permissions."""
        try:
            uid = item.get("uid")
            if not uid:
                logger.warning(f"Folder {item.get('title')} has no UID, skipping")
                return None
            
            # Generate filename
            if self.folder_config.uid_support:
                filename = uid
            else:
                filename = item.get("uri", "unknown")
            
            # Clean up filename
            filename = filename.replace("/", "_").replace("\\", "_")
            
            # Fetch folder settings
            status_settings, content_settings = await client.get(f"/api/folders/{uid}")
            
            if status_settings != 200:
                logger.error(f"Failed to fetch folder settings {uid}: {content_settings}")
                return None
            
            # Save folder settings
            settings_path = await self._save_json(content_settings, filename)
            
            # Fetch and save permissions if enabled
            if self.folder_config.include_permissions:
                status_permissions, content_permissions = await client.get(f"/api/folders/{uid}/permissions")
                
                if status_permissions == 200:
                    permissions_filename = f"{filename}_permissions"
                    await self._save_json(content_permissions, permissions_filename)
                else:
                    logger.warning(f"Failed to fetch folder permissions {uid}: {content_permissions}")
            
            return settings_path
            
        except Exception as e:
            logger.error(f"Failed to save folder {item.get('title')}: {e}")
            return None