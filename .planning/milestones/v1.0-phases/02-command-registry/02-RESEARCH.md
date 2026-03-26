# Phase 2: Command Registry - Research

**Researched:** 2026-03-23
**Domain:** CLI CRUD operations, SQLite persistence, Pydantic data modeling
**Confidence:** HIGH

## Summary

Phase 2 implements the command registry -- the core data layer and CLI interface for registering, browsing, and managing commands. The technical domain is well-understood: SQLite via Python's stdlib `sqlite3`, Pydantic v2 models for validation and serialization, Typer with `Annotated` syntax for CLI commands, and Rich tables for output formatting. All libraries are already in `pyproject.toml` dependencies except `sqlite3` which is stdlib.

The key architectural decisions are already locked: SQLite over TinyDB (D-14), stdlib `sqlite3` with no ORM (D-15), Pydantic model for the Command record (D-16), name as user-facing identifier with UUID as internal PK (D-01/D-02), and field-level patching for updates (D-10). Research focuses on the correct patterns for implementing these decisions safely, particularly around SQLite's transaction model in Python 3.12+ and the Pydantic-to-SQLite serialization boundary.

**Primary recommendation:** Use Python 3.12's `autocommit=False` with WAL mode and the connection context manager for crash-safe atomic writes. Keep the database layer as a thin module (`db.py`) with a Pydantic model (`models.py`) that handles all validation -- the CLI layer should never construct raw SQL.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Name as the primary user-facing identifier. Commands are referenced by name in all CLI operations (`navigator show my-command`, `navigator delete my-command`).
- **D-02:** Auto-generated UUID as internal primary key. Used for database references and future cross-namespace resolution (Phase 7).
- **D-03:** Names must be unique within a namespace. Name validation: lowercase alphanumeric + hyphens, no spaces.
- **D-04:** `name` is a required positional argument: `navigator register my-command --prompt "..."`.
- **D-05:** `--prompt` is a required option (the Claude Code prompt/instruction to execute).
- **D-06:** Optional flags with sensible defaults: `--environment` (working directory, defaults to cwd), `--secrets` (secrets path, defaults to none), `--allowed-tools` (comma-separated list, defaults to none).
- **D-07:** All paths resolved to absolute at registration time via `resolve_path()` from config module (INFRA-07 carry-forward).
- **D-08:** Rich tables for human-readable output on `list` and `show` commands.
- **D-09:** JSON output mode (`--output json`) deferred to Phase 10 (INFRA-04). For now, Rich tables only.
- **D-10:** Field-level patching -- `navigator update my-command --prompt "new prompt"` updates only the prompt field. Unspecified fields remain unchanged.
- **D-11:** All update-able fields are optional flags on the `update` subcommand.
- **D-12:** Status field on the command record: `active` or `paused`. Simple enum, no separate table.
- **D-13:** Paused commands are skipped by the executor (Phase 3) and scheduler (Phase 5). The registry just stores the state.
- **D-14:** Single `commands` table with columns for all command fields. SQLite chosen over TinyDB per REG-10 for crash-safe atomic transactions.
- **D-15:** Use Python `sqlite3` stdlib module -- no ORM. Direct SQL with parameterized queries.
- **D-16:** Pydantic model for the Command record -- validates data before DB writes, serializes for display.

