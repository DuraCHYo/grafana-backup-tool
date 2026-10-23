"""
Modern async annotations backup component.
"""

import time
from pathlib import Path
from typing import Any

from loguru import logger

from .base import BaseComponent, ComponentConfig


class AnnotationsConfig(ComponentConfig):
    """Configuration for annotations backup."""

    retention_months: int = 13
    time_range_days: int = 31  # Time range per request in days
    file_extension: str = "annotation"


class AnnotationsComponent(BaseComponent):
    """Async annotations backup component."""

    @property
    def component_name(self) -> str:
        return "annotations"

    def __init__(self, config: AnnotationsConfig, backup_dir: Path, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.annotations_config = config

    async def fetch_data(self, client: Any) -> list[dict]:
        """Fetch all annotations from Grafana using time ranges."""
        annotations = []

        now = round(time.time() * 1000)
        one_month_in_ms = self.annotations_config.time_range_days * 24 * 60 * 60 * 1000
        max_retention = self.annotations_config.retention_months * one_month_in_ms

        ts_to = now
        ts_from = now - one_month_in_ms
        thirteen_months_retention = now - max_retention

        while ts_from > thirteen_months_retention:
            status, content = await client.get(
                "/api/annotations",
                params={
                    "type": "annotation",
                    "limit": 5000,
                    "from": str(ts_from),
                    "to": str(ts_to),
                },
            )

            if status == 200:
                annotations_batch = content
                if annotations_batch:
                    logger.info(f"Found {len(annotations_batch)} annotations for time range")
                    annotations.extend(annotations_batch)
                else:
                    logger.debug(f"No annotations found for time range {ts_from} - {ts_to}")
            else:
                logger.error(f"Failed to fetch annotations: {content}")

            ts_to = ts_from
            ts_from = ts_from - one_month_in_ms

        # Adjacent/large time ranges can return the same annotation more than
        # once; de-duplicate by id (keeping the first occurrence).
        unique: dict[int, dict] = {}
        for annotation in annotations:
            annotation_id = annotation.get("id")
            if annotation_id is None:
                continue
            unique.setdefault(annotation_id, annotation)

        logger.info(
            f"Total annotations found: {len(unique)} (deduplicated from {len(annotations)})"
        )
        return list(unique.values())

    async def save_item(self, item: dict, client: Any) -> str | None:
        """Save a single annotation."""
        try:
            # Generate filename from annotation ID
            annotation_id = item.get("id")
            if annotation_id is None:
                logger.warning("Annotation has no ID, skipping")
                return None

            filename = str(annotation_id)

            # Save to file
            return await self._save_json(item, filename)

        except Exception as e:
            logger.error(f"Failed to save annotation: {e}")
            return None
