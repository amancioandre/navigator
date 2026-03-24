"""Navigator CLI — Autonomous task orchestrator for Claude Code sessions."""

from typing import Annotated

import typer

from navigator import __version__

app = typer.Typer(
    name="navigator",
    help="Autonomous task orchestrator for Claude Code sessions.",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"navigator {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """Autonomous task orchestrator for Claude Code sessions."""


@app.command()
def register() -> None:
    """Register a new command."""
    typer.echo("register: not yet implemented")


@app.command(name="list")
def list_commands() -> None:
    """List all registered commands."""
    typer.echo("list: not yet implemented")


@app.command(name="exec")
def exec_command() -> None:
    """Execute a registered command."""
    typer.echo("exec: not yet implemented")


@app.command()
def schedule() -> None:
    """Schedule a command with a cron expression."""
    typer.echo("schedule: not yet implemented")


@app.command()
def watch() -> None:
    """Register a file watcher for a command."""
    typer.echo("watch: not yet implemented")


@app.command()
def chain() -> None:
    """Chain commands together."""
    typer.echo("chain: not yet implemented")


@app.command()
def logs() -> None:
    """View execution logs."""
    typer.echo("logs: not yet implemented")


@app.command()
def doctor() -> None:
    """Verify system health."""
    typer.echo("doctor: not yet implemented")
