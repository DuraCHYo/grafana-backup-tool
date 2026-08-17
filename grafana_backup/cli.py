import os
from pathlib import Path

import typer

from grafana_backup.constants import JSON_CONFIG_PATH, PKG_NAME
from grafana_backup.delete.delete import main as delete
from grafana_backup.grafanaSettings import main as conf
from grafana_backup.restore import main as restore
from grafana_backup.save.save import main as save
from grafana_backup.tools import main as tools

app = typer.Typer(
    name="grafana-backup",
    help=f"{PKG_NAME} — Grafana backup and restore utility.",
    no_args_is_help=False,
    add_completion=False,
)


def get_settings(config: str | None):
    """Load configuration using the same priority as the old CLI."""

    default_config = Path(__file__).parent / "conf" / "grafanaSettings.json"

    if config:
        return conf(config)

    if os.path.isfile(JSON_CONFIG_PATH):
        return conf(JSON_CONFIG_PATH)

    if default_config.is_file():
        return conf(str(default_config))

    return conf()


def build_args(
    config: str | None,
    components: str | None,
    no_archive: bool = False,
):
    """
    Build an args dict compatible with the existing functions.

    This allows us to migrate the CLI to Typer without rewriting
    save/restore/delete/tools internals.
    """

    return {
        "--config": config,
        "--components": components,
        "--no-archive": no_archive,
    }


@app.callback(invoke_without_command=True)
def cli(
    ctx: typer.Context,
    config: str | None = typer.Option(
        None,
        "--config",
        help="Override default configuration path.",
    ),
):
    """
    Grafana backup utility.

    With no command:
      RESTORE=true  -> restore mode
      otherwise     -> save mode
    """

    if ctx.invoked_subcommand is not None:
        return

    settings = get_settings(config)

    env_mode = os.getenv("RESTORE", "false").lower()

    if env_mode == "true":
        archive = os.getenv("ARCHIVE_FILE")

        if not archive:
            raise typer.BadParameter(
                "No archive file provided for restore mode. "
                "Use 'grafana-backup restore <file>' "
                "or set $ARCHIVE_FILE."
            )

        backup_dir = settings.get("BACKUP_DIR", "_OUTPUT_")

        if not os.path.exists(archive):
            backup_archive = os.path.join(backup_dir, archive)

            if os.path.exists(backup_archive):
                archive = backup_archive

        args = {
            "--config": config,
            "--components": None,
            "--no-archive": False,
            "<archive_file>": archive,
        }

        restore(args, settings)

    else:
        args = {
            "--config": config,
            "--components": None,
            "--no-archive": False,
        }

        save(args, settings)


@app.command("save")
def save_command(
    ctx: typer.Context,
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

    settings = get_settings(config)

    args = build_args(
        config=config,
        components=components,
        no_archive=no_archive,
    )

    save(args, settings)


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

    settings = get_settings(config)

    archive = archive_file or os.getenv("ARCHIVE_FILE")

    if not archive:
        raise typer.BadParameter(
            "No archive file provided. "
            "Use: grafana-backup restore <file> "
            "or set $ARCHIVE_FILE."
        )

    backup_dir = settings.get("BACKUP_DIR", "_OUTPUT_")

    if not os.path.exists(archive):
        backup_archive = os.path.join(backup_dir, archive)

        if os.path.exists(backup_archive):
            archive = backup_archive

    args = build_args(
        config=config,
        components=components,
    )

    args["<archive_file>"] = archive

    restore(args, settings)


@app.command("delete")
def delete_command(
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
    """Delete Grafana backup data."""

    settings = get_settings(config)

    args = build_args(
        config=config,
        components=components,
    )

    delete(args, settings)


@app.command("tools")
def tools_command(
    optional_command: str | None = typer.Argument(
        None,
        help="Optional tools command.",
    ),
    optional_argument: str | None = typer.Argument(
        None,
        help="Optional command argument.",
    ),
    config: str | None = typer.Option(
        None,
        "--config",
        help="Override default configuration path.",
    ),
):
    """Run backup utility tools."""

    settings = get_settings(config)

    args = {
        "--config": config,
        "<optional-command>": optional_command,
        "<optional-argument>": optional_argument,
    }

    tools(args, settings)


def main():
    app()