### Claude's Discretion
- Exact SQLite column types and constraints (NOT NULL, defaults, indexes)
- Whether to add a `show` subcommand vs overloading `list` with a `--name` filter
- Internal module organization (single `registry.py` vs `models.py` + `db.py`)
- Whether `created_at` / `updated_at` timestamps use ISO 8601 strings or Unix epoch integers
- Test structure and fixtures

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REG-01 | User can register a command with name, prompt, environment path, secrets path, and allowed tools | Typer Annotated patterns for positional args + required/optional options; Pydantic model validation; `resolve_path()` for all paths |
| REG-02 | User can list all registered commands with filtering by namespace | Rich Table rendering; SQL `SELECT` with optional `WHERE namespace = ?`; namespace column defaults to `"default"` for now |
| REG-03 | User can show details of a specific registered command | Separate `show` subcommand with Rich panel/table; SQL `SELECT WHERE name = ?` |
| REG-04 | User can update any field of a registered command | Field-level patching via optional Typer options; dynamic SQL `UPDATE SET` for only provided fields |
| REG-05 | User can delete a registered command | SQL `DELETE WHERE name = ?` with confirmation or `--force` flag; note cleanup of crontab/watchers is Phase 5/6 concern |
| REG-06 | User can pause a registered command | SQL `UPDATE SET status = 'paused'` with status enum validation |
| REG-07 | User can resume a paused command | SQL `UPDATE SET status = 'active'` with status enum validation |
| REG-08 | User can list commands sorted by created date for housekeeping | SQL `ORDER BY created_at` with `--sort` flag; ISO 8601 timestamps for natural sort |
| REG-10 | Registry persists in SQLite with crash-safe atomic transactions | WAL mode + `autocommit=False` + context manager pattern; `BEGIN IMMEDIATE` for writes |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Tech stack**: Python >= 3.12, globally installable via pip/uv
- **Build backend**: hatchling
- **CLI framework**: Typer >= 0.24.0 with Annotated syntax
- **Validation**: Pydantic >= 2.12
- **Output**: Rich >= 14.0 for tables
- **Linting**: ruff (replaces flake8/black/isort)
- **Testing**: pytest >= 9.0
- **Package manager**: uv (not pip directly)
- **DB**: SQLite via stdlib `sqlite3` -- no ORM, no TinyDB
- **Paths**: All paths resolved to absolute at registration via `resolve_path()`
- **Config**: XDG-compliant paths via platformdirs

## Standard Stack

### Core (already in pyproject.toml)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| sqlite3 | stdlib (SQLite 3.37.2) | Command registry persistence | Stdlib, zero dependencies, crash-safe with WAL, verified available on target system |
| Pydantic | >= 2.12 | Command model validation + serialization | Already in deps, Rust-backed v2, handles all type coercion and validation |
| Typer | >= 0.24.0 | CLI subcommands with type-annotated args | Already in deps, Annotated syntax for clean arg/option definitions |
| Rich | >= 14.0 | Table output for list/show commands | Already in deps, Typer integrates natively |

### Supporting (already in pyproject.toml)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| platformdirs | >= 4.0 | XDG path for DB location | `get_data_dir()` already provides `~/.local/share/navigator/` |
| uuid (stdlib) | stdlib | Generate command UUIDs | `uuid.uuid4()` for internal primary keys |

### No New Dependencies Required
All libraries needed for Phase 2 are already declared in `pyproject.toml` or are Python stdlib. No `pip install` or `uv add` needed.

## Architecture Patterns

### Recommended Module Structure
```
src/navigator/
    __init__.py          # existing
    __main__.py          # existing
    cli.py               # existing -- add register/list/show/update/delete/pause/resume implementations
    config.py            # existing -- resolve_path(), load_config(), db_path
    models.py            # NEW -- Command Pydantic model, CommandStatus enum
    db.py                # NEW -- SQLite connection management, CRUD operations
```

**Rationale for `models.py` + `db.py` split (discretion area):** Separating the Pydantic model from database operations keeps concerns clean. `models.py` is pure data validation (testable without SQLite). `db.py` is the persistence layer that accepts/returns model instances. The CLI layer calls `db.py` functions, never writes SQL directly.

### Pattern 1: Command Pydantic Model
**What:** Single Pydantic model representing a command record with validation
**When to use:** All command creation, update validation, and display serialization

```python
# src/navigator/models.py
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class CommandStatus(StrEnum):
    """Command lifecycle status."""
    ACTIVE = "active"
    PAUSED = "paused"


class Command(BaseModel):
    """A registered command in the Navigator registry."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    prompt: str
    environment: Path
    secrets: Path | None = None
    allowed_tools: list[str] = Field(default_factory=list)
    namespace: str = "default"
    status: CommandStatus = CommandStatus.ACTIVE
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Enforce lowercase alphanumeric + hyphens, no spaces."""
        import re
        if not re.match(r"^[a-z0-9][a-z0-9-]*$", v):
            msg = "Name must be lowercase alphanumeric + hyphens, cannot start with hyphen"
            raise ValueError(msg)
        return v
```

