"""
Simple CLI for testing Grafana backup v2.
"""

import asyncio
import os

import typer
from rich.console import Console
from rich.table import Table

from grafana_backup.v2.config import load_config
from grafana_backup.v2.core import BackupCoordinator, RestoreCoordinator
from grafana_backup.v2.utils import setup_logging

app = typer.Typer(
    name="grafana-backup-v2",
    help="Grafana Backup Tool v2 - Modern async implementation",
    no_args_is_help=True,
)

console = Console()


async def run_backup(
    components: str | None = None,
    debug: bool = False,
    config: str | None = None,
    no_archive: bool = False,
):
    """Run Grafana backup using v2 architecture."""

    # Setup logging (LOG_LEVEL env is used by Docker/Helm and `make logs`)
    log_level = "DEBUG" if debug else os.getenv("LOG_LEVEL", "INFO").upper()
    setup_logging(log_level, debug)

    # Load settings
    try:
        settings = load_config(config)
    except Exception as e:
        console.print(f"[red]Failed to load settings: {e}[/red]")
        raise typer.Exit(1)

    if no_archive:
        settings.storage.create_archive = False

    # Run backup
    coordinator = BackupCoordinator(settings)

    component_list = components.split(",") if components else None

    try:
        stats = await coordinator.run_backup(component_list)

        # Display results
        _display_results(stats)

        if not stats.get("success"):
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Backup failed: {e}[/red]")
        raise typer.Exit(1)


async def run_restore(
    archive_file: str,
    components: str | None = None,
    debug: bool = False,
    config: str | None = None,
):
    """Run Grafana restore using v2 architecture."""

    # Setup logging (LOG_LEVEL env is used by Docker/Helm and `make logs`)
    log_level = "DEBUG" if debug else os.getenv("LOG_LEVEL", "INFO").upper()
    setup_logging(log_level, debug)

    # Load settings
    try:
        settings = load_config(config)
    except Exception as e:
        console.print(f"[red]Failed to load settings: {e}[/red]")
        raise typer.Exit(1)

    component_list = components.split(",") if components else None

    # Run restore
    coordinator = RestoreCoordinator(settings, archive_file, component_list)

    try:
        stats = await coordinator.run_restore()

        # Display results (the CLI owns presentation; the coordinator is silent)
        _display_restore_results(stats)

        if not stats.get("success"):
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Restore failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def save(
    components: str = typer.Option(
        None, "--components", help="Components to backup (comma-separated)"
    ),
    config: str = typer.Option(None, "--config", help="Configuration file path"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
):
    """Run Grafana backup using v2 architecture."""

    # Run backup
    asyncio.run(run_backup(components, debug, config))


@app.command()
def restore(
    archive_file: str = typer.Argument(..., help="Backup archive file to restore"),
    components: str = typer.Option(
        None, "--components", help="Components to restore (comma-separated)"
    ),
    config: str = typer.Option(None, "--config", help="Configuration file path"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
):
    """Run Grafana restore using v2 architecture."""

    # Run restore
    asyncio.run(run_restore(archive_file, components, debug, config))


def _display_results(stats: dict):
    """Display backup results in a nice table."""
    table = Table(title="Backup Results")
    table.add_column("Component", style="cyan")
    table.add_column("Total", justify="right", style="green")
    table.add_column("Saved", justify="right", style="green")
    table.add_column("Failed", justify="right", style="red")
    table.add_column("Status", style="bold")

    for component_name, component_stats in stats.get("components", {}).items():
        if component_stats.get("skipped"):
            status = "[yellow]Skipped[/yellow]"
        elif component_stats.get("failed", 0) == 0:
            status = "[green]Success[/green]"
        else:
            status = "[red]Failed[/red]"

        table.add_row(
            component_name,
            str(component_stats.get("total", 0)),
            str(component_stats.get("saved", 0)),
            str(component_stats.get("failed", 0)),
            status,
        )

    console.print(table)

    # Remote storage summary (S3 et al.)
    upload = stats.get("upload")
    if upload:
        if upload.get("uploaded"):
            console.print(
                f"[green]☁ Uploaded to {upload['provider']}://"
                f"{upload.get('bucket', '')}/{upload.get('key', '')}[/green]"
            )
        else:
            console.print(
                f"[red]☁ Upload to {upload.get('provider')} failed: "
                f"{upload.get('error', 'unknown error')}[/red]"
            )

    # Overall status
    if stats.get("success"):
        console.print("[green]✓ Backup completed successfully[/green]")
    else:
        console.print("[red]✗ Backup completed with errors[/red]")


def _display_restore_results(stats: dict):
    """Display restore results in a nice table."""
    table = Table(title="Restore Results")
    table.add_column("Component", style="cyan")
    table.add_column("Total", justify="right", style="magenta")
    table.add_column("Restored", justify="right", style="green")
    table.add_column("Failed", justify="right", style="red")
    table.add_column("Status", style="bold")

    for component_name, component_stats in stats.get("components", {}).items():
        if component_stats.get("skipped"):
            status = "[yellow]Skipped[/yellow]"
        elif component_stats.get("failed", 0) == 0:
            status = "[green]Success[/green]"
        else:
            status = "[red]Failed[/red]"

        table.add_row(
            component_name,
            str(component_stats.get("total", 0)),
            str(component_stats.get("restored", 0)),
            str(component_stats.get("failed", 0)),
            status,
        )

    console.print(table)

    # Overall status
    if stats.get("success"):
        console.print("[green]✓ Restore completed successfully[/green]")
    else:
        console.print("[red]✗ Restore completed with errors[/red]")


def main():
    app()
