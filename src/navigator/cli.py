"""Navigator CLI — Autonomous task orchestrator for Claude Code sessions."""

from __future__ import annotations

import subprocess
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

namespace_app = typer.Typer(
    name="namespace",
    help="Manage namespaces.",
    no_args_is_help=True,
)
app.add_typer(namespace_app)


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
    output: Annotated[
        str | None,
        typer.Option("--output", help="Output format: text or json"),
    ] = None,
) -> None:
    """Autonomous task orchestrator for Claude Code sessions."""
    import navigator.output as nav_output

    nav_output.output_format = output or "text"


# --- Namespace subcommands ---


@namespace_app.command()
def create(
    name: Annotated[
        str, typer.Argument(help="Namespace name (lowercase, hyphens allowed)")
    ],
    description: Annotated[
        str | None,
        typer.Option("--description", "-d", help="Namespace description"),
    ] = None,
) -> None:
    """Create a new namespace."""
    from navigator.config import load_config
    from navigator.db import get_connection, get_namespace_by_name, init_db, insert_namespace
    from navigator.models import Namespace

    config = load_config()
    conn = get_connection(config.db_path)
    try:
        init_db(conn)
        if get_namespace_by_name(conn, name) is not None:
            console.print(f"[red]Namespace '{name}' already exists.[/red]")
            raise typer.Exit(code=1)

        try:
            ns = Namespace(name=name, description=description)
        except Exception:
            console.print(f"[red]Invalid namespace name '{name}'[/red]")
            raise typer.Exit(code=1) from None

        insert_namespace(conn, ns)
        console.print(f"[green]Created namespace '{name}'[/green]")
    finally:
        conn.close()


@namespace_app.command(name="list")
def list_namespaces() -> None:
    """List all namespaces with command counts."""
    from navigator.config import load_config
    from navigator.db import get_all_commands, get_all_namespaces, get_connection, init_db

    config = load_config()
    conn = get_connection(config.db_path)
    try:
        init_db(conn)
        namespaces = get_all_namespaces(conn)

        from navigator.output import is_json, json_response

        if is_json():
            ns_data = [
                {
                    "name": ns.name,
                    "description": ns.description,
                    "created_at": ns.created_at,
                    "command_count": len(get_all_commands(conn, namespace=ns.name)),
                }
                for ns in namespaces
            ]
            typer.echo(json_response("ok", {"namespaces": ns_data}))
            return

        if not namespaces:
            console.print("[dim]No namespaces found.[/dim]")
            return

        table = Table(title="Namespaces")
        table.add_column("Name", style="cyan")
        table.add_column("Commands")
        table.add_column("Description", style="dim")
        table.add_column("Created", style="dim")

        for ns in namespaces:
            cmds = get_all_commands(conn, namespace=ns.name)
            table.add_row(
                ns.name,
                str(len(cmds)),
                ns.description or "",
                ns.created_at,
            )

        console.print(table)
    finally:
        conn.close()


@namespace_app.command(name="delete")
def delete_namespace_cmd(
    name: Annotated[
        str, typer.Argument(help="Namespace name to delete")
    ],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Force delete even if commands exist"),
    ] = False,
) -> None:
    """Delete a namespace."""
    if name == "default":
        console.print("[red]Cannot delete the 'default' namespace.[/red]")
        raise typer.Exit(code=1)

    from navigator.config import load_config
    from navigator.db import delete_namespace, get_connection, init_db

    config = load_config()
    conn = get_connection(config.db_path)
    try:
        init_db(conn)
        try:
            rows = delete_namespace(conn, name, force=force)
        except ValueError as exc:
            console.print(f"[red]{exc}. Use --force to delete anyway.[/red]")
            raise typer.Exit(code=1) from None

        if rows == 0:
            console.print(f"[red]Namespace '{name}' not found.[/red]")
            raise typer.Exit(code=1)

        console.print(f"[green]Deleted namespace '{name}'[/green]")
    finally:
        conn.close()


# --- Command subcommands ---


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
    namespace: Annotated[
        str | None,
        typer.Option("--namespace", "-n", help="Namespace for the command"),
    ] = None,
) -> None:
    """Register a new command."""
    from navigator.config import load_config, resolve_path
    from navigator.db import get_connection, get_namespace_by_name, init_db, insert_command
    from navigator.models import Command
    from navigator.namespace import namespace_secrets_path

    ns = namespace or "default"
    config = load_config()
    env_path = resolve_path(environment) if environment else resolve_path(Path.cwd())
    tools = [t.strip() for t in allowed_tools.split(",")] if allowed_tools else []

    conn = get_connection(config.db_path)
    try:
        init_db(conn)

        # Validate namespace exists
        if get_namespace_by_name(conn, ns) is None:
            console.print(f"[red]Namespace '{ns}' not found.[/red]")
            raise typer.Exit(code=1)

        # Auto-resolve secrets path for non-default namespaces when not explicitly provided
        if secrets:
            sec_path = resolve_path(secrets)
        elif ns != "default":
            sec_path = namespace_secrets_path(ns)
        else:
            sec_path = None

        try:
            cmd = Command(
                name=name,
                prompt=prompt,
                environment=env_path,
                secrets=sec_path,
                allowed_tools=tools,
                namespace=ns,
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

        from navigator.output import is_json, json_response

        if is_json():
            cmd_data = [
                {
                    "name": c.name,
                    "status": c.status,
                    "namespace": c.namespace,
                    "environment": str(c.environment),
                    "created_at": c.created_at,
                }
                for c in commands
            ]
            typer.echo(json_response("ok", {"commands": cmd_data}))
            return

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
    from navigator.namespace import parse_qualified_name

    try:
        parsed_ns, bare_name = parse_qualified_name(name)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from None

    config = load_config()
    conn = get_connection(config.db_path)
    try:
        init_db(conn)

        from navigator.output import is_json, json_response

        cmd = get_command_by_name(conn, bare_name)
        if cmd is None:
            if is_json():
                typer.echo(json_response("error", message=f"Command '{bare_name}' not found."))
                raise typer.Exit(code=1)
            console.print(f"[red]Command '{bare_name}' not found.[/red]")
            raise typer.Exit(code=1)

        if cmd.namespace != parsed_ns:
            if is_json():
                typer.echo(json_response("error", message=f"Command '{bare_name}' is in namespace '{cmd.namespace}', not '{parsed_ns}'."))
                raise typer.Exit(code=1)
            console.print(
                f"[red]Command '{bare_name}' is in namespace '{cmd.namespace}', "
                f"not '{parsed_ns}'.[/red]"
            )
            raise typer.Exit(code=1)

        if is_json():
            typer.echo(json_response("ok", cmd.model_dump(mode="json")))
            return

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
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show what would execute without running"),
    ] = False,
) -> None:
    """Execute a registered command."""
    from navigator.config import load_config
    from navigator.db import get_command_by_name, get_connection, init_db
    from navigator.executor import execute_command
    from navigator.namespace import parse_qualified_name

    try:
        parsed_ns, bare_name = parse_qualified_name(name)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from None

    config = load_config()
    conn = get_connection(config.db_path)
    try:
        init_db(conn)
        cmd = get_command_by_name(conn, bare_name)
        if cmd is None:
            console.print(f"[red]Command '{bare_name}' not found.[/red]")
            raise typer.Exit(code=1)

        if cmd.namespace != parsed_ns:
            console.print(
                f"[red]Command '{bare_name}' is in namespace '{cmd.namespace}', "
                f"not '{parsed_ns}'.[/red]"
            )
            raise typer.Exit(code=1)

        if cmd.status == "paused":
            console.print(
                f"[red]Command '{bare_name}' is paused. "
                f"Run `navigator resume {bare_name}` first.[/red]"
            )
            raise typer.Exit(code=1)

        if dry_run:
            from navigator.executor import build_command_args, build_clean_env
            from navigator.secrets import load_secrets

            secrets = load_secrets(cmd.secrets)
            env = build_clean_env(secrets)
            args = build_command_args(cmd.prompt, cmd.allowed_tools)

            dry_run_data = {
                "command_name": cmd.name,
                "namespace": cmd.namespace,
                "command_args": args,
                "working_directory": str(cmd.environment),
                "env_keys": sorted(env.keys()),
                "allowed_tools": cmd.allowed_tools,
                "chain_next": cmd.chain_next,
                "on_failure_continue": cmd.on_failure_continue,
            }

            from navigator.output import is_json, json_response

            if is_json():
                typer.echo(json_response("ok", dry_run_data))
            else:
                from rich.panel import Panel

                lines = []
                lines.append(f"Command:    {cmd.name}")
                lines.append(f"Namespace:  {cmd.namespace}")
                lines.append(f"Directory:  {cmd.environment}")
                lines.append(f"Args:       {' '.join(args)}")
                lines.append(f"Env keys:   {', '.join(sorted(env.keys()))}")
                tools_str = ", ".join(cmd.allowed_tools) if cmd.allowed_tools else "(none)"
                lines.append(f"Tools:      {tools_str}")
                if cmd.chain_next:
                    lines.append(f"Chain next: {cmd.chain_next}")
                    lines.append(f"On failure: {'continue' if cmd.on_failure_continue else 'stop'}")
                console.print(Panel("\n".join(lines), title="Dry Run", border_style="cyan"))
            return

        # Chain execution: if command has chain_next, run entire chain
        if cmd.chain_next is not None:
            from navigator.chainer import execute_chain

            try:
                chain_result = execute_chain(conn, cmd, config)
            except (FileNotFoundError, ValueError) as e:
                console.print(f"[red]{e}[/red]")
                raise typer.Exit(code=1) from None

            console.print(f"[dim]Chain ID: {chain_result.correlation_id}[/dim]")
            for i, step_result in enumerate(chain_result.results, 1):
                if step_result.returncode == 0:
                    console.print(
                        f"  [green]Step {i}: {step_result.command_name} "
                        f"(exit 0)[/green]"
                    )
                else:
                    console.print(
                        f"  [red]Step {i}: {step_result.command_name} "
                        f"(exit {step_result.returncode})[/red]"
                    )
            console.print(
                f"[dim]{chain_result.steps_run}/{chain_result.total_steps} "
                f"steps completed[/dim]"
            )

            if not chain_result.success:
                # Find last non-zero return code
                last_code = 1
                for r in reversed(chain_result.results):
                    if r.returncode != 0:
                        last_code = r.returncode
                        break
                raise typer.Exit(code=last_code)
            return

        # Single command execution (no chain)
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

        from navigator.output import is_json, json_response

        if is_json():
            typer.echo(json_response("ok", {"schedules": entries}))
            return

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

        from navigator.output import is_json, json_response

        if is_json():
            watcher_data = [
                {
                    "id": w.id,
                    "command_name": w.command_name,
                    "watch_path": str(w.watch_path),
                    "patterns": w.patterns,
                    "debounce_ms": w.debounce_ms,
                    "active_hours": w.active_hours,
                    "status": w.status,
                }
                for w in watchers
            ]
            typer.echo(json_response("ok", {"watchers": watcher_data}))
            return

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
def chain(
    command: Annotated[
        str, typer.Argument(help="Command name (supports namespace:command)")
    ],
    next_cmd: Annotated[
        str | None,
        typer.Option("--next", help="Next command to chain (supports namespace:command)"),
    ] = None,
    show: Annotated[
        bool,
        typer.Option("--show", help="Show the chain starting from this command"),
    ] = False,
    remove: Annotated[
        bool,
        typer.Option("--remove", help="Remove chain link from this command"),
    ] = False,
    on_failure: Annotated[
        str | None,
        typer.Option("--on-failure", help="Failure mode: 'stop' (default) or 'continue'"),
    ] = None,
) -> None:
    """Chain commands together."""
    from datetime import UTC, datetime

    from navigator.config import load_config
    from navigator.db import get_command_by_name, get_connection, init_db, update_command
    from navigator.namespace import parse_qualified_name

    # Validate flags: at least one mode required
    if next_cmd is None and not show and not remove:
        console.print(
            "[yellow]Use --next to link, --show to display, "
            "or --remove to unlink.[/yellow]"
        )
        raise typer.Exit(code=1)

    # Validate mutual exclusion
    if next_cmd is not None and (show or remove):
        console.print("[red]Cannot combine --next with --show or --remove.[/red]")
        raise typer.Exit(code=1)
    if show and remove:
        console.print("[red]Cannot combine --show with --remove.[/red]")
        raise typer.Exit(code=1)

    # Parse command name
    try:
        _parsed_ns, bare_name = parse_qualified_name(command)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from None

    config = load_config()
    conn = get_connection(config.db_path)
    try:
        init_db(conn)

        # Look up the source command
        cmd = get_command_by_name(conn, bare_name)
        if cmd is None:
            console.print(f"[red]Command '{bare_name}' not found.[/red]")
            raise typer.Exit(code=1)

        # --- --show mode ---
        if show:
            from navigator.chainer import walk_chain

            try:
                chain_cmds = walk_chain(conn, bare_name, config.max_chain_depth)
            except ValueError as exc:
                console.print(f"[red]{exc}[/red]")
                raise typer.Exit(code=1) from None

            parts: list[str] = []
            for c in chain_cmds:
                label = c.name
                if c.on_failure_continue:
                    label += " [dim](continue on failure)[/dim]"
                parts.append(label)

            console.print(" -> ".join(parts))
            return

        # --- --remove mode ---
        if remove:
            if cmd.chain_next is None:
                console.print(
                    f"[yellow]Command '{bare_name}' has no chain link.[/yellow]"
                )
                return

            now = datetime.now(UTC).isoformat()
            with conn:
                conn.execute(
                    "UPDATE commands SET chain_next = NULL, on_failure_continue = 0, "
                    "updated_at = ? WHERE name = ?",
                    (now, bare_name),
                )
            console.print(
                f"[green]Removed chain link from '{bare_name}'[/green]"
            )
            return

        # --- --next mode (link) ---
        if next_cmd is not None:
            # Validate on_failure value
            if on_failure is not None and on_failure not in ("stop", "continue"):
                console.print(
                    f"[red]Invalid --on-failure value '{on_failure}'. "
                    "Use 'stop' or 'continue'.[/red]"
                )
                raise typer.Exit(code=1)

            # Parse target command
            try:
                _next_ns, next_bare = parse_qualified_name(next_cmd)
            except ValueError as exc:
                console.print(f"[red]{exc}[/red]")
                raise typer.Exit(code=1) from None

            # Validate target exists
            target = get_command_by_name(conn, next_bare)
            if target is None:
                console.print(f"[red]Command '{next_bare}' not found.[/red]")
                raise typer.Exit(code=1)

            # Cycle detection
            from navigator.chainer import detect_cycle

            if detect_cycle(conn, bare_name, next_bare):
                console.print(
                    f"[red]Cycle detected: chaining '{bare_name}' -> "
                    f"'{next_cmd}' would create a loop.[/red]"
                )
                raise typer.Exit(code=1)

            on_failure_continue = on_failure == "continue"
            update_command(
                conn,
                bare_name,
                chain_next=next_cmd,
                on_failure_continue=on_failure_continue,
            )
            console.print(
                f"[green]Chained '{command}' -> '{next_cmd}'[/green]"
            )
            return
    finally:
        conn.close()


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

    from navigator.output import is_json, json_response

    if is_json():
        log_data = [
            {
                "timestamp": e.timestamp,
                "exit_code": e.exit_code,
                "duration": e.duration,
                "attempt": e.attempt,
            }
            for e in entries
        ]
        typer.echo(json_response("ok", {"logs": log_data}))
        return

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
def daemon() -> None:
    """Run the watcher daemon in foreground (for systemd)."""
    from navigator.config import load_config
    from navigator.watcher import run_daemon

    config = load_config()
    console.print("[dim]Starting watcher daemon...[/dim]")
    run_daemon(config)


@app.command(name="install-service")
def install_service_cmd(
    no_linger: Annotated[
        bool,
        typer.Option("--no-linger", help="Skip loginctl enable-linger"),
    ] = False,
) -> None:
    """Generate and install the systemd user service."""
    from navigator.service import install_service

    try:
        path = install_service(enable_linger=not no_linger)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from None
    except subprocess.CalledProcessError as exc:
        console.print(f"[red]systemctl failed: {exc}[/red]")
        raise typer.Exit(code=1) from None

    console.print(f"[green]Service installed at {path}[/green]")
    console.print("[dim]Start with: navigator service start[/dim]")


@app.command(name="uninstall-service")
def uninstall_service_cmd() -> None:
    """Remove the systemd user service."""
    from navigator.service import uninstall_service

    existed = uninstall_service()
    if existed:
        console.print("[green]Service uninstalled.[/green]")
    else:
        console.print("[yellow]Service was not installed.[/yellow]")


@app.command()
def service(
    action: Annotated[
        str,
        typer.Argument(help="Action: status, start, stop, restart"),
    ],
) -> None:
    """Manage the Navigator systemd service."""
    from navigator.service import service_control

    try:
        result = service_control(action)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from None

    if result.stdout:
        console.print(result.stdout.strip())
    if result.stderr:
        console.print(f"[dim]{result.stderr.strip()}[/dim]")
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@app.command()
def doctor(
    fix: Annotated[
        bool,
        typer.Option("--fix", help="Apply safe auto-fixes for common issues"),
    ] = False,
) -> None:
    """Verify system health."""
    from navigator.config import load_config
    from navigator.doctor import run_doctor
    from navigator.output import is_json, json_response

    config = load_config()
    result = run_doctor(config, fix=fix)

    if is_json():
        data = {
            "checks": [
                {
                    "name": c.name,
                    "status": c.status,
                    "message": c.message,
                    "fixable": c.fixable,
                    "fixed": c.fixed,
                }
                for c in result.checks
            ],
            "summary": result.summary,
        }
        typer.echo(json_response("ok", data))
    else:
        status_icons = {
            "pass": "[green]PASS[/green]",
            "fail": "[red]FAIL[/red]",
            "warn": "[yellow]WARN[/yellow]",
        }
        for check in result.checks:
            icon = status_icons.get(check.status, check.status)
            fixed_tag = " [green](fixed)[/green]" if check.fixed else ""
            console.print(f"  {icon}  {check.name}: {check.message}{fixed_tag}")

        s = result.summary
        console.print(
            f"\n[bold]{s['total']} checks:[/bold] "
            f"[green]{s['passed']} passed[/green], "
            f"[red]{s['failed']} failed[/red], "
            f"[yellow]{s['warned']} warned[/yellow]"
        )

    if result.summary["failed"] > 0:
        raise typer.Exit(code=1)
