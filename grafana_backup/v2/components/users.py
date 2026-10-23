"""
Modern async users backup component.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .base import BaseComponent, ComponentConfig


class UsersConfig(ComponentConfig):
    """Configuration for users backup."""
    include_orgs: bool = True
    file_extension: str = "user"


class UsersComponent(BaseComponent):
    """Async users backup component."""
    
    @property
    def component_name(self) -> str:
        return "users"
    
    def __init__(self, config: UsersConfig, backup_dir: Path, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.users_config = config
    
    async def fetch_data(self, client: Any) -> list[dict]:
        """Fetch all users from Grafana."""
        status, content = await client.get("/api/users")
        
        if status != 200:
            logger.error(f"Failed to fetch users: {content}")
            return []
        
        if not content:
            return []
        
        logger.info(f"Found {len(content)} users")
        return content
    
    async def save_item(self, item: dict, client: Any) -> str | None:
        """Save a single user with org information."""
        try:
            user_id = item.get("id")
            if not user_id:
                logger.warning(f"User {item.get('login')} has no ID, skipping")
                return None
            
            # Fetch detailed user information
            status_user, content_user = await client.get(f"/api/users/{user_id}")
            
            if status_user == 200:
                item.update(content_user)
            
            # Fetch user organizations if enabled
            if self.users_config.include_orgs:
                status_orgs, content_orgs = await client.get(f"/api/users/{user_id}/orgs")
                
                if status_orgs == 200:
                    item.update({"orgs": content_orgs})
            
            # Generate filename from user ID
            filename = str(user_id)
            
            # Save to file
            return await self._save_json(item, filename)
            
        except Exception as e:
            logger.error(f"Failed to save user {item.get('login')}: {e}")
            return None