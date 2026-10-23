import asyncio
import os
from pathlib import Path

import typer

app = typer.Typer(
    name="grafana-backup",
    help="grafana-backup — Grafana backup and restore utility.",
    no_args_is_help=True,
    add_completion=False,
)


def _resolve_backup_dir(config: str | None) -> Path:
    """Resolve the configured backup directory (falls back to ``_OUTPUT_``)."""
    try:
        from grafana_backup.v2.config import load_config

        return load_config(config).storage.backup_dir
    except Exception:
        return Path("_OUTPUT_")


@app.command("save")
def save_command(
    config: str | None = typer.Option(
        None,
        "--config",
        help="Override default configuration path.",
    ),
    components: str | None = typer.Option(
        None,
        "--components",
        help="Comma separated list of components.",
    ),
    no_archive: bool = typer.Option(
        False,
        "--no-archive",
        help="Skip archive creation.",
    ),
):
    """Create a Grafana backup."""
    from grafana_backup.v2.cli import run_backup

    asyncio.run(run_backup(components, False, config, no_archive))


@app.command("restore")
def restore_command(
    archive_file: str | None = typer.Argument(
        None,
        help="Backup archive to restore.",
    ),
    config: str | None = typer.Option(
        None,
        "--config",
        help="Override default configuration path.",
    ),
    components: str | None = typer.Option(
        None,
        "--components",
        help="Comma separated list of components.",
    ),
):
    """Restore Grafana from a backup archive."""
    from grafana_backup.v2.cli import run_restore

    # Get archive file
    archive = archive_file or os.getenv("ARCHIVE_FILE")

    if not archive:
        raise typer.BadParameter(
            "No archive file provided. Use: grafana-backup restore <file> or set $ARCHIVE_FILE."
        )

    # Resolve relative archive names against the configured backup directory.
    backup_dir = _resolve_backup_dir(config)
    if not os.path.exists(archive):
        backup_archive = os.path.join(str(backup_dir), archive)
        if os.path.exists(backup_archive):
            archive = backup_archive

    asyncio.run(run_restore(archive, components, False, config))


def main():
    app()


if __name__ == "__main__":
    main()
