"""
Restore users component.
"""

from typing import Any

from loguru import logger

from grafana_backup.v2.components.restore_base import BaseRestoreComponent, RestoreConfig


class UsersRestoreConfig(RestoreConfig):
    """Configuration for users restore."""
    overwrite: bool = False  # Whether to overwrite existing users
    default_password: str = "temp_password_123"  # Default password for restored users


class UsersRestoreComponent(BaseRestoreComponent):
    """Async users restore component."""
    
    @property
    def component_name(self) -> str:
        return "users"
    
    def __init__(self, config: UsersRestoreConfig, backup_dir, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.users_config = config
    
    async def restore_item(self, item: dict, client: Any) -> str | None:
        """Restore a single user."""
        try:
            # Clean up the user data for restore
            user_login = item.get("login")
            if not user_login:
                logger.warning("User has no login, skipping")
                return None
            
            restore_data = {
                "name": item.get("name", ""),
                "email": item.get("email", ""),
                "login": user_login,
                "password": self.users_config.default_password,
            }
            
            # Check if user already exists
            status, existing = await client.get(f"/api/users/lookup?loginOrEmail={user_login}")
            
            if status == 200 and existing and existing.get("id"):
                if self.users_config.overwrite:
                    # Update existing user
                    user_id = existing.get("id")
                    status, result = await client.put(
                        f"/api/users/{user_id}",
                        json=restore_data
                    )
                    if status == 200:
                        logger.info(f"Updated user: {user_login}")
                        return str(user_id)
                    else:
                        logger.error(f"Failed to update user {user_login}: {result}")
                        return None
                else:
                    logger.info(f"User {user_login} already exists, skipping")
                    return str(existing.get("id"))
            
            # Create new user
            status, result = await client.post(
                "/api/admin/users",
                json=restore_data
            )
            
            if status == 200:
                logger.info(f"Created user: {user_login}")
                user_id = result.get("id")
                
                # Restore user organizations if present
                orgs = item.get("orgs")
                if orgs:
                    await self._restore_organizations(orgs, user_id, client)
                
                return str(user_id)
            else:
                logger.error(f"Failed to create user {user_login}: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to restore user: {e}")
            return None
    
    async def _restore_organizations(self, orgs: list, user_id: str, client: Any):
        """Restore user organizations."""
        try:
            for org in orgs:
                org_name = org.get("name")
                role = org.get("role", "Viewer")
                
                # Try to find organization
                status, existing_orgs = await client.get("/api/orgs")
                if status == 200:
                    org_id = None
                    for existing_org in existing_orgs:
                        if existing_org.get("name") == org_name:
                            org_id = existing_org.get("id")
                            break
                    
                    if org_id:
                        # Add user to organization
                        status, result = await client.post(
                            f"/api/orgs/{org_id}/users",
                            json={"loginOrEmail": org_name, "role": role}
                        )
                        if status == 200:
                            logger.info(f"Added user to organization: {org_name}")
                        else:
                            logger.warning(f"Failed to add user to organization {org_name}: {result}")
                    else:
                        logger.warning(f"Organization {org_name} not found, skipping")
                        
        except Exception as e:
            logger.warning(f"Failed to restore user organizations: {e}")