**Timestamp recommendation (discretion area):** Use ISO 8601 strings (`datetime.now(timezone.utc).isoformat()`). Reasons: human-readable in database inspection, sorts correctly as text in SQLite, no timezone ambiguity with explicit UTC, consistent with standard APIs. Unix epochs save bytes but lose readability for a personal tool.

### Pattern 2: SQLite Database Layer
**What:** Connection management with WAL mode, parameterized CRUD operations
**When to use:** All database interactions -- never bypass this layer

```python
# src/navigator/db.py
from __future__ import annotations

import sqlite3
from pathlib import Path

from navigator.models import Command


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Create a SQLite connection with WAL mode and row factory."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), autocommit=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create the commands table if it does not exist."""
    with conn:
        conn.execute("""
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
        """)


def insert_command(conn: sqlite3.Connection, cmd: Command) -> None:
    """Insert a validated Command into the database."""
    import json
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
                cmd.status.value,
                cmd.created_at,
                cmd.updated_at,
            ),
        )
```

### Pattern 3: Typer Command with Annotated Syntax
**What:** CLI subcommand with positional argument + required/optional options
**When to use:** The `register` command implementation

```python
# In src/navigator/cli.py
from typing import Annotated

@app.command()
def register(
    name: Annotated[str, typer.Argument(help="Command name (lowercase, hyphens allowed)")],
    prompt: Annotated[str, typer.Option("--prompt", "-p", help="Claude Code prompt to execute")],
    environment: Annotated[
        str | None,
        typer.Option("--environment", "-e", help="Working directory (defaults to cwd)"),
    ] = None,
    secrets: Annotated[
        str | None,
        typer.Option("--secrets", "-s", help="Path to secrets file"),
    ] = None,
    allowed_tools: Annotated[
        str | None,
        typer.Option("--allowed-tools", "-t", help="Comma-separated list of allowed tools"),
    ] = None,
) -> None:
    """Register a new command."""
    # resolve paths, validate via Pydantic, persist via db.py
```

### Pattern 4: Rich Table Output
**What:** Formatted table for `list` command output
**When to use:** `list` and `show` commands

```python
from rich.console import Console
from rich.table import Table

console = Console()

def render_command_table(commands: list[Command]) -> None:
    """Display commands as a Rich table."""
    table = Table(title="Registered Commands")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Namespace", style="dim")
    table.add_column("Created", style="dim")
    for cmd in commands:
        status_style = "green" if cmd.status == "active" else "yellow"
        table.add_row(cmd.name, f"[{status_style}]{cmd.status}[/]", cmd.namespace, cmd.created_at)
    console.print(table)
```

### Pattern 5: Field-Level Update
**What:** Dynamic SQL UPDATE for only the fields the user provided
**When to use:** The `update` subcommand (D-10)

```python
def update_command(conn: sqlite3.Connection, name: str, **fields) -> None:
    """Update only the provided fields for a command."""
    from datetime import datetime, timezone
    # Filter out None values (user didn't provide these)
    updates = {k: v for k, v in fields.items() if v is not None}
    if not updates:
        return
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [name]
    with conn:
        conn.execute(
            f"UPDATE commands SET {set_clause} WHERE name = ?",
            values,
        )
```

### Anti-Patterns to Avoid
- **String-formatting SQL:** Always use parameterized queries (`?` placeholders). Never f-strings for SQL.
- **Opening connections per operation:** Create one connection per CLI invocation, pass it through. Don't open/close per query.
- **Validating in the CLI layer:** CLI extracts user input and passes to Pydantic model. Validation logic lives in the model, not scattered across CLI functions.
- **Storing lists as comma-separated strings:** Use `json.dumps()`/`json.loads()` for the `allowed_tools` list. Comma-separated breaks if a tool name contains a comma.
- **Forgetting `updated_at`:** Every mutation (update, pause, resume) must set `updated_at` to current timestamp.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| UUID generation | Custom ID scheme | `uuid.uuid4()` | Collision-resistant, stdlib, universally understood |
| Name validation regex | Custom character-by-character validation | Pydantic `field_validator` with `re.match` | Declarative, testable, runs automatically on model creation |
| Path resolution | Manual `os.path` logic | `resolve_path()` from `config.py` | Already exists, handles `~` expansion and relative paths (INFRA-07) |
| Table formatting | Manual string padding/alignment | `rich.table.Table` | Handles terminal width, column wrapping, styling automatically |
| Timestamp formatting | Custom format strings | `datetime.now(timezone.utc).isoformat()` | Standard ISO 8601, sorts correctly, timezone-aware |
| Transaction safety | Manual BEGIN/COMMIT | `with conn:` context manager | Auto-commits on success, auto-rollbacks on exception |

