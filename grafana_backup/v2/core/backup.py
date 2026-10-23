"""
Main backup coordinator for Grafana backup v2.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from grafana_backup.v2.components import registry
from grafana_backup.v2.config import Settings
from grafana_backup.v2.core.client import GrafanaClient, GrafanaConfig

# Legacy aliases (v1-style and older v2 CLI names) mapped to the canonical
# dash-separated component names used by the registry. Unknown names are left
# untouched so callers get a clear "not available" warning instead of silence.
_API_ALIASES = {
    "alert_channels": "alert-channels",
    "alert_rules": "alert-rules",
    "contact_points": "contact-points",
    "dashboard_versions": "dashboard-versions",
    "library_elements": "library-elements",
    "team_members": "team-members",
    "notification_policy": "notification-policy",
}


class BackupCoordinator:
    """Coordinates the backup process for all components."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.stats: dict[str, Any] = {}

    async def run_backup(self, components: list[str] | None = None) -> dict[str, Any]:
        """
        Run backup for specified components or all if None.

        Returns statistics about the backup operation.
        """
        logger.info("Starting Grafana backup v2")

        # Initialize Grafana client
        grafana_config = GrafanaConfig(
            url=self.settings.grafana.url,
            token=self.settings.grafana.token,
            admin_user=self.settings.grafana.admin_user,
            admin_password=self.settings.grafana.admin_password,
            verify_ssl=self.settings.grafana.verify_ssl,
            timeout=self.settings.grafana.timeout,
        )

        client = GrafanaClient(grafana_config)

        try:
            # Prepare backup directory
            backup_dir = self.settings.storage.backup_dir
            timestamp = self._generate_timestamp()

            logger.info(f"Backup directory: {backup_dir}")
            logger.info(f"Timestamp: {timestamp}")

            # Select components to backup
            components_to_backup = self._select_components(components)
            logger.info(f"Components to backup: {components_to_backup}")

            # Run backup for each component
            all_stats = {}

            for component_name in components_to_backup:
                component_stats = await self._backup_component(
                    component_name, client, backup_dir, timestamp
                )
                all_stats[component_name] = component_stats

            # Create archive if enabled
            upload_stats = None
            if self.settings.storage.create_archive:
                archive_path = await self._create_archive(backup_dir, timestamp)
                upload_stats = await self._upload_archive(archive_path)

                # Cleanup temporary files (only once they are safely archived)
                self._cleanup_temp_files(backup_dir, timestamp)

            components_ok = all(stat.get("failed", 0) == 0 for stat in all_stats.values())
            upload_ok = not upload_stats or upload_stats.get("uploaded", False)
            self.stats = {
                "timestamp": timestamp,
                "components": all_stats,
                "total_components": len(components_to_backup),
                "upload": upload_stats,
                "success": components_ok and upload_ok,
            }

            logger.info(f"Backup completed: {self.stats}")
            return self.stats

        finally:
            await client.close()

    def _select_components(self, components: list[str] | None = None) -> list[str]:
        """Select components to backup.

        Explicitly requested names are normalized (legacy aliases and
        underscore spellings are mapped to canonical registry names). When
        nothing is requested, every component registered as backupable is used,
        in registry order (which encodes restore-order semantics too).
        """
        if components:
            requested = []
            for name in components:
                canonical = self._canonical_name(name)
                if canonical != name:
                    logger.debug(f"Component '{name}' normalized to '{canonical}'")
                requested.append(canonical)
            return requested

        # Return all backupable components from the registry
        return registry.REGISTRY.backup_names()

    @staticmethod
    def _canonical_name(name: str) -> str:
        """Map legacy/underscore component names to canonical registry names."""
        if name in registry.REGISTRY.names():
            return name
        alias = registry.REGISTRY.get(_API_ALIASES.get(name.replace("-", "_"), name))
        return alias.name if alias else name

    async def _backup_component(
        self, component_name: str, client: GrafanaClient, backup_dir: Path, timestamp: str
    ) -> dict[str, Any]:
        """Backup a single component."""
        logger.info(f"Backing up {component_name}")

        # Build the component from the shared registry. The registry is the
        # single source of truth for names/implementations, so a new component
        # becomes auto-discovered here without touching this coordinator.
        component = registry.REGISTRY.build_backup(component_name, backup_dir, timestamp)
        if component is None:
            logger.warning(f"Component {component_name} not implemented in v2 yet")
            return {
                "component": component_name,
                "total": 0,
                "saved": 0,
                "failed": 0,
                "skipped": True,
            }

        # Run backup
        stats = await component.backup(client)
        return stats

    def _generate_timestamp(self) -> str:
        """Generate timestamp for backup."""
        from datetime import datetime

        return datetime.now().strftime(self.settings.storage.timestamp_format)

    async def _create_archive(self, backup_dir: Path, timestamp: str) -> Path | None:
        """Create archive from backup files and return its path (or ``None``)."""
        import tarfile

        archive_file = backup_dir / f"{timestamp}.tgz"

        logger.info(f"Creating archive: {archive_file}")

        # Find all backup directories with timestamp
        backup_dirs = []
        for component_dir in backup_dir.iterdir():
            if component_dir.is_dir():
                timestamp_dir = component_dir / timestamp
                if timestamp_dir.exists() and timestamp_dir.is_dir():
                    backup_dirs.append((component_dir.name, timestamp_dir))

        if not backup_dirs:
            logger.warning("No backup directories found to archive")
            return None

        # Use synchronous file operations for tarfile (it doesn't support async)
        with tarfile.open(archive_file, "w:gz") as tar:
            for component_name, timestamp_dir in backup_dirs:
                # Add every file beneath the component's timestamp directory,
                # preserving nested layout (e.g. dashboard_versions stores
                # per-dashboard subdirectories) inside the archive.
                for file_path in sorted(timestamp_dir.rglob("*")):
                    if file_path.is_file():
                        relative = file_path.relative_to(timestamp_dir)
                        tar.add(file_path, arcname=f"{component_name}/{timestamp}/{relative}")

        logger.info("Archive created successfully")
        return archive_file

    async def _upload_archive(self, archive_path: Path | None) -> dict[str, Any] | None:
        """Upload the finished archive to the configured remote storage.

        Returns ``None`` when no provider is configured, otherwise a stats
        dictionary. Upload errors are reported (and make the backup fail) but
        never crash the process before local files are cleaned up.
        """
        if archive_path is None or not archive_path.exists():
            return None

        from grafana_backup.v2.storage import get_storage

        try:
            storage = get_storage(self.settings)
        except Exception as e:
            logger.error(f"Failed to initialize remote storage: {e}")
            return {"provider": "unknown", "uploaded": False, "error": str(e)}

        if storage is None:
            return None

        import asyncio

        try:
            key = await asyncio.to_thread(storage.upload, archive_path, archive_path.name)
            return {
                "provider": storage.name,
                "bucket": getattr(storage, "bucket", None),
                "key": key,
                "uploaded": True,
            }
        except Exception as e:
            logger.error(f"Failed to upload {archive_path.name} to {storage.name}: {e}")
            return {"provider": storage.name, "uploaded": False, "error": str(e)}

    def _cleanup_temp_files(self, backup_dir: Path, timestamp: str):
        """Clean up temporary backup files after archiving.

        Removes each ``<component>/<timestamp>`` directory (mirroring the v1
        behaviour) and then prunes component directories left empty.
        """
        import shutil

        for component_dir in backup_dir.iterdir():
            if not component_dir.is_dir():
                continue

            timestamp_dir = component_dir / timestamp
            if timestamp_dir.is_dir():
                try:
                    shutil.rmtree(timestamp_dir)
                    logger.debug(f"Cleaned up {timestamp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup {timestamp_dir}: {e}")

            # Remove empty parent directories
            if component_dir.is_dir() and not any(component_dir.iterdir()):
                try:
                    component_dir.rmdir()
                    logger.debug(f"Removed empty directory {component_dir}")
                except Exception as e:
                    logger.warning(f"Failed to remove empty directory {component_dir}: {e}")
