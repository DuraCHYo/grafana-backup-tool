"""
Modern async dashboards backup component.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .base import BaseComponent, ComponentConfig


class DashboardConfig(ComponentConfig):
    """Configuration for dashboards backup."""
    include_versions: bool = False
    uid_support: bool = True
    slug_suffix: bool = False
    file_extension: str = "dashboard"


class DashboardsComponent(BaseComponent):
    """Async dashboards backup component."""
    
    @property
    def component_name(self) -> str:
        return "dashboards"
    
    def __init__(self, config: DashboardConfig, backup_dir: Path, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.dashboard_config = config
    
    async def fetch_data(self, client: Any) -> list[dict]:
        """Fetch all dashboards from Grafana."""
        dashboards = []
        page = 1
        limit = 5000
        
        while True:
            status, content = await client.get(
                "/api/search",
                params={"type": "dash-db", "limit": limit, "page": page}
            )
            
            if status != 200:
                logger.error(f"Failed to fetch dashboards: {content}")
                break
            
            if not content:
                break
            
            dashboards.extend(content)
            page += 1
            
            # Check if we got less than limit, means no more pages
            if len(content) < limit:
                break
        
        return dashboards
    
    async def save_item(self, item: dict, client: Any) -> str | None:
        """Save a single dashboard with its full details."""
        try:
            # Get dashboard UID for detailed fetch
            uid = item.get("uid")
            if not uid:
                logger.warning(f"Dashboard {item.get('title')} has no UID, skipping")
                return None
            
            # Fetch full dashboard details
            status, content = await client.get(f"/api/dashboards/uid/{uid}")
            
            if status != 200:
                logger.error(f"Failed to fetch dashboard {uid}: {content}")
                return None
            
            # Clean up dashboard data for backup
            dashboard_data = content.get("dashboard", {})
            dashboard_data["id"] = None  # Remove ID for restore
            
            # Generate filename
            filename = self._generate_filename(item, dashboard_data)
            
            # Save to file
            return await self._save_json(dashboard_data, filename)
            
        except Exception as e:
            logger.error(f"Failed to save dashboard {item.get('title')}: {e}")
            return None
    
    def _generate_filename(self, item: dict, dashboard_data: dict) -> str:
        """Generate filename for dashboard."""
        uid = item.get("uid", item.get("uri", "unknown"))
        
        if self.dashboard_config.slug_suffix:
            slug = dashboard_data.get("meta", {}).get("slug")
            if slug:
                uid = f"{uid}-{slug}"
        
        # Clean up filename
        return uid.replace("/", "_").replace("\\", "_")