## Common Pitfalls

### Pitfall 1: SQLite Connection Without WAL Mode
**What goes wrong:** Default journal mode (DELETE) locks the entire database during writes. Future phases (executor, watcher daemon) that read while CLI writes will get "database is locked" errors.
**Why it happens:** WAL mode isn't the default -- you must explicitly enable it.
**How to avoid:** Call `PRAGMA journal_mode=WAL` immediately after opening every connection. WAL mode is persistent (stored in the DB file), but setting it on every connection is idempotent and safe.
**Warning signs:** "database is locked" errors when multiple processes access the DB.

### Pitfall 2: Forgetting autocommit=False in Python 3.12
**What goes wrong:** Python 3.12's default is `LEGACY_TRANSACTION_CONTROL` which has inconsistent implicit transaction behavior. Some PRAGMA statements fail silently because they're inside an implicit transaction.
**Why it happens:** The default hasn't changed yet for backwards compatibility, but the legacy behavior is poorly documented and surprising.
**How to avoid:** Always pass `autocommit=False` to `sqlite3.connect()` and use `with conn:` for all mutations.
**Warning signs:** PRAGMA commands not taking effect, or transactions not committing when expected.

### Pitfall 3: Not Handling "Command Not Found" Gracefully
**What goes wrong:** `show`, `update`, `delete`, `pause`, `resume` all take a name argument. If the name doesn't exist, a cryptic error or silent no-op results.
**Why it happens:** SQL UPDATE/DELETE on non-existent rows succeed silently (0 rows affected).
**How to avoid:** After every UPDATE/DELETE, check `cursor.rowcount`. If 0, raise a clear error: `"Command 'foo' not found"`.
**Warning signs:** User runs `navigator delete typo-name` and gets no feedback.

### Pitfall 4: allowed_tools Serialization Mismatch
**What goes wrong:** User passes `--allowed-tools "Edit,Write,Bash"` (comma-separated string). Code stores it as a string. Later, Phase 3 executor tries to iterate over it and gets individual characters.
**Why it happens:** Confusion between CLI input format (comma-separated string) and storage format (JSON array).
**How to avoid:** Parse comma-separated input in CLI layer (`value.split(",")` with strip), store as `json.dumps(list)` in SQLite, deserialize with `json.loads()` when reading back.
**Warning signs:** Executor commands getting tools like `"E"`, `"d"`, `"i"`, `"t"` instead of `"Edit"`.

### Pitfall 5: Path Fields Stored as Relative
**What goes wrong:** User runs `navigator register foo --environment .` from `/home/user/project`. Path stored as `.`. Later, cron runs from `/` and the command executes in the wrong directory.
**Why it happens:** Forgetting to call `resolve_path()` on environment and secrets before storing.
**How to avoid:** Call `resolve_path()` on all path fields in the CLI layer before constructing the Pydantic model. Pydantic model stores only absolute `Path` objects.
**Warning signs:** Commands work when run manually but fail when scheduled via cron.

### Pitfall 6: Typer list Command Name Conflict
**What goes wrong:** Defining `def list()` shadows Python's built-in `list` type, causing subtle type errors elsewhere in the module.
**Why it happens:** `list` is both a desired CLI command name and a Python builtin.
**How to avoid:** Already handled in Phase 1 -- the function is named `list_commands()` with `@app.command(name="list")`. Follow this same pattern for any other built-in conflicts.
**Warning signs:** `TypeError: 'function' object is not iterable` when trying to use `list()` as a type constructor.

## Code Examples

### Complete Register Flow
```python
# CLI layer extracts input, resolves paths, delegates to model + db
@app.command()
def register(
    name: Annotated[str, typer.Argument(help="Command name")],
    prompt: Annotated[str, typer.Option("--prompt", "-p", help="Prompt text")],
    environment: Annotated[str | None, typer.Option("--environment", "-e")] = None,
    secrets: Annotated[str | None, typer.Option("--secrets", "-s")] = None,
    allowed_tools: Annotated[str | None, typer.Option("--allowed-tools", "-t")] = None,
) -> None:
    """Register a new command."""
    from navigator.config import load_config, resolve_path
    from navigator.db import get_connection, init_db, insert_command
    from navigator.models import Command

    config = load_config()
    env_path = resolve_path(environment) if environment else resolve_path(Path.cwd())
    sec_path = resolve_path(secrets) if secrets else None
    tools = [t.strip() for t in allowed_tools.split(",")] if allowed_tools else []

    cmd = Command(name=name, prompt=prompt, environment=env_path, secrets=sec_path, allowed_tools=tools)

    conn = get_connection(config.db_path)
    try:
        init_db(conn)
        insert_command(conn, cmd)
        console.print(f"[green]Registered command '{name}'[/green]")
    finally:
        conn.close()
```

### SQLite Schema (Recommended)
```sql
CREATE TABLE IF NOT EXISTS commands (
    id          TEXT PRIMARY KEY,                    -- UUID v4
    name        TEXT NOT NULL UNIQUE,                -- user-facing identifier
    prompt      TEXT NOT NULL,                       -- Claude Code prompt
    environment TEXT NOT NULL,                       -- absolute path to working directory
    secrets     TEXT,                                -- absolute path to secrets file (nullable)
    allowed_tools TEXT NOT NULL DEFAULT '[]',        -- JSON array of tool names
    namespace   TEXT NOT NULL DEFAULT 'default',     -- for Phase 7 namespacing
    status      TEXT NOT NULL DEFAULT 'active',      -- 'active' or 'paused'
    created_at  TEXT NOT NULL,                       -- ISO 8601 UTC timestamp
    updated_at  TEXT NOT NULL                        -- ISO 8601 UTC timestamp
);

-- Index for listing by namespace (REG-02)
CREATE INDEX IF NOT EXISTS idx_commands_namespace ON commands(namespace);

-- Index for sorting by created_at (REG-08)
CREATE INDEX IF NOT EXISTS idx_commands_created_at ON commands(created_at);
```

