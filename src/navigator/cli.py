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
def exec_command(
    name: Annotated[str, typer.Argument(help="Command name to execute")],
    timeout: Annotated[
        int | None,
        typer.Option("--timeout", help="Timeout in seconds (overrides config default)"),
    ] = None,
    retries: Annotated[
        int | None,
        typer.Option("--retries", help="Max retry attempts (overrides config default)"),
    ] = None,
) -> None:
    """Execute a registered command."""
    from navigator.config import load_config
    from navigator.db import get_command_by_name, get_connection, init_db
    from navigator.executor import execute_command

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
                f"[red]Command '{name}' is paused. "
                f"Run `navigator resume {name}` first.[/red]"
            )
            raise typer.Exit(code=1)

        try:
            result = execute_command(
                cmd, config, timeout_override=timeout, retries_override=retries
            )
        except FileNotFoundError as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(code=1) from None

        if result.stdout:
            console.print(result.stdout)

        if result.timed_out:
            console.print(
                f"[yellow]Command '{name}' timed out after "
                f"{timeout or config.default_timeout}s[/yellow]"
            )

        if result.attempts > 1:
            console.print(
                f"[dim]Completed after {result.attempts} attempt(s)[/dim]"
            )

        if result.returncode != 0:
            console.print(
                f"[red]Command '{name}' exited with code "
                f"{result.returncode}[/red]"
            )
            if result.stderr:
                console.print(f"[dim]{result.stderr}[/dim]")
            raise typer.Exit(code=result.returncode)

        if result.log_path:
            console.print(f"[dim]Log: {result.log_path}[/dim]")
    finally:
        conn.close()


@app.command()
def schedule(
    command: Annotated[
        str | None,
        typer.Argument(help="Command name to schedule"),
    ] = None,
    cron_expr: Annotated[
        str | None,
        typer.Option("--cron", help='Cron expression (e.g., "*/5 * * * *")'),
    ] = None,
    remove: Annotated[
        bool,
        typer.Option("--remove", help="Remove schedule for command"),
    ] = False,
    list_all: Annotated[
        bool,
        typer.Option("--list", help="List all scheduled commands"),
    ] = False,
) -> None:
    """Schedule a command with a cron expression."""
    from navigator.config import get_data_dir

    # --list mode: show all scheduled commands
    if list_all:
        from navigator.scheduler import CrontabManager

        manager = CrontabManager(lock_path=get_data_dir() / "crontab.lock")
        entries = manager.list_schedules()

        if not entries:
            console.print("[dim]No scheduled commands.[/dim]")
            return

        table = Table(title="Scheduled Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Schedule", style="green")
        table.add_column("Enabled", style="dim")

        for entry in entries:
            table.add_row(entry["command"], entry["schedule"], entry["enabled"])

        console.print(table)
        return

    # Validation: command name required for non-list operations
    if command is None:
        console.print("[red]Command name required.[/red]")
        raise typer.Exit(code=1)

    if cron_expr and remove:
        console.print("[red]Cannot use --cron and --remove together.[/red]")
        raise typer.Exit(code=1)

    if not cron_expr and not remove:
        console.print(
            "[red]Use --cron to schedule or --remove to unschedule.[/red]"
        )
        raise typer.Exit(code=1)

    # Validate command exists and is active
    from navigator.config import load_config
    from navigator.db import get_command_by_name, get_connection, init_db

    config = load_config()
    conn = get_connection(config.db_path)
    try:
        init_db(conn)
        cmd = get_command_by_name(conn, command)
        if cmd is None:
            console.print(f"[red]Command '{command}' not found.[/red]")
            raise typer.Exit(code=1)
        if cmd.status == "paused":
            console.print(
                f"[red]Command '{command}' is paused. "
                f"Run `navigator resume {command}` first.[/red]"
            )
            raise typer.Exit(code=1)
    finally:
        conn.close()

    from navigator.scheduler import CrontabManager

    manager = CrontabManager(lock_path=get_data_dir() / "crontab.lock")

    # --cron mode: schedule command
    if cron_expr:
        try:
            manager.schedule(command, cron_expr)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from None
        except FileNotFoundError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from None
        except TimeoutError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from None
        console.print(
            f"[green]Scheduled '{command}' with cron: {cron_expr}[/green]"
        )
        return

    # --remove mode: unschedule command
    if remove:
        removed = manager.unschedule(command)
        if removed:
            console.print(
                f"[green]Removed schedule for '{command}'[/green]"
            )
        else:
            console.print(
                f"[yellow]Command '{command}' was not scheduled.[/yellow]"
            )


