"""
Restore team members component.

Membership documents encode ``userId``/``teamId``/``teamName``. To be portable
across instances the target team is resolved by name first, then by id, and the
user is resolved by login/email before being added.
"""

from typing import Any

from loguru import logger

from grafana_backup.v2.components.restore_base import BaseRestoreComponent, RestoreConfig


class TeamMembersRestoreConfig(RestoreConfig):
    """Configuration for team members restore."""

    overwrite: bool = False


class TeamMembersRestoreComponent(BaseRestoreComponent):
    """Async team members restore component."""

    @property
    def component_name(self) -> str:
        return "team-members"

    @property
    def directory_name(self) -> str:
        return "team_members"

    def __init__(self, config: TeamMembersRestoreConfig, backup_dir, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.team_members_config = config

    async def restore_item(self, item: dict, client: Any) -> str | None:
        """Restore a single team membership."""
        try:
            team_name = item.get("teamName")
            team_id = item.get("teamId")
            user_id = item.get("userId")
            user_login = item.get("login") or item.get("email")

            # Resolve target team id by name where possible.
            resolved_team_id = None
            if team_name:
                status, search = await client.get(
                    "/api/teams/search", params={"query": team_name, "perpage": 1000}
                )
                if status == 200 and isinstance(search, dict):
                    for team in search.get("teams", []):
                        if team.get("name") == team_name:
                            resolved_team_id = team.get("id")
                            break
            if resolved_team_id is None:
                resolved_team_id = team_id

            if resolved_team_id is None:
                logger.warning(f"Could not resolve team for membership {item}, skipping")
                return None

            # Resolve user id on the target instance.
            resolved_user_id = user_id
            if user_login:
                status, user = await client.get(f"/api/users/lookup?loginOrEmail={user_login}")
                if status == 200 and isinstance(user, dict) and user.get("id") is not None:
                    resolved_user_id = user.get("id")

            if resolved_user_id is None:
                logger.warning(f"Could not resolve user for membership {item}, skipping")
                return None

            status, result = await client.post(
                f"/api/teams/{resolved_team_id}/members",
                json={"userId": resolved_user_id},
            )
            if status == 200:
                logger.info(f"Added user {resolved_user_id} to team {resolved_team_id}")
                return str(resolved_team_id)

            # A 409/"already member" response is treated as success.
            message = str(result)
            if "already" in message.lower():
                logger.info(f"User {resolved_user_id} already in team {resolved_team_id}")
                return str(resolved_team_id)

            logger.error(f"Failed to add user to team {resolved_team_id}: {result}")
            return None

        except Exception as e:
            logger.error(f"Failed to restore team member: {e}")
            return None
