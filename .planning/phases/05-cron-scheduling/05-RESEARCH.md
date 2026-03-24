# Phase 5: Cron Scheduling - Research

**Researched:** 2026-03-24
**Domain:** System crontab management via python-crontab, file locking with fcntl
**Confidence:** HIGH

## Summary

Phase 5 adds cron scheduling to Navigator. Users schedule registered commands with cron expressions, and Navigator writes tagged entries to the real system crontab via the `python-crontab` library. Each entry invokes `navigator exec <command>`, so scheduled tasks work without a running daemon. File locking via `fcntl.flock` prevents crontab corruption from concurrent access.

The core challenge is straightforward: python-crontab provides a clean read-modify-write API for the system crontab, and `fcntl` is available in the Python stdlib on Linux. The main risk areas are (1) resolving the absolute path to the `navigator` binary for crontab entries (since cron runs with a minimal PATH), (2) ensuring the tag format is robust for find/remove operations, and (3) testing without modifying the real system crontab.

**Primary recommendation:** Create a `scheduler.py` module that wraps python-crontab with file locking. Use `CronTab(user=True)` for current-user crontab access, `find_comment()` for entry management, and `shutil.which('navigator')` resolved at schedule-time for absolute paths in cron commands.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Tag format: `# navigator:<command_name>` as a comment line immediately before the cron entry. Greppable for management.
- **D-02:** Cron command: `navigator exec <command_name>` -- uses existing exec subcommand, works without daemon running.
- **D-03:** Use `python-crontab` library for crontab CRUD -- no manual parsing of crontab files.
- **D-04:** Validate cron expressions via python-crontab before writing -- reject invalid expressions with clear error.
- **D-05:** Lock mechanism: `fcntl.flock` on a dedicated lock file at `{config.data_dir}/crontab.lock`.
- **D-06:** Lock timeout: 10 seconds, error with clear message if lock can't be acquired.
- **D-07:** Lock scope: entire read-modify-write cycle -- atomic crontab operations.
- **D-08:** Schedule syntax: `navigator schedule <command> --cron "*/5 * * * *"` -- cron expression as quoted string option.
- **D-09:** Unschedule: `navigator schedule <command> --remove` -- same subcommand, flag-based.
- **D-10:** List schedules: `navigator schedule --list` -- shows all scheduled commands with cron expressions as Rich table.
- **D-11:** Verify after write: re-read crontab and confirm the entry exists after writing.

### Claude's Discretion
- Internal module organization (single `scheduler.py` or separate `crontab_manager.py`)
- Whether to store schedule info in the SQLite registry alongside command records
- python-crontab API usage patterns and error handling
- Test strategy for crontab operations (mock vs real crontab in temp environment)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SCHED-01 | User can schedule a command with a cron expression via `navigator schedule <command> --cron <expr>` | python-crontab `CronTab.new()` + `CronItem.setall()` API verified; Typer CLI pattern established |
| SCHED-02 | Scheduled commands create tagged entries in the real system crontab (`# navigator:<id>`) | python-crontab `comment` parameter on `new()` + `find_comment()` for lookup verified |
| SCHED-03 | User can unschedule a command (removes crontab entry) | python-crontab `CronTab.remove()` + `find_comment()` verified |
| SCHED-04 | Crontab writes are file-locked to prevent corruption from concurrent access | `fcntl.flock` with `LOCK_EX` verified available on Linux |
| SCHED-05 | Crontab entries invoke `navigator exec <id>` so tasks survive daemon downtime | Absolute path resolution via `shutil.which()` researched; cron PATH limitation identified |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Tech stack**: Python, globally installable via pip/uv
- **Scheduling**: Must use the system's actual crontab, not a reimplementation
- **Library**: python-crontab for crontab CRUD (CLAUDE.md "What NOT to Use" explicitly forbids APScheduler, Celery, schedule)
- **Testing**: pytest with `uv run pytest`
- **Linting**: ruff
- **Patterns**: Lazy imports inside CLI functions, Rich Console/Table for output, Pydantic models for validation

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-crontab | 3.3.0 | Crontab CRUD | Reads/writes system crontab programmatically. Handles cron expression parsing, validation, entry CRUD. Latest version, verified on PyPI 2026-03-24. |
| fcntl (stdlib) | N/A | File locking | POSIX file locking. Available in Python stdlib on Linux. No external dependency needed. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shutil (stdlib) | N/A | Binary path resolution | `shutil.which('navigator')` to get absolute path for crontab entries |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| python-crontab | subprocess `crontab -l`/`crontab -` | Lower-level, must parse cron format yourself. python-crontab is a thin wrapper anyway. Only if python-crontab has a bug. |
| fcntl.flock | filelock (pip) | Cross-platform but adds a dependency. fcntl is fine since Navigator targets Linux only. |