@app.command()
def watch(
    command: Annotated[str | None, typer.Argument(help="Command name")] = None,
    path: Annotated[str | None, typer.Option("--path", help="Directory to watch")] = None,
    pattern: Annotated[
        str | None, typer.Option("--pattern", help="Glob pattern (e.g., '*.md')")
    ] = None,
    debounce: Annotated[
        int, typer.Option("--debounce", help="Debounce in milliseconds")
    ] = 500,
    ignore: Annotated[
        list[str] | None, typer.Option("--ignore", help="Ignore pattern")
    ] = None,
    active_hours: Annotated[
        str | None, typer.Option("--active-hours", help="HH:MM-HH:MM time window")
    ] = None,
    remove: Annotated[
        bool, typer.Option("--remove", help="Remove watcher")
    ] = False,
    list_all: Annotated[
        bool, typer.Option("--list", help="List all watchers")
    ] = False,
    start: Annotated[
        bool, typer.Option("--start", help="Start watcher daemon")
    ] = False,
) -> None:
    """Register a file watcher for a command."""
    # --list mode: show all watchers
    if list_all:
        from navigator.config import load_config
        from navigator.watcher import WatcherManager

        config = load_config()
        manager = WatcherManager(config)
        watchers = manager.list_watchers()

        if not watchers:
            console.print("[dim]No watchers registered.[/dim]")
            return

        table = Table(title="Registered Watchers")
        table.add_column("ID", style="dim")
        table.add_column("Command", style="cyan")
        table.add_column("Path", style="green")
        table.add_column("Pattern")
        table.add_column("Debounce")
        table.add_column("Active Hours")
        table.add_column("Status")

        for w in watchers:
            table.add_row(
                w.id[:8],
                w.command_name,
                str(w.watch_path),
                ", ".join(w.patterns),
                f"{w.debounce_ms}ms",
                w.active_hours or "(always)",
                w.status,
            )

        console.print(table)
        return

    # --start mode: run the watcher daemon
    if start:
        from navigator.config import load_config
        from navigator.watcher import run_daemon

        config = load_config()
        run_daemon(config)
        return

    # Validation: command name required for register/remove
    if command is None:
        console.print("[red]Command name required.[/red]")
        raise typer.Exit(code=1)

    if remove and path:
        console.print("[red]Cannot use --path and --remove together.[/red]")
        raise typer.Exit(code=1)

    # --remove mode
    if remove:
        from navigator.config import load_config
        from navigator.watcher import WatcherManager

        config = load_config()
        manager = WatcherManager(config)
        count = manager.remove_watchers_for_command(command)
        if count > 0:
            console.print(
                f"[green]Removed {count} watcher(s) for '{command}'[/green]"
            )
        else:
            console.print(
                f"[yellow]No watchers found for '{command}'.[/yellow]"
            )
        return

    # Register mode: --path is required
    if not path:
        console.print(
            "[red]Use --path to register a watcher or --remove to remove.[/red]"
        )
        raise typer.Exit(code=1)

    # Validate command exists and is active
    from navigator.config import load_config, resolve_path
    from navigator.db import get_command_by_name, get_connection, init_db

    config = load_config()
    conn = get_connection(config.db_path)
    try:
        init_db(conn)
        cmd = get_command_by_name(conn, command)
        if cmd is None:
            console.print(f"[red]Command '{command}' not found.[/red]")
            raise typer.Exit(code=1)
        if cmd.status == "paused":
            console.print(
                f"[red]Command '{command}' is paused. "
                f"Run `navigator resume {command}` first.[/red]"
            )
            raise typer.Exit(code=1)
    finally:
        conn.close()

    from navigator.watcher import WatcherManager

    abs_path = resolve_path(path)
    patterns = [pattern] if pattern else None
    ignore_list = ignore if ignore else None

    manager = WatcherManager(config)
    try:
        manager.register_watcher(
            command_name=command,
            watch_path=abs_path,
            patterns=patterns,
            ignore_patterns=ignore_list,
            debounce_ms=debounce,
            active_hours=active_hours,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from None

    console.print(
        f"[green]Registered watcher for '{command}' on {abs_path}[/green]"
    )


@app.command()
def chain() -> None:
    """Chain commands together."""
    typer.echo("chain: not yet implemented")


@app.command()
def logs(
    name: Annotated[str, typer.Argument(help="Command name")],
    count: Annotated[
        int, typer.Option("--count", "-n", help="Number of log entries to show")
    ] = 10,
    tail: Annotated[
        bool, typer.Option("--tail", help="Show full content of last log")
    ] = False,
) -> None:
    """View execution logs."""
    from navigator.config import load_config
    from navigator.execution_logger import list_execution_logs, read_log_content

    config = load_config()
    entries = list_execution_logs(config.log_dir, name, count=count)

    if not entries:
        console.print(f"[dim]No execution logs for '{name}'[/dim]")
        return

    if tail:
        content = read_log_content(entries[0].path)
        console.print(content)
        return

    table = Table(title=f"Execution Logs: {name}")
    table.add_column("Timestamp", style="dim")
    table.add_column("Exit Code")
    table.add_column("Duration", style="dim")
    table.add_column("Attempt", style="dim")

    for entry in entries:
        if entry.exit_code == 0:
            code_style = "green"
        elif entry.exit_code == 124:
            code_style = "yellow"
        else:
            code_style = "red"

        table.add_row(
            entry.timestamp,
            f"[{code_style}]{entry.exit_code}[/{code_style}]",
            entry.duration,
            str(entry.attempt),
        )

    console.print(table)


@app.command()
def doctor() -> None:
    """Verify system health."""
    typer.echo("doctor: not yet implemented")
