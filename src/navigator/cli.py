"""Navigator CLI — Autonomous task orchestrator for Claude Code sessions."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from navigator import __version__

app = typer.Typer(
    name="navigator",
    help="Autonomous task orchestrator for Claude Code sessions.",
    no_args_is_help=True,
)

console = Console()


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
def register(
    name: Annotated[
        str, typer.Argument(help="Command name (lowercase, hyphens allowed)")
    ],
    prompt: Annotated[
        str, typer.Option("--prompt", "-p", help="Claude Code prompt")
    ],
    environment: Annotated[
        str | None,
        typer.Option("--environment", "-e", help="Working directory"),
    ] = None,
    secrets: Annotated[
        str | None,
        typer.Option("--secrets", "-s", help="Path to secrets file"),
    ] = None,
    allowed_tools: Annotated[
        str | None,
        typer.Option("--allowed-tools", "-t", help="Comma-separated tools"),
    ] = None,
) -> None:
    """Register a new command."""
    from navigator.config import load_config, resolve_path
    from navigator.db import get_connection, init_db, insert_command
    from navigator.models import Command

    config = load_config()
    env_path = resolve_path(environment) if environment else resolve_path(Path.cwd())
    sec_path = resolve_path(secrets) if secrets else None
    tools = [t.strip() for t in allowed_tools.split(",")] if allowed_tools else []

    conn = get_connection(config.db_path)
    try:
        init_db(conn)
        try:
            cmd = Command(
                name=name,
                prompt=prompt,
                environment=env_path,
                secrets=sec_path,
                allowed_tools=tools,
            )
        except Exception:
            console.print(f"[red]Invalid command name '{name}'[/red]")
            raise typer.Exit(code=1) from None

        try:
            insert_command(conn, cmd)
        except sqlite3.IntegrityError:
            console.print(f"[red]Command '{name}' already exists.[/red]")
            raise typer.Exit(code=1) from None

        console.print(f"[green]Registered command '{name}'[/green]")
    finally:
        conn.close()


@app.command(name="list")
def list_commands(
    namespace: Annotated[
        str | None,
        typer.Option("--namespace", "-n", help="Filter by namespace"),
    ] = None,
    sort_date: Annotated[
        bool,
        typer.Option("--sort-date", help="Sort by creation date"),
    ] = False,
) -> None:
    """List all registered commands."""
    from navigator.config import load_config
    from navigator.db import get_all_commands, get_connection, init_db

    config = load_config()
    conn = get_connection(config.db_path)
    try:
        init_db(conn)
        commands = get_all_commands(conn, namespace=namespace, sort_by_created=sort_date)
        if not commands:
            console.print("[dim]No commands registered.[/dim]")
            return

        table = Table(title="Registered Commands")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Namespace", style="dim")
        table.add_column("Environment", style="dim")
        table.add_column("Created", style="dim")

        for cmd in commands:
            status_style = "green" if cmd.status == "active" else "yellow"
            table.add_row(
                cmd.name,
                f"[{status_style}]{cmd.status}[/{status_style}]",
                cmd.namespace,
                str(cmd.environment),
                cmd.created_at,
            )

        console.print(table)
    finally:
        conn.close()


@app.command()
def show(
    name: Annotated[str, typer.Argument(help="Command name to show")],
) -> None:
    """Show full details of a registered command."""
    from navigator.config import load_config
    from navigator.db import get_command_by_name, get_connection, init_db

    config = load_config()
    conn = get_connection(config.db_path)
    try:
        init_db(conn)
        cmd = get_command_by_name(conn, name)
        if cmd is None:
            console.print(f"[red]Command '{name}' not found.[/red]")
            raise typer.Exit(code=1)

        table = Table(title=f"Command: {cmd.name}", show_header=False)
        table.add_column("Field")
        table.add_column("Value")

        tools_str = ", ".join(cmd.allowed_tools) if cmd.allowed_tools else "(none)"
        secrets_str = str(cmd.secrets) if cmd.secrets else "(none)"

        table.add_row("ID", cmd.id)
        table.add_row("Name", cmd.name)
        table.add_row("Prompt", cmd.prompt)
        table.add_row("Environment", str(cmd.environment))
        table.add_row("Secrets", secrets_str)
        table.add_row("Allowed Tools", tools_str)
        table.add_row("Namespace", cmd.namespace)
        table.add_row("Status", cmd.status)
        table.add_row("Created", cmd.created_at)
        table.add_row("Updated", cmd.updated_at)

        console.print(table)
    finally:
        conn.close()


@app.command()
def update(
    name: Annotated[
        str, typer.Argument(help="Command name to update")
    ],
    prompt: Annotated[
        str | None,
        typer.Option("--prompt", "-p", help="New prompt"),
    ] = None,
    environment: Annotated[
        str | None,
        typer.Option("--environment", "-e", help="New working directory"),
    ] = None,
    secrets: Annotated[
        str | None,
        typer.Option("--secrets", "-s", help="New secrets path"),
    ] = None,
    allowed_tools: Annotated[
        str | None,
        typer.Option("--allowed-tools", "-t", help="New comma-separated tools"),
    ] = None,
) -> None:
    """Update fields of a registered command."""
    from navigator.config import load_config, resolve_path
    from navigator.db import get_connection, init_db, update_command

    fields: dict[str, object] = {}
    if prompt is not None:
        fields["prompt"] = prompt
    if environment is not None:
        fields["environment"] = str(resolve_path(environment))
    if secrets is not None:
        fields["secrets"] = str(resolve_path(secrets))
    if allowed_tools is not None:
        fields["allowed_tools"] = [
            t.strip() for t in allowed_tools.split(",")
        ]

    if not fields:
        console.print(
            "[yellow]No fields to update. "
            "Use --prompt, --environment, --secrets, "
            "or --allowed-tools.[/yellow]"
        )
        return

    config = load_config()
    conn = get_connection(config.db_path)
    try:
        init_db(conn)
        rows = update_command(conn, name, **fields)
        if rows == 0:
            console.print(f"[red]Command '{name}' not found.[/red]")
            raise typer.Exit(code=1)
        console.print(f"[green]Updated command '{name}'[/green]")
    finally:
        conn.close()


@app.command()
def delete(
    name: Annotated[
        str, typer.Argument(help="Command name to delete")
    ],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation"),
    ] = False,
) -> None:
    """Delete a registered command."""
    if not force:
        typer.confirm(f"Delete command '{name}'?", abort=True)

    from navigator.config import load_config
    from navigator.db import delete_command, get_connection, init_db

    config = load_config()
    conn = get_connection(config.db_path)
    try:
        init_db(conn)
        rows = delete_command(conn, name)
        if rows == 0:
            console.print(f"[red]Command '{name}' not found.[/red]")
            raise typer.Exit(code=1)
        console.print(f"[green]Deleted command '{name}'[/green]")
    finally:
        conn.close()


@app.command()
def pause(
    name: Annotated[
        str, typer.Argument(help="Command name to pause")
    ],
) -> None:
    """Pause a registered command."""
    from navigator.config import load_config
    from navigator.db import (
        get_command_by_name,
        get_connection,
        init_db,
        update_command,
    )

    config = load_config()
    conn = get_connection(config.db_path)
    try:
        init_db(conn)
        cmd = get_command_by_name(conn, name)
        if cmd is None:
            console.print(f"[red]Command '{name}' not found.[/red]")
            raise typer.Exit(code=1)
        if cmd.status == "paused":
            console.print(
                f"[yellow]Command '{name}' is already paused.[/yellow]"
            )
            return
        update_command(conn, name, status="paused")
        console.print(f"[green]Paused command '{name}'[/green]")
    finally:
        conn.close()


@app.command()
def resume(
    name: Annotated[
        str, typer.Argument(help="Command name to resume")
    ],
) -> None:
    """Resume a paused command."""
    from navigator.config import load_config
    from navigator.db import (
        get_command_by_name,
        get_connection,
        init_db,
        update_command,
    )

    config = load_config()
    conn = get_connection(config.db_path)
    try:
        init_db(conn)
        cmd = get_command_by_name(conn, name)
        if cmd is None:
            console.print(f"[red]Command '{name}' not found.[/red]")
            raise typer.Exit(code=1)
        if cmd.status == "active":
            console.print(
                f"[yellow]Command '{name}' is already active.[/yellow]"
            )
            return
        update_command(conn, name, status="active")
        console.print(f"[green]Resumed command '{name}'[/green]")
    finally:
        conn.close()


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