**Installation:**
```bash
uv add python-crontab
```

**Version verification:** python-crontab 3.3.0 confirmed as latest on PyPI (2026-03-24). No newer versions exist.

## Architecture Patterns

### Recommended Module Organization

Use a single `scheduler.py` module. The scope (4 public functions: schedule, unschedule, list, verify) does not warrant splitting into multiple files.

```
src/navigator/
    scheduler.py      # NEW: CrontabManager class + file locking
    cli.py            # MODIFIED: replace schedule() stub
    config.py         # EXISTING: data_dir for lock file path
    db.py             # EXISTING: get_command_by_name for validation
```

### Pattern 1: CrontabManager Class

**What:** A class that encapsulates python-crontab operations with file locking.
**When to use:** All crontab read/write operations.

```python
# Source: Verified against python-crontab 3.3.0 API
import fcntl
import shutil
from pathlib import Path
from crontab import CronTab

COMMENT_PREFIX = "navigator"

class CrontabManager:
    """Manages Navigator entries in the system crontab with file locking."""

    def __init__(self, lock_path: Path) -> None:
        self.lock_path = lock_path

    def _make_comment(self, command_name: str) -> str:
        """Build the tag comment for a crontab entry."""
        return f"{COMMENT_PREFIX}:{command_name}"

    def _resolve_navigator_path(self) -> str:
        """Get absolute path to navigator binary for crontab entries."""
        path = shutil.which("navigator")
        if path is None:
            msg = "navigator CLI not found on PATH. Cannot create crontab entry."
            raise FileNotFoundError(msg)
        return path

    def schedule(self, command_name: str, cron_expr: str) -> None:
        """Add or update a crontab entry for a command."""
        nav_path = self._resolve_navigator_path()
        comment = self._make_comment(command_name)

        with self._lock():
            cron = CronTab(user=True)

            # Remove existing entry if any (idempotent update)
            existing = list(cron.find_comment(comment))
            for job in existing:
                cron.remove(job)

            # Create new entry
            job = cron.new(
                command=f"{nav_path} exec {command_name}",
                comment=comment,
            )
            job.setall(cron_expr)

            if not job.is_valid():
                msg = f"Invalid cron expression: {cron_expr}"
                raise ValueError(msg)

            cron.write()

    def _lock(self):
        """Context manager for file locking."""
        # See code example below
        ...
```

### Pattern 2: File Locking Context Manager

**What:** `fcntl.flock`-based context manager wrapping the lock file.
**When to use:** Every crontab read-modify-write cycle.

```python
import fcntl
import time
from contextlib import contextmanager

@contextmanager
def _lock(self):
    """Acquire exclusive file lock with timeout."""
    self.lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = open(self.lock_path, "w")
    deadline = time.monotonic() + 10  # D-06: 10 second timeout
    try:
        while True:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    lock_fd.close()
                    msg = "Could not acquire crontab lock within 10 seconds. Another navigator process may be modifying the crontab."
                    raise TimeoutError(msg)
                time.sleep(0.1)
        yield
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
```

### Pattern 3: Post-Write Verification (D-11)

**What:** Re-read the crontab after writing to confirm the entry was persisted.
**When to use:** After every `cron.write()` call.

```python
def _verify_entry(self, command_name: str) -> bool:
    """Re-read crontab and verify entry exists."""
    cron = CronTab(user=True)
    comment = self._make_comment(command_name)
    return len(list(cron.find_comment(comment))) > 0
```

### Pattern 4: CLI Integration with Typer

**What:** Replace the schedule() stub with full implementation.
**When to use:** The `navigator schedule` command.

```python
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
    # list_all and remove are mutually exclusive with cron
    ...
```

### Anti-Patterns to Avoid
- **Using `CronTab(tabfile='/path')` for user crontab:** Always use `CronTab(user=True)` to access the current user's crontab. Tabfile is for testing or managing arbitrary files.
- **Not using absolute paths in crontab commands:** Cron runs with a minimal PATH (`/usr/bin:/bin`). Always resolve `navigator` to its absolute path at schedule time.
- **Reading crontab outside the lock:** The lock must cover the entire read-modify-write cycle (D-07), not just the write.
- **Catching all exceptions from `setall()`:** python-crontab raises `KeyError` for parse failures and `ValueError` for range violations. Catch both specifically.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cron expression parsing | Regex parser for `* */5 0-23` etc. | python-crontab `setall()` + `is_valid()` | Cron syntax is deceptively complex (ranges, steps, names, specials like `@hourly`) |
| Crontab file I/O | `subprocess.run(['crontab', '-l'])` + string manipulation | python-crontab `CronTab(user=True)` | Handles edge cases: empty crontab, comments, environment variables, special entries |
| Crontab entry finding | Grep through rendered crontab text | python-crontab `find_comment()` | Returns CronItem objects you can modify/remove directly |
| File locking | PID files, advisory lock files | `fcntl.flock()` | Kernel-enforced, handles process crashes (lock released on fd close), no stale lockfile problem |

**Key insight:** python-crontab handles the entire crontab lifecycle (read, parse, modify, validate, write) as an atomic unit. Reimplementing any part defeats the purpose of using it.

## Common Pitfalls

### Pitfall 1: Cron PATH Does Not Include User Binary Locations
**What goes wrong:** Crontab entry with `navigator exec test-cmd` fails because cron's PATH is `/usr/bin:/bin`.
**Why it happens:** Cron runs with minimal environment, not the user's shell profile.
**How to avoid:** Always resolve `navigator` to its absolute path using `shutil.which('navigator')` at schedule time and embed the full path in the crontab entry.
**Warning signs:** Scheduled commands fail silently (check `mail` or cron logs).

### Pitfall 2: python-crontab Exception Types for Invalid Expressions
**What goes wrong:** Catching only `ValueError` misses `KeyError` from parse failures.
**Why it happens:** python-crontab raises `KeyError` when a cron field can't be parsed (e.g., `"invalid cron"`) and `ValueError` when a value is out of range (e.g., minute=99). These are different code paths.
**How to avoid:** Catch both `KeyError` and `ValueError` from `setall()`, or use a blanket `except (KeyError, ValueError)` and re-raise as a clean user-facing error.
**Warning signs:** Unhandled `KeyError` tracebacks in CLI output.

### Pitfall 3: Stale Lock File After Crash
**What goes wrong:** Lock file exists but process crashed without releasing.
**Why it happens:** Misunderstanding of `fcntl.flock` -- it's advisory and tied to the file descriptor, not the file. When the process dies, the OS closes the fd and releases the lock.
**How to avoid:** This is actually NOT a problem with `fcntl.flock`. The lock is automatically released when the file descriptor is closed or the process exits. No cleanup needed.
**Warning signs:** None -- this pitfall is a misconception. Using `fcntl.flock` correctly avoids it entirely.

### Pitfall 4: find_comment Returns Iterator, Not List
**What goes wrong:** Iterating `find_comment()` twice consumes the iterator on the first pass.
**Why it happens:** `find_comment()` returns a generator.
**How to avoid:** Always wrap in `list()`: `list(cron.find_comment(comment))`.
**Warning signs:** Second iteration over results yields nothing.

### Pitfall 5: Navigator Not Globally Installed
**What goes wrong:** `shutil.which('navigator')` returns `None` when Navigator is only in a virtualenv.
**Why it happens:** During development, navigator is in `.venv/bin/navigator` which may not be on PATH.
**How to avoid:** If `shutil.which()` returns None, check `sys.executable` parent dir or provide a `--navigator-path` fallback. For production, Navigator must be globally installed via `uv tool install` (INFRA-01).
**Warning signs:** `FileNotFoundError` at schedule time with clear error message.

### Pitfall 6: Schedule Command Needs Optional Positional Argument
**What goes wrong:** `navigator schedule --list` fails because Typer expects a required positional argument.
**Why it happens:** D-10 says `--list` works without a command name, but D-08/D-09 need a command name.
**How to avoid:** Make `command` an optional argument with `default=None`. Validate that `command` is provided when `--cron` or `--remove` is used.
**Warning signs:** Typer exits with "Missing argument" when running `navigator schedule --list`.

## Code Examples

### Scheduling a Command (Full Flow)
```python
# Source: Verified against python-crontab 3.3.0
from crontab import CronTab

cron = CronTab(user=True)

# Create entry with navigator tag
job = cron.new(
    command="/home/user/.local/bin/navigator exec my-cmd",
    comment="navigator:my-cmd",
)
job.setall("*/5 * * * *")
assert job.is_valid()

# Write to system crontab
cron.write()

# Verify (D-11)
cron2 = CronTab(user=True)
found = list(cron2.find_comment("navigator:my-cmd"))
assert len(found) == 1
```

### Removing a Schedule
```python
# Source: Verified against python-crontab 3.3.0
from crontab import CronTab

cron = CronTab(user=True)
jobs = list(cron.find_comment("navigator:my-cmd"))
for job in jobs:
    cron.remove(job)
cron.write()
```

### Listing All Navigator Schedules
```python
# Source: Verified against python-crontab 3.3.0
from crontab import CronTab

cron = CronTab(user=True)
# Find all entries with navigator: prefix in comment
for job in cron:
    if job.comment.startswith("navigator:"):
        cmd_name = job.comment.split(":", 1)[1]
        schedule = str(job.slices)
        enabled = job.is_enabled()
        print(f"{cmd_name}: {schedule} (enabled={enabled})")
```

### File Locking with Timeout
```python
# Source: Python stdlib fcntl documentation
import fcntl
import time

lock_path = Path("/home/user/.local/share/navigator/crontab.lock")
lock_path.parent.mkdir(parents=True, exist_ok=True)

fd = open(lock_path, "w")
try:
    deadline = time.monotonic() + 10
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                raise TimeoutError("Could not acquire crontab lock within 10s")
            time.sleep(0.1)

    # ... do crontab operations ...
finally:
    fcntl.flock(fd, fcntl.LOCK_UN)
    fd.close()
```

