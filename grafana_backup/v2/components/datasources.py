"""
Modern async datasources backup component.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .base import BaseComponent, ComponentConfig


class DatasourceConfig(ComponentConfig):
    """Configuration for datasources backup."""
    uid_support: bool = True
    file_extension: str = "datasource"


class DatasourcesComponent(BaseComponent):
    """Async datasources backup component."""
    
    @property
    def component_name(self) -> str:
        return "datasources"
    
    def __init__(self, config: DatasourceConfig, backup_dir: Path, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.datasource_config = config
    
    async def fetch_data(self, client: Any) -> list[dict]:
        """Fetch all datasources from Grafana."""
        status, content = await client.get("/api/datasources")
        
        if status != 200:
            logger.error(f"Failed to fetch datasources: {content}")
            return []
        
        if not content:
            return []
        
        logger.info(f"Found {len(content)} datasources")
        return content
    
    async def save_item(self, item: dict, client: Any) -> str | None:
        """Save a single datasource."""
        try:
            # Generate filename
            if self.datasource_config.uid_support and item.get("uid"):
                filename = item["uid"]
            else:
                filename = item.get("name", "unknown")
            
            # Clean up filename
            filename = filename.replace("/", "_").replace("\\", "_")
            
            # Save to file
            return await self._save_json(item, filename)
            
        except Exception as e:
            logger.error(f"Failed to save datasource {item.get('name')}: {e}")
            return None