"""
Modern async library elements backup component.

Library elements (a.k.a. library panels) are stored in the Grafana database and
referenced by dashboards. Backing them up *before* dashboards allows the restore
coordinator to recreate referenced panels first (see registry ``depends_on``).
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .base import BaseComponent, ComponentConfig


class LibraryElementsConfig(ComponentConfig):
    """Configuration for library elements backup."""
    file_extension: str = "library_element"
    page_size: int = 100


class LibraryElementsComponent(BaseComponent):
    """Async library elements backup component."""

    @property
    def component_name(self) -> str:
        return "library-elements"

    def __init__(self, config: LibraryElementsConfig, backup_dir: Path, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.library_config = config

    async def fetch_data(self, client: Any) -> list[dict]:
        """Fetch all library elements, following pagination."""
        elements: list[dict] = []
        page = 1
        limit = self.library_config.page_size

        while True:
            status, content = await client.get(
                "/api/library-elements",
                params={"perPage": limit, "page": page},
            )

            if status != 200:
                logger.error(f"Failed to fetch library elements: {content}")
                break

            if not content:
                break

            result = content.get("result", {}) if isinstance(content, dict) else {}
            batch = result.get("elements", []) if isinstance(result, dict) else []

            if not batch:
                break

            elements.extend(batch)

            total = result.get("totalCount")
            if total is not None and len(elements) >= total:
                break
            if len(batch) < limit:
                break

            page += 1

        logger.info(f"Found {len(elements)} library elements")
        return elements

    async def save_item(self, item: dict, client: Any) -> str | None:
        """Save a single library element."""
        try:
            identifier = item.get("uid") or item.get("id")
            if not identifier:
                logger.warning(f"Library element {item.get('name')} has no uid/id, skipping")
                return None

            # v1 uses either the element uid or its numeric id, slugified.
            filename = str(identifier).replace("/", "_").replace("\\", "_")
            return await self._save_json(item, filename)

        except Exception as e:
            logger.error(f"Failed to save library element {item.get('name')}: {e}")
            return None
