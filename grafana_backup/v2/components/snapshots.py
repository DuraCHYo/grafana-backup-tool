"""
Modern async snapshots backup component.

Snapshots are fetched in two steps: a search returns lightweight entries with a
``key``, and each snapshot's full payload is fetched by key. v1 appended a random
suffix to filenames (snapshot names are not unique), which is preserved here.
"""

import random
import string
from pathlib import Path
from typing import Any

from loguru import logger

from .base import BaseComponent, ComponentConfig


class SnapshotsConfig(ComponentConfig):
    """Configuration for snapshots backup."""
    file_extension: str = "snapshot"
    random_suffix_length: int = 6


class SnapshotsComponent(BaseComponent):
    """Async snapshots backup component."""

    @property
    def component_name(self) -> str:
        return "snapshots"

    def __init__(self, config: SnapshotsConfig, backup_dir: Path, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.snapshots_config = config

    async def fetch_data(self, client: Any) -> list[dict]:
        """Fetch the list of snapshots (metadata only, includes ``key``).

        Endpoint compatibility: newer Grafana (>= 13) exposes the snapshot list
        under ``/api/dashboard/snapshots``; older versions use ``/api/snapshots``.
        Try both, old first (it still works anywhere it exists) and new second.
        """
        endpoints = ["/api/snapshots", "/api/dashboard/snapshots"]
        content = None
        for endpoint in endpoints:
            status, content = await client.get(endpoint)
            if status == 200:
                break
            logger.debug(f"{endpoint} unavailable (status {status}), trying next")

        if status != 200 or content is None:
            logger.error(f"Failed to fetch snapshots: {content}")
            return []

        if not content:
            return []

        snapshots = [
            s for s in content if isinstance(s, dict) and s.get("key")
        ]
        logger.info(f"Found {len(snapshots)} snapshots")
        return snapshots

    async def save_item(self, item: dict, client: Any) -> str | None:
        """Fetch and save a single snapshot's full payload by key."""
        try:
            key = item.get("key")
            if not key:
                logger.warning(f"Snapshot {item.get('name')} has no key, skipping")
                return None

            status, content = await client.get(f"/api/snapshots/{key}")
            if status != 200:
                logger.error(f"Failed to fetch snapshot {key}: {content}")
                return None

            suffix = "".join(
                random.choice(string.ascii_letters)
                for _ in range(self.snapshots_config.random_suffix_length)
            )
            base = str(item.get("name") or key).replace("/", "_").replace("\\", "_")
            filename = f"{base}_{suffix}"

            return await self._save_json(content, filename)

        except Exception as e:
            logger.error(f"Failed to save snapshot {item.get('name')}: {e}")
            return None
