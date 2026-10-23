"""
Modern async team members backup component.

Team membership is a join between teams and users, so this component iterates
over all teams and saves each team's members. Filenames encode
``<userId>_<teamId>`` to match the v1 layout and avoid collisions.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .base import BaseComponent, ComponentConfig


class TeamMembersConfig(ComponentConfig):
    """Configuration for team members backup."""

    file_extension: str = "team_member"


class TeamMembersComponent(BaseComponent):
    """Async team members backup component."""

    @property
    def component_name(self) -> str:
        return "team-members"

    @property
    def directory_name(self) -> str:
        # Preserve the legacy on-disk directory name used by v1 archives.
        return "team_members"

    def __init__(self, config: TeamMembersConfig, backup_dir: Path, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.team_members_config = config

    async def fetch_data(self, client: Any) -> list[dict]:
        """Fetch all teams (members are fetched per team in save_item)."""
        status, content = await client.get("/api/teams/search", params={"perpage": 1000, "page": 1})

        if status != 200:
            logger.error(f"Failed to fetch teams for team-members: {content}")
            return []

        if not content:
            return []

        teams = content.get("teams", []) if isinstance(content, dict) else content
        teams = [t for t in teams if isinstance(t, dict) and t.get("id") is not None]
        logger.info(f"Found {len(teams)} teams to back up members for")
        return teams

    async def save_item(self, item: dict, client: Any) -> str | None:
        """Fetch and save all members of a single team."""
        try:
            team_id = item.get("id")
            if team_id is None:
                return None

            status, content = await client.get(f"/api/teams/{team_id}/members")
            if status != 200:
                logger.error(f"Failed to fetch members of team {team_id}: {content}")
                return None

            if not content:
                return None

            members = content if isinstance(content, list) else []
            if not members:
                return None

            saved = 0
            for member in members:
                user_id = member.get("userId")
                team_id_member = member.get("teamId", team_id)
                if user_id is None:
                    continue

                identifier = f"{user_id}_{team_id_member}"
                # Persist team name alongside membership so restore can resolve it.
                payload = dict(member)
                payload.setdefault("teamName", item.get("name"))
                if await self._save_json(payload, identifier):
                    saved += 1

            logger.debug(f"Saved {saved} members for team {item.get('name')}")
            return str(team_id) if saved else None

        except Exception as e:
            logger.error(f"Failed to save team members for {item.get('name')}: {e}")
            return None
