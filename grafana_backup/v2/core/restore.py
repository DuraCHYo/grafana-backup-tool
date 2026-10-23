"""
Restore coordinator for Grafana restore operations.
"""

import re
import shutil
import tarfile
from pathlib import Path
from typing import Any

from loguru import logger

from grafana_backup.v2.components.registry import REGISTRY
from grafana_backup.v2.config import Settings
from grafana_backup.v2.core.client import GrafanaClient, GrafanaConfig


class RestoreCoordinator:
    """Coordinator for restore operations across all components."""

    def __init__(
        self,
        settings: Settings,
        archive_file: str,
        components: list[str] | None = None,
    ):
        self.settings = settings
        self.archive_file = archive_file
        self.requested_components = components
        self.components: list[str] = []
        self.backup_dir = Path(settings.storage.backup_dir)

    def _resolve_components(self) -> list[str]:
        """Resolve components to restore, ordered so dependencies come first.

        When no explicit list is requested, all restore-capable components are
        used. When a subset is requested, its registry dependencies are still
        honoured (e.g. requesting dashboards restores folders first).
        """
        if not self.requested_components:
            return REGISTRY.restore_names()

        known = [c for c in self.requested_components if REGISTRY.get(c) is not None]
        for name in self.requested_components:
            if REGISTRY.get(name) is None:
                logger.warning(f"Unknown component '{name}', skipping")
        return REGISTRY.order_for_restore(known)

    async def run_restore(self) -> dict[str, Any]:
        """Run restore process for all components."""
        logger.info("Starting Grafana restore v2")

        # If the archive is not available locally, try remote storage (S3)
        await self._download_archive_if_missing()

        # Extract archive
        timestamp = await self._extract_archive()
        if not timestamp:
            logger.error("Failed to extract archive")
            return {"success": False, "error": "Failed to extract archive"}

        logger.info(f"Timestamp from archive: {timestamp}")

        self.components = self._resolve_components()
        logger.info(f"Components to restore (dependency order): {self.components}")

        # Create Grafana client
        grafana_config = GrafanaConfig(
            url=self.settings.grafana.url,
            token=self.settings.grafana.token,
            admin_user=self.settings.grafana.admin_user,
            admin_password=self.settings.grafana.admin_password,
            verify_ssl=self.settings.grafana.verify_ssl,
            timeout=self.settings.grafana.timeout,
        )
        client = GrafanaClient(grafana_config)

        # Restore each component
        results = {}
        try:
            for component_name in self.components:
                result = await self._restore_component(
                    component_name, client, self.backup_dir, timestamp
                )
                results[component_name] = result
        finally:
            await client.close()

        # Calculate total statistics
        total_restored = sum(r.get("restored", 0) for r in results.values())
        total_failed = sum(r.get("failed", 0) for r in results.values())

        final_result = {
            "timestamp": timestamp,
            "components": results,
            "total_components": len(self.components),
            "total_restored": total_restored,
            "total_failed": total_failed,
            "success": total_failed == 0,
        }

        logger.info(f"Restore completed: {final_result}")

        # Cleanup
        self._cleanup(timestamp)

        return final_result

    async def _download_archive_if_missing(self) -> None:
        """Download the archive from remote storage when it isn't local.

        Mirrors the documented "restore from S3" flow: pass just the archive
        file name and let the configured bucket provide it.
        """
        archive_path = Path(self.archive_file)
        if archive_path.exists():
            return

        from grafana_backup.v2.storage import get_storage

        try:
            storage = get_storage(self.settings)
        except Exception as e:
            logger.error(f"Failed to initialize remote storage: {e}")
            return

        if storage is None:
            return

        import asyncio

        target = self.backup_dir / archive_path.name
        try:
            downloaded = await asyncio.to_thread(
                storage.download, archive_path.name, target
            )
        except Exception as e:
            logger.error(f"Failed to download {archive_path.name} from {storage.name}: {e}")
            return

        if downloaded and Path(downloaded).exists():
            self.archive_file = str(downloaded)
            logger.info(f"Using archive downloaded from {storage.name}: {downloaded}")

    async def _extract_archive(self) -> str | None:
        """Extract archive and return timestamp."""
        archive_path = Path(self.archive_file)

        if not archive_path.exists():
            logger.error(f"Archive file not found: {self.archive_file}")
            return None

        try:
            # Create temporary directory for extraction (fresh, in case a
            # previous restore failed mid-move and left stale content behind)
            temp_dir = self.backup_dir / "temp_restore"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir(parents=True)

            # Extract archive
            logger.info(f"Extracting archive: {self.archive_file}")
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(temp_dir)

            # Check archive structure
            # v2 format: dashboards/2026-08-27-22-50/adw7rbb.dashboard
            # v1 format: dashboards/adw7rbb.dashboard

            # Detect timestamp-named subdirectories via a real timestamp regex
            # (uid-only subdirectories such as ``dash-host-overview`` also
            # contain digits/hyphens and must not be mistaken for one).
            timestamp_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}$")
            has_timestamp_dirs = False
            timestamp = None

            for d in temp_dir.iterdir():
                if d.is_dir():
                    for subdir in d.iterdir():
                        if subdir.is_dir() and timestamp_pattern.match(subdir.name):
                            has_timestamp_dirs = True
                            timestamp = subdir.name
                            break
                    if has_timestamp_dirs:
                        break

            if has_timestamp_dirs:
                # v2 format: move each <component>/<timestamp> pair as-is
                logger.info("Detected v2 archive format")
                for component_dir in sorted(temp_dir.iterdir()):
                    if not component_dir.is_dir():
                        continue
                    ts_subdir = component_dir / timestamp
                    target_component = self.backup_dir / component_dir.name
                    target_component.mkdir(parents=True, exist_ok=True)
                    if ts_subdir.is_dir():
                        # shutil.move into an existing directory nests the
                        # source inside it, so remove any stale destination
                        # and move the timestamp directory itself.
                        dest = target_component / timestamp
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.move(str(ts_subdir), str(dest))
                    else:
                        dest = target_component / timestamp
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.move(str(component_dir), str(dest))
            else:
                # v1 format: create timestamp directory structure
                logger.info("Detected v1 archive format")
                timestamp = self._generate_timestamp()

                for component_dir in temp_dir.iterdir():
                    if component_dir.is_dir():
                        target_dir = self.backup_dir / component_dir.name / timestamp
                        target_dir.parent.mkdir(parents=True, exist_ok=True)
                        if target_dir.exists():
                            # A generated timestamp should never collide, but a
                            # stale one would make shutil.move nest the source.
                            shutil.rmtree(target_dir)
                        shutil.move(str(component_dir), str(target_dir))

            # Cleanup temp directory
            shutil.rmtree(temp_dir)

            return timestamp or self._generate_timestamp()

        except Exception as e:
            logger.error(f"Failed to extract archive: {e}")
            return None

    def _generate_timestamp(self) -> str:
        """Generate timestamp in the same format as backup."""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d-%H-%M")

    async def _restore_component(
        self, component_name: str, client: GrafanaClient, backup_dir: Path, timestamp: str
    ) -> dict[str, Any]:
        """Restore a single component using the registry."""
        logger.info(f"Restoring {component_name}")

        component = REGISTRY.build_restore(component_name, backup_dir, timestamp)
        if component is None:
            logger.warning(f"Component {component_name} is not implemented for restore in v2")
            return {
                "component": component_name,
                "total": 0,
                "restored": 0,
                "failed": 0,
                "skipped": True,
            }

        return await component.restore(client)

    def _cleanup(self, timestamp: str):
        """Cleanup temporary files."""
        logger.info("Cleaning up temporary files")
        # Cleanup is done during extraction
