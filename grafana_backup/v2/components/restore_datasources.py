"""
Restore datasources component.
"""

from typing import Any

from loguru import logger

from grafana_backup.v2.components.restore_base import BaseRestoreComponent, RestoreConfig


class DatasourcesRestoreConfig(RestoreConfig):
    """Configuration for datasources restore."""
    overwrite: bool = False  # Whether to overwrite existing datasources


class DatasourcesRestoreComponent(BaseRestoreComponent):
    """Async datasources restore component."""
    
    @property
    def component_name(self) -> str:
        return "datasources"
    
    def __init__(self, config: DatasourcesRestoreConfig, backup_dir, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.datasource_config = config
    
    async def restore_item(self, item: dict, client: Any) -> str | None:
        """Restore a single datasource."""
        try:
            # Clean up the datasource data for restore
            # Remove fields that shouldn't be restored
            restore_data = {
                "name": item.get("name"),
                "type": item.get("type"),
                "url": item.get("url"),
                "access": item.get("access", "proxy"),
                "isDefault": item.get("isDefault", False),
                "jsonData": item.get("jsonData", {}),
                "secureJsonData": item.get("secureJsonData", {}),
            }
            
            # Check if datasource already exists
            status, existing = await client.get(f"/api/datasources/name/{restore_data['name']}")
            
            if status == 200 and existing:
                if self.datasource_config.overwrite:
                    # Update existing datasource
                    datasource_id = existing.get("id")
                    status, result = await client.put(
                        f"/api/datasources/{datasource_id}",
                        json=restore_data
                    )
                    if status == 200:
                        logger.info(f"Updated datasource: {restore_data['name']}")
                        return str(datasource_id)
                    else:
                        logger.error(f"Failed to update datasource {restore_data['name']}: {result}")
                        return None
                else:
                    logger.info(f"Datasource {restore_data['name']} already exists, skipping")
                    return str(existing.get("id"))
            
            # Create new datasource
            status, result = await client.post(
                "/api/datasources",
                json=restore_data
            )
            
            if status == 200:
                logger.info(f"Created datasource: {restore_data['name']}")
                return str(result.get("id"))
            else:
                logger.error(f"Failed to create datasource {restore_data['name']}: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to restore datasource: {e}")
            return None