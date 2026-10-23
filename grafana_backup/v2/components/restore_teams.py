"""
Restore teams component.
"""

from typing import Any

from loguru import logger

from grafana_backup.v2.components.restore_base import BaseRestoreComponent, RestoreConfig


class TeamsRestoreConfig(RestoreConfig):
    """Configuration for teams restore."""
    overwrite: bool = False  # Whether to overwrite existing teams


class TeamsRestoreComponent(BaseRestoreComponent):
    """Async teams restore component."""
    
    @property
    def component_name(self) -> str:
        return "teams"
    
    def __init__(self, config: TeamsRestoreConfig, backup_dir, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.teams_config = config
    
    async def restore_item(self, item: dict, client: Any) -> str | None:
        """Restore a single team."""
        try:
            # Clean up the team data for restore
            restore_data = {
                "name": item.get("name"),
                "email": item.get("email"),
            }
            
            # Add optional fields if present
            if item.get("uid"):
                restore_data["uid"] = item["uid"]
            
            # Check if team already exists
            team_name = item.get("name")
            status, existing = await client.get(f"/api/teams/search?name={team_name}")
            
            if status == 200 and existing and existing.get("teams"):
                if self.teams_config.overwrite:
                    # Update existing team
                    team_id = existing["teams"][0].get("id")
                    status, result = await client.put(
                        f"/api/teams/{team_id}",
                        json=restore_data
                    )
                    if status == 200:
                        logger.info(f"Updated team: {team_name}")
                        return str(team_id)
                    else:
                        logger.error(f"Failed to update team {team_name}: {result}")
                        return None
                else:
                    logger.info(f"Team {team_name} already exists, skipping")
                    return str(existing["teams"][0].get("id"))
            
            # Create new team
            status, result = await client.post(
                "/api/teams",
                json=restore_data
            )
            
            if status == 200:
                logger.info(f"Created team: {team_name}")
                return str(result.get("id"))
            else:
                logger.error(f"Failed to create team {team_name}: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to restore team: {e}")
            return None