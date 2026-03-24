"""Navigator SQLite database layer — connection, schema, and CRUD operations.

Provides crash-safe atomic writes with WAL mode and parameterized queries.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from navigator.models import Command, CommandStatus, Watcher, WatcherStatus

_CREATE_TABLE = """\
CREATE TABLE IF NOT EXISTS commands (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    prompt TEXT NOT NULL,
    environment TEXT NOT NULL,
    secrets TEXT,
    allowed_tools TEXT NOT NULL DEFAULT '[]',
    namespace TEXT NOT NULL DEFAULT 'default',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

_CREATE_INDEX_NAMESPACE = (
    "CREATE INDEX IF NOT EXISTS idx_commands_namespace ON commands(namespace)"
)
_CREATE_INDEX_CREATED = (
    "CREATE INDEX IF NOT EXISTS idx_commands_created_at ON commands(created_at)"
)

_CREATE_WATCHERS_TABLE = """\
CREATE TABLE IF NOT EXISTS watchers (
    id TEXT PRIMARY KEY,
    command_name TEXT NOT NULL,
    watch_path TEXT NOT NULL,
    patterns TEXT NOT NULL DEFAULT '["*"]',
    ignore_patterns TEXT NOT NULL DEFAULT '[".git/**","*.swp","*.tmp","*~","__pycache__/**"]',
    debounce_ms INTEGER NOT NULL DEFAULT 500,
    active_hours TEXT,
    recursive INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (command_name) REFERENCES commands(name) ON DELETE CASCADE
)
"""

_CREATE_INDEX_WATCHERS_COMMAND = (
    "CREATE INDEX IF NOT EXISTS idx_watchers_command ON watchers(command_name)"
)
_CREATE_INDEX_WATCHERS_STATUS = (
    "CREATE INDEX IF NOT EXISTS idx_watchers_status ON watchers(status)"
)


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection with WAL mode and foreign keys enabled.

    Creates parent directories if they don't exist.
    PRAGMAs are executed in autocommit mode since they cannot run inside
    a transaction, then the connection is set to manual commit mode.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # PRAGMAs must run outside a transaction, so connect with autocommit first
    conn = sqlite3.connect(str(db_path), autocommit=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    # Switch to manual transaction management for all subsequent operations
    conn.autocommit = False
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create the commands and watchers tables and indexes if they don't exist."""
    with conn:
        conn.execute(_CREATE_TABLE)
        conn.execute(_CREATE_INDEX_NAMESPACE)
        conn.execute(_CREATE_INDEX_CREATED)
        conn.execute(_CREATE_WATCHERS_TABLE)
        conn.execute(_CREATE_INDEX_WATCHERS_COMMAND)
        conn.execute(_CREATE_INDEX_WATCHERS_STATUS)


def insert_command(conn: sqlite3.Connection, cmd: Command) -> None:
    """Insert a command into the database atomically."""
    with conn:
        conn.execute(
            """INSERT INTO commands
            (id, name, prompt, environment, secrets, allowed_tools,
             namespace, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                cmd.id,
                cmd.name,
                cmd.prompt,
                str(cmd.environment),
                str(cmd.secrets) if cmd.secrets else None,
                json.dumps(cmd.allowed_tools),
                cmd.namespace,
                cmd.status,
                cmd.created_at,
                cmd.updated_at,
            ),
        )


def get_command_by_name(conn: sqlite3.Connection, name: str) -> Command | None:
    """Retrieve a command by name, or None if not found."""
    row = conn.execute(
        "SELECT * FROM commands WHERE name = ?", (name,)
    ).fetchone()
    if row is None:
        return None
    return row_to_command(row)


def get_all_commands(
    conn: sqlite3.Connection,
    namespace: str | None = None,
    sort_by_created: bool = False,
) -> list[Command]:
    """Retrieve all commands, optionally filtered by namespace and sorted."""
    query = "SELECT * FROM commands"
    params: list[str] = []

    if namespace is not None:
        query += " WHERE namespace = ?"
        params.append(namespace)

    if sort_by_created:
        query += " ORDER BY created_at DESC"

    rows = conn.execute(query, params).fetchall()
    return [row_to_command(row) for row in rows]


def update_command(conn: sqlite3.Connection, name: str, **fields: object) -> int:
    """Update specified fields of a command by name.

    Always updates updated_at. Returns number of rows affected (0 or 1).
    """
    # Filter out None values
    updates = {k: v for k, v in fields.items() if v is not None}
    if not updates:
        return 0

    # Always update timestamp
    updates["updated_at"] = datetime.now(UTC).isoformat()

    # Serialize complex types
    if "allowed_tools" in updates:
        updates["allowed_tools"] = json.dumps(updates["allowed_tools"])
    if "environment" in updates:
        updates["environment"] = str(updates["environment"])
    if "secrets" in updates:
        updates["secrets"] = str(updates["secrets"])

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = [*updates.values(), name]

    with conn:
        cursor = conn.execute(
            f"UPDATE commands SET {set_clause} WHERE name = ?",  # noqa: S608
            values,
        )
        return cursor.rowcount


def delete_command(conn: sqlite3.Connection, name: str) -> int:
    """Delete a command by name. Returns number of rows affected (0 or 1)."""
    with conn:
        cursor = conn.execute("DELETE FROM commands WHERE name = ?", (name,))
        return cursor.rowcount


def row_to_command(row: sqlite3.Row) -> Command:
    """Deserialize a database row into a Command model."""
    return Command(
        id=row["id"],
        name=row["name"],
        prompt=row["prompt"],
        environment=Path(row["environment"]),
        secrets=Path(row["secrets"]) if row["secrets"] else None,
        allowed_tools=json.loads(row["allowed_tools"]),
        namespace=row["namespace"],
        status=CommandStatus(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# --- Watcher CRUD ---


def insert_watcher(conn: sqlite3.Connection, watcher: Watcher) -> None:
    """Insert a watcher into the database atomically."""
    with conn:
        conn.execute(
            """INSERT INTO watchers
            (id, command_name, watch_path, patterns, ignore_patterns,
             debounce_ms, active_hours, recursive, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                watcher.id,
                watcher.command_name,
                str(watcher.watch_path),
                json.dumps(watcher.patterns),
                json.dumps(watcher.ignore_patterns),
                watcher.debounce_ms,
                watcher.active_hours,
                1 if watcher.recursive else 0,
                watcher.status,
                watcher.created_at,
                watcher.updated_at,
            ),
        )


def get_watcher_by_id(conn: sqlite3.Connection, watcher_id: str) -> Watcher | None:
    """Retrieve a watcher by id, or None if not found."""
    row = conn.execute(
        "SELECT * FROM watchers WHERE id = ?", (watcher_id,)
    ).fetchone()
    if row is None:
        return None
    return row_to_watcher(row)


def get_watchers_for_command(
    conn: sqlite3.Connection, command_name: str
) -> list[Watcher]:
    """Retrieve all watchers for a specific command."""
    rows = conn.execute(
        "SELECT * FROM watchers WHERE command_name = ?", (command_name,)
    ).fetchall()
    return [row_to_watcher(row) for row in rows]


def get_active_watchers(conn: sqlite3.Connection) -> list[Watcher]:
    """Retrieve all active watchers."""
    rows = conn.execute(
        "SELECT * FROM watchers WHERE status = ?", (WatcherStatus.ACTIVE,)
    ).fetchall()
    return [row_to_watcher(row) for row in rows]


def delete_watcher(conn: sqlite3.Connection, watcher_id: str) -> int:
    """Delete a watcher by id. Returns number of rows affected (0 or 1)."""
    with conn:
        cursor = conn.execute("DELETE FROM watchers WHERE id = ?", (watcher_id,))
        return cursor.rowcount


def delete_watchers_for_command(conn: sqlite3.Connection, command_name: str) -> int:
    """Delete all watchers for a command. Returns number of rows affected."""
    with conn:
        cursor = conn.execute(
            "DELETE FROM watchers WHERE command_name = ?", (command_name,)
        )
        return cursor.rowcount


def row_to_watcher(row: sqlite3.Row) -> Watcher:
    """Deserialize a database row into a Watcher model."""
    return Watcher(
        id=row["id"],
        command_name=row["command_name"],
        watch_path=Path(row["watch_path"]),
        patterns=json.loads(row["patterns"]),
        ignore_patterns=json.loads(row["ignore_patterns"]),
        debounce_ms=row["debounce_ms"],
        active_hours=row["active_hours"],
        recursive=bool(row["recursive"]),
        status=WatcherStatus(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
