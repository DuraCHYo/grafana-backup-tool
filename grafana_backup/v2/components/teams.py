"""
Modern async teams backup component.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .base import BaseComponent, ComponentConfig


class TeamsConfig(ComponentConfig):
    """Configuration for teams backup."""
    uid_support: bool = True
    file_extension: str = "team"


class TeamsComponent(BaseComponent):
    """Async teams backup component."""
    
    @property
    def component_name(self) -> str:
        return "teams"
    
    def __init__(self, config: TeamsConfig, backup_dir: Path, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.teams_config = config
    
    async def fetch_data(self, client: Any) -> list[dict]:
        """Fetch all teams from Grafana."""
        status, content = await client.get(
            "/api/teams/search",
            params={"perPage": 5000}
        )
        
        if status != 200:
            logger.error(f"Failed to fetch teams: {content}")
            return []
        
        teams = content.get("teams", [])
        if not teams:
            return []
        
        logger.info(f"Found {len(teams)} teams")
        return teams
    
    async def save_item(self, item: dict, client: Any) -> str | None:
        """Save a single team."""
        try:
            # Generate filename from UID or ID
            if self.teams_config.uid_support and item.get("uid"):
                filename = item["uid"]
            else:
                filename = str(item.get("id", "unknown"))
            
            # Clean up filename
            filename = filename.replace("/", "_").replace("\\", "_")
            
            # Save to file
            return await self._save_json(item, filename)
            
        except Exception as e:
            logger.error(f"Failed to save team {item.get('name')}: {e}")
            return None