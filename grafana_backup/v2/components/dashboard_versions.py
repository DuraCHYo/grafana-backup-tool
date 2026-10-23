"""
Modern async dashboard versions backup component.

Each dashboard's versions are stored under a per-dashboard subdirectory
``<component_dir>/<dashboard-uid>/<version>.dashboard_version``. This mirrors the
v1 layout (``dashboard_versions/<uid>/<version>.version``) so archives remain
restorable by the v1 tool as well.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .base import BaseComponent, ComponentConfig


class DashboardVersionsConfig(ComponentConfig):
    """Configuration for dashboard versions backup."""

    file_extension: str = "dashboard_version"
    search_limit: int = 5000


class DashboardVersionsComponent(BaseComponent):
    """Async dashboard versions backup component."""

    @property
    def component_name(self) -> str:
        return "dashboard-versions"

    @property
    def directory_name(self) -> str:
        # Preserve the legacy on-disk directory name used by v1 archives.
        return "dashboard_versions"

    def __init__(self, config: DashboardVersionsConfig, backup_dir: Path, timestamp: str):
        super().__init__(config, backup_dir, timestamp)
        self.versions_config = config

    async def fetch_data(self, client: Any) -> list[dict]:
        """Fetch all dashboards (versions are fetched per dashboard in save_item)."""
        dashboards: list[dict] = []
        page = 1
        limit = self.versions_config.search_limit

        while True:
            status, content = await client.get(
                "/api/search",
                params={"type": "dash-db", "limit": limit, "page": page},
            )
            if status != 200:
                logger.error(f"Failed to fetch dashboards for versions: {content}")
                break
            if not content:
                break
            dashboards.extend(content)
            if len(content) < limit:
                break
            page += 1

        # A dashboard must have a uid (newer Grafana) or a numeric id (older
        # Grafana) for its versions to be fetchable.
        dashboards = [d for d in dashboards if d.get("uid") or d.get("id")]
        logger.info(f"Found {len(dashboards)} dashboards to back up versions for")
        return dashboards

    async def save_item(self, item: dict, client: Any) -> str | None:
        """Fetch and save all versions for a single dashboard."""
        try:
            uid = item.get("uid")
            dashboard_id = item.get("id")
            if not uid and not dashboard_id:
                return None

            listed_via, versions = await self._fetch_versions_list(client, uid, dashboard_id)
            if versions is None:
                logger.error(f"Failed to fetch versions for dashboard {uid or dashboard_id}")
                return None

            if not versions:
                return None

            # Create per-dashboard directory.
            dashboard_dir = self.component_dir / str(uid or dashboard_id).replace("/", "_")
            dashboard_dir.mkdir(parents=True, exist_ok=True)

            saved = 0
            for version_meta in versions:
                version = version_meta.get("version")
                if version is None:
                    continue

                # Newer Grafana includes the full dashboard model in each entry
                # of the versions listing as ``data``; prefer that and only fall
                # back to per-version endpoints when it is missing.
                version_content = version_meta.get("data")
                if version_content is None:
                    version_content = await self._fetch_version_document(
                        client, uid, dashboard_id, version, listed_via
                    )
                if version_content is None:
                    logger.warning(
                        f"Failed to fetch dashboard {uid or dashboard_id} version {version}"
                    )
                    continue

                file_path = dashboard_dir / f"{version}.{self.config.file_extension}"
                import json

                import aiofiles

                async with aiofiles.open(file_path, "w") as f:
                    await f.write(
                        json.dumps(
                            version_content,
                            indent=4 if self.config.pretty_print else None,
                            ensure_ascii=False,
                        )
                    )
                saved += 1

            logger.debug(f"Saved {saved} versions for dashboard {uid or dashboard_id}")
            return str(dashboard_dir) if saved else None

        except Exception as e:
            logger.error(f"Failed to save dashboard versions for {item.get('title')}: {e}")
            return None

    @staticmethod
    def _parse_versions_envelope(content: Any) -> list[dict]:
        """Extract the version list from either API response shape.

        Older Grafana returns a bare list; newer Grafana (uid-based endpoint)
        returns an object such as ``{"versions": [...], "continueToken": ""}``.
        """
        if isinstance(content, list):
            return content
        if isinstance(content, dict) and "versions" in content:
            return content["versions"]
        return []

    async def _fetch_versions_list(
        self, client: Any, uid: str | None, dashboard_id: int | None
    ) -> tuple[str | None, list[dict] | None]:
        """Fetch the version list, preferring the newer uid-based endpoint.

        Returns ``(listed_via, versions)`` as path style used (``"uid"`` or
        ``"id"``), or ``(None, None)`` when both endpoints fail.
        """
        if uid:
            status, content = await client.get(f"/api/dashboards/uid/{uid}/versions")
            if status == 200:
                return "uid", self._parse_versions_envelope(content)
            logger.debug(f"uid versions endpoint unavailable for {uid} (status {status}), falling back")

        if dashboard_id:
            status, content = await client.get(
                f"/api/dashboards/id/{dashboard_id}/versions"
            )
            if status == 200:
                return "id", self._parse_versions_envelope(content)
            logger.debug(f"id versions endpoint unavailable for {dashboard_id} (status {status})")

        return None, None

    async def _fetch_version_document(
        self,
        client: Any,
        uid: str | None,
        dashboard_id: int | None,
        version: int,
        listed_via: str,
    ) -> dict | None:
        """Fetch a single version document with endpoint backwards compatibility.

        Old Grafana list responses contain no dashboard payload, so the
        per-version document must be queried separately. Prefer the endpoint
        style that successfully listed the versions (uid for Grafana >= 13,
        id for legacy), then fall back to the other style.
        """
        candidates = []
        if listed_via == "uid":
            if uid:
                candidates.append(f"/api/dashboards/uid/{uid}/versions/{version}")
            if dashboard_id:
                candidates.append(
                    f"/api/dashboards/id/{dashboard_id}/versions/{version}"
                )
        else:
            if dashboard_id:
                candidates.append(
                    f"/api/dashboards/id/{dashboard_id}/versions/{version}"
                )
            if uid:
                candidates.append(f"/api/dashboards/uid/{uid}/versions/{version}")

        for endpoint in candidates:
            status, content = await client.get(endpoint)
            if status == 200:
                return content
            logger.debug(f"{endpoint} unavailable (status {status})")
        return None