### Reading Command Back from SQLite to Pydantic
```python
import json

def row_to_command(row: sqlite3.Row) -> Command:
    """Convert a sqlite3.Row to a Command model."""
    return Command(
        id=row["id"],
        name=row["name"],
        prompt=row["prompt"],
        environment=Path(row["environment"]),
        secrets=Path(row["secrets"]) if row["secrets"] else None,
        allowed_tools=json.loads(row["allowed_tools"]),
        namespace=row["namespace"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `isolation_level=None` for manual transaction control | `autocommit=False` (PEP 249 compliant) | Python 3.12 | Cleaner, more predictable transaction behavior |
| `sqlite3.Row` only | `sqlite3.Row` + Pydantic `model_validate` | Pydantic v2 | Type-safe deserialization from DB rows |
| Pydantic v1 `class Config` | Pydantic v2 `model_config` dict | Pydantic 2.0 | Rust-backed core, `model_dump()` replaces `.dict()` |
| Click decorators | Typer `Annotated` syntax | Typer 0.9+ | Type hints drive CLI parsing, less boilerplate |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REG-01 | Register command with all fields | unit + integration | `uv run pytest tests/test_registry.py::test_register_command -x` | No -- Wave 0 |
| REG-01 | Name validation rejects invalid names | unit | `uv run pytest tests/test_models.py::test_name_validation -x` | No -- Wave 0 |
| REG-02 | List commands with namespace filter | unit | `uv run pytest tests/test_registry.py::test_list_commands -x` | No -- Wave 0 |
| REG-03 | Show command details | unit | `uv run pytest tests/test_registry.py::test_show_command -x` | No -- Wave 0 |
| REG-04 | Update individual fields | unit | `uv run pytest tests/test_registry.py::test_update_command -x` | No -- Wave 0 |
| REG-05 | Delete command | unit | `uv run pytest tests/test_registry.py::test_delete_command -x` | No -- Wave 0 |
| REG-06 | Pause command sets status | unit | `uv run pytest tests/test_registry.py::test_pause_command -x` | No -- Wave 0 |
| REG-07 | Resume command sets status | unit | `uv run pytest tests/test_registry.py::test_resume_command -x` | No -- Wave 0 |
| REG-08 | List sorted by created date | unit | `uv run pytest tests/test_registry.py::test_list_sorted_by_date -x` | No -- Wave 0 |
| REG-10 | SQLite persistence survives restart | integration | `uv run pytest tests/test_db.py::test_persistence -x` | No -- Wave 0 |
| REG-10 | WAL mode enabled | unit | `uv run pytest tests/test_db.py::test_wal_mode -x` | No -- Wave 0 |
| REG-10 | Transaction rollback on error | unit | `uv run pytest tests/test_db.py::test_transaction_rollback -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_models.py` -- Command model validation (name regex, defaults, status enum)
- [ ] `tests/test_db.py` -- SQLite CRUD, WAL mode, transaction safety, persistence
- [ ] `tests/test_registry.py` -- CLI integration tests via `CliRunner` for all 7 subcommands
- [ ] Update `tests/conftest.py` -- Add fixtures for in-memory SQLite connection, sample Command instances

## Open Questions

1. **show as separate subcommand vs list --name filter**
   - What we know: `show` and `list` serve different UX purposes. `list` shows a summary table; `show` shows full detail for one command.
   - Recommendation: Separate `show` subcommand. It's more discoverable via `--help`, follows the kubectl/docker pattern (`list` = many, `show`/`inspect` = one), and has different output formatting (vertical key-value vs horizontal table).

2. **Namespace column default value**
   - What we know: Namespacing is Phase 7 (NS-01). But the schema needs the column now to avoid a migration later.
   - Recommendation: Default to `"default"` namespace. The column exists from day one with a sensible default. Phase 7 adds namespace CRUD and the `namespace:command` syntax.

3. **REG-05 cleanup of crontab/watchers on delete**
   - What we know: REG-05 says "cleans up crontab entry and watchers." But crontab is Phase 5 and watchers are Phase 6.
   - Recommendation: Phase 2 implements `delete` for the registry record only. Add a hook point (or just a comment/TODO) where Phase 5/6 will add cleanup logic. The delete function should be designed so cleanup can be added without changing its signature.

## Sources

### Primary (HIGH confidence)
- [Python 3.12 sqlite3 docs](https://docs.python.org/3/library/sqlite3.html) -- autocommit parameter, context manager, parameterized queries
- [SQLite WAL documentation](https://sqlite.org/wal.html) -- WAL mode behavior and limitations
- [Typer CLI Arguments docs](https://typer.tiangolo.com/tutorial/commands/arguments/) -- Annotated syntax for positional args
- [Typer Required Options docs](https://typer.tiangolo.com/tutorial/options/required/) -- Required options with Annotated
- [Rich Tables docs](https://rich.readthedocs.io/en/stable/tables.html) -- Table API and column configuration
- [Pydantic v2 Models docs](https://docs.pydantic.dev/latest/concepts/models/) -- model_validate, model_dump, field_validator

### Secondary (MEDIUM confidence)
- [Simon Willison - Enabling WAL mode](https://til.simonwillison.net/sqlite/enabling-wal-mode) -- Practical WAL mode setup verified against official docs
- [Charles Leifer - Going Fast with SQLite](https://charlesleifer.com/blog/going-fast-with-sqlite-and-python/) -- Performance patterns for Python sqlite3

### Tertiary (LOW confidence)
- None -- all findings verified against official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in pyproject.toml, stdlib sqlite3 verified available
- Architecture: HIGH -- patterns are well-established (Pydantic + sqlite3 + Typer), decisions locked in CONTEXT.md
- Pitfalls: HIGH -- common SQLite/Python pitfalls documented in official docs and verified by multiple sources

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable domain, no fast-moving dependencies)