### Testing with Tabfile (Mock Crontab)
```python
# Source: Verified against python-crontab 3.3.0
from crontab import CronTab

# Use a temp file instead of real system crontab
cron = CronTab(tab="")  # In-memory, empty
job = cron.new(command="navigator exec test", comment="navigator:test")
job.setall("0 * * * *")
cron.write("/tmp/test_crontab")  # Write to file, not system

# Read back from file
cron2 = CronTab(tabfile="/tmp/test_crontab")
assert len(list(cron2.find_comment("navigator:test"))) == 1
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| subprocess crontab -l pipe | python-crontab 3.x API | Stable since 2020 | Clean CRUD without string parsing |
| PID file locking | fcntl.flock | Always available on POSIX | Kernel-enforced, crash-safe |

**Deprecated/outdated:**
- python-crontab 2.x: Minor API differences but 3.x is backward compatible. No breaking changes.

## Open Questions

1. **Store schedule info in SQLite alongside commands?**
   - What we know: The crontab IS the source of truth for whether a command is scheduled. Duplicating in SQLite risks desynchronization.
   - What's unclear: Whether `navigator show <cmd>` should display the cron schedule (it would need to read the crontab).
   - Recommendation: Do NOT store schedule info in SQLite. Read from crontab when needed. Keeps a single source of truth. The `show` command can read crontab to display schedule if needed, but this is lower priority.

2. **How to handle `navigator` not on PATH (development vs production)?**
   - What we know: During dev, navigator is at `.venv/bin/navigator`. In production, it should be globally installed via `uv tool install`.
   - What's unclear: Whether to support venv-only installs creating crontab entries.
   - Recommendation: Use `shutil.which('navigator')` and fail with clear error if not found. User must ensure navigator is on PATH (via global install or PATH configuration). This matches INFRA-01.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| crontab (system) | SCHED-01-05 | Yes | crontab from util-linux | -- |
| python-crontab | SCHED-01-04 | No (not yet added to deps) | 3.3.0 on PyPI | -- |
| fcntl (stdlib) | SCHED-04 | Yes | Python stdlib | -- |
| navigator on PATH | SCHED-05 | No (venv only) | 0.1.0 | `sys.executable` parent or error |

**Missing dependencies with no fallback:**
- python-crontab must be added to pyproject.toml dependencies

**Missing dependencies with fallback:**
- navigator not on global PATH -- acceptable during development; crontab entries will use venv path if found via `shutil.which()` in activated environment

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_scheduler.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCHED-01 | Schedule command with cron expression | unit | `uv run pytest tests/test_scheduler.py::test_schedule_command -x` | No -- Wave 0 |
| SCHED-01 | CLI `schedule --cron` invocation | unit | `uv run pytest tests/test_cli.py::TestSchedule -x` | No -- Wave 0 |
| SCHED-02 | Tagged entries in crontab with comment | unit | `uv run pytest tests/test_scheduler.py::test_tagged_entry_format -x` | No -- Wave 0 |
| SCHED-03 | Unschedule removes crontab entry | unit | `uv run pytest tests/test_scheduler.py::test_unschedule_command -x` | No -- Wave 0 |
| SCHED-03 | CLI `schedule --remove` invocation | unit | `uv run pytest tests/test_cli.py::TestScheduleRemove -x` | No -- Wave 0 |
| SCHED-04 | File-locked crontab writes | unit | `uv run pytest tests/test_scheduler.py::test_file_locking -x` | No -- Wave 0 |
| SCHED-05 | Entries use absolute navigator path | unit | `uv run pytest tests/test_scheduler.py::test_absolute_path -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_scheduler.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_scheduler.py` -- covers SCHED-01 through SCHED-05 scheduler module tests
- [ ] CLI schedule tests in `tests/test_cli.py` -- covers SCHED-01, SCHED-03 CLI integration

### Test Strategy: Mock Crontab

Use python-crontab's `CronTab(tab="")` (in-memory empty crontab) and `CronTab(tabfile=path)` for testing. This avoids touching the real system crontab entirely.

**Pattern for scheduler tests:**
```python
def test_schedule_command(tmp_path, monkeypatch):
    """Schedule creates a tagged crontab entry."""
    tab_file = tmp_path / "crontab"
    tab_file.write_text("")

    # Monkeypatch CronTab to use tabfile instead of user=True
    monkeypatch.setattr(
        "navigator.scheduler.CronTab",
        lambda **kw: CronTab(tabfile=str(tab_file)),
    )
    monkeypatch.setattr("shutil.which", lambda cmd: "/usr/local/bin/navigator")

    manager = CrontabManager(lock_path=tmp_path / "crontab.lock")
    manager.schedule("test-cmd", "*/5 * * * *")

    # Verify entry was written
    cron = CronTab(tabfile=str(tab_file))
    jobs = list(cron.find_comment("navigator:test-cmd"))
    assert len(jobs) == 1
    assert "*/5 * * * *" in str(jobs[0])
```

## Sources

### Primary (HIGH confidence)
- python-crontab 3.3.0 -- API verified by direct import and interactive testing (CronTab, CronItem, find_comment, setall, write, remove)
- Python stdlib fcntl -- verified available on Linux, LOCK_EX/LOCK_NB behavior tested
- PyPI registry -- version 3.3.0 confirmed as latest (2026-03-24)

### Secondary (MEDIUM confidence)
- [python-crontab PyPI page](https://pypi.org/project/python-crontab/) -- package metadata and description
- [python-crontab GitHub](https://github.com/guige/python-crontab) -- source code reference

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- python-crontab 3.3.0 API verified by direct testing, fcntl verified in stdlib
- Architecture: HIGH -- straightforward CRUD wrapper with file locking; patterns verified against working API
- Pitfalls: HIGH -- exception types, PATH issues, and locking semantics verified by direct testing

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (stable domain, mature libraries)
