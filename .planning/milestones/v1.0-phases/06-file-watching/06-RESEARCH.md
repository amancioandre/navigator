# Phase 6: File Watching - Research

**Researched:** 2026-03-24
**Domain:** Filesystem monitoring, event-driven command triggering, watchdog library
**Confidence:** HIGH

## Summary

Phase 6 adds file/folder watching as a trigger pattern for Navigator commands. Users register watchers that monitor filesystem paths via inotify (through the watchdog library) and trigger registered commands on changes -- with debounce, self-trigger guards, time-window constraints, and ignore patterns. The implementation follows the same SQLite + Pydantic + Typer CLI patterns established in phases 1-5.

The watchdog library (v6.0.0) provides `Observer` (threaded filesystem monitor) and `PatternMatchingEventHandler` (glob-based event filtering) which directly address WATCH-02 and WATCH-05. Debounce (WATCH-02), self-trigger guards (WATCH-03), and time-window constraints (WATCH-04) require custom logic on top of watchdog's event dispatch. The watcher daemon runs as a foreground process in this phase; systemd integration is deferred to Phase 9 (WATCH-06).

**Primary recommendation:** Use watchdog's `PatternMatchingEventHandler` with custom debounce via `threading.Timer`, a PID/path-based self-trigger guard, and time-window checking in the event dispatch pipeline. Store watcher config in a new `watchers` SQLite table following the existing `db.py` patterns.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** New `watchers` table in SQLite -- stores watcher config (command, path, pattern, debounce, ignore patterns, active hours, status).
- **D-02:** Registration: `navigator watch <command> --path /dir --pattern "*.md"` -- mirrors schedule command pattern.
- **D-03:** Unwatch: `navigator watch <command> --remove` -- consistent with schedule --remove.
- **D-04:** List: `navigator watch --list` -- Rich table showing path, pattern, command, status.
- **D-05:** Timer-based debounce: accumulate events for configurable period (default 500ms), fire command once after quiet period.
- **D-06:** Default debounce: 500ms. Configurable per-watcher via `--debounce` flag (milliseconds).
- **D-07:** Self-trigger guard: track child PID + working directory during command execution; ignore filesystem events from paths modified by the triggered command.
- **D-08:** Default ignore patterns: `.git/**`, `*.swp`, `*.tmp`, `*~`, `__pycache__/**`. Configurable per-watcher via `--ignore` flag.
- **D-09:** Time window format: `--active-hours "09:00-17:00"` -- HH:MM range in local time.
- **D-10:** Outside window: silently skip the event, log at debug level. No queuing.
- **D-11:** Single time window per watcher this phase -- keep it simple.

### Claude's Discretion
- Module organization (single `watcher.py` vs separate `watcher_db.py` + `watcher_daemon.py`)
- Whether the watcher daemon runs as a foreground process or background daemon in this phase (Phase 9 adds systemd)
- Watchdog observer configuration details
- Test strategy for filesystem events (real tmpdir vs mocked observer)
- Pydantic model for Watcher record vs simple dataclass

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WATCH-01 | User can register a file/folder watcher that triggers a command on changes | watchdog Observer + PatternMatchingEventHandler; new `watchers` SQLite table; CLI `navigator watch` subcommand following schedule pattern |
| WATCH-02 | Watchers use inotify (via watchdog) with configurable debounce (default 500ms) | watchdog uses InotifyObserver on Linux; custom `threading.Timer` debounce pattern; per-watcher configurable delay |
| WATCH-03 | Watchers have self-trigger guards (ignore changes made by triggered command) | Track child PID via executor; record working directory; filter events originating from command's cwd during execution |
| WATCH-04 | Watchers support time-window constraints (e.g., only trigger 9am-5pm) | Parse HH:MM-HH:MM format; check `datetime.now().time()` against window before dispatching; log skipped events at debug |
| WATCH-05 | Watchers support ignore patterns (editor temp files, .git, etc.) | watchdog's `PatternMatchingEventHandler` has built-in `ignore_patterns` parameter; combine with user-configurable patterns |

</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Tech stack:** Python >=3.12, uv for package management, hatchling build backend
- **Libraries:** watchdog 6.0.0 (already in recommended stack), Pydantic 2.12+, Typer 0.24+, Rich 14+
- **DB:** SQLite with WAL mode, parameterized queries, `with conn:` for atomic transactions
- **CLI pattern:** Lazy imports inside CLI commands, Rich Console/Table for output
- **Testing:** pytest with `uv run pytest`, TDD approach
- **Linting:** ruff (replaces black+isort+flake8)
- **Avoid:** APScheduler, Celery, schedule library, Flask/FastAPI, Poetry, pip directly

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| watchdog | 6.0.0 | Filesystem monitoring via inotify | Only serious Python filesystem watcher. Uses inotify on Linux, cross-platform. Provides Observer thread + event handler classes with built-in pattern matching. |
| sqlite3 | stdlib | Watcher config persistence | Already used for command registry. Same get_connection/init_db pattern. |
| threading | stdlib | Debounce timers, daemon thread management | Timer-based debounce requires threading.Timer. Observer itself is a thread. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pydantic | 2.12+ | Watcher model validation | Validate watcher records (path exists, debounce >0, time window format). Already in project dependencies. |
| logging | stdlib | Debug-level event logging | D-10 requires debug logging for skipped events outside time window. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PatternMatchingEventHandler | RegexMatchingEventHandler | Regex is more powerful but glob patterns are what users expect for file matching. D-02 uses glob syntax (`"*.md"`). |
| threading.Timer debounce | asyncio debounce | The executor is sync (subprocess.Popen). Observer callbacks are sync. No benefit to async here; adds complexity. |

**Installation:**
```bash
uv add watchdog>=6.0.0
```

**Version verification:** watchdog 6.0.0 released 2024-11-01 (verified via PyPI). Latest stable. Already listed in CLAUDE.md recommended stack.

## Architecture Patterns

### Recommended Module Organization

Split into two modules for separation of concerns (recommended discretion choice):

```
src/navigator/
    watcher.py          # WatcherManager class: CRUD for watchers table + daemon orchestration
    watcher_handler.py  # DebouncedHandler: watchdog event handler with debounce, self-trigger guard, time window
```

**Rationale:** The DB/CRUD logic (watcher.py) is pure and easily testable. The event handler logic (watcher_handler.py) has threading and timing concerns that benefit from isolation. This follows the project's pattern of `scheduler.py` (CrontabManager) being a focused module.

Alternative: single `watcher.py` with both CRUD and handler. Acceptable for this scope, but harder to test the handler independently.

### Recommended Watcher Model

Use Pydantic (consistent with Command model in models.py):

```python
class WatcherStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"

class Watcher(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    command_name: str          # FK to commands.name
    watch_path: Path           # Directory to watch
    patterns: list[str] = Field(default_factory=lambda: ["*"])  # Glob patterns
    ignore_patterns: list[str] = Field(
        default_factory=lambda: [".git/**", "*.swp", "*.tmp", "*~", "__pycache__/**"]
    )
    debounce_ms: int = 500
    active_hours: str | None = None  # "HH:MM-HH:MM" or None for always
    recursive: bool = True
    status: WatcherStatus = WatcherStatus.ACTIVE
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
```

### Pattern 1: Timer-Based Debounce (D-05, D-06)

**What:** Accumulate rapid filesystem events and fire the command once after a quiet period.
**When to use:** Every watcher event dispatch.
**Example:**
```python
import threading
from collections.abc import Callable

class DebouncedHandler(PatternMatchingEventHandler):
    """Watchdog handler with per-watcher debounce via threading.Timer."""

    def __init__(
        self,
        callback: Callable[[], None],
        debounce_seconds: float,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._callback = callback
        self._debounce = debounce_seconds
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def on_any_event(self, event):
        # Skip directory events for modified (noisy on Linux)
        if event.is_directory and event.event_type == "modified":
            return
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce, self._fire)
            self._timer.daemon = True
            self._timer.start()

    def _fire(self):
        self._callback()
```

### Pattern 2: Self-Trigger Guard (D-07)

**What:** Track when a triggered command is executing and ignore events from its working directory.
**When to use:** Before dispatching debounced callback.

```python
class SelfTriggerGuard:
    """Prevents re-triggering when the watched command modifies watched files."""

    def __init__(self):
        self._executing: bool = False
        self._lock = threading.Lock()

    def set_executing(self, value: bool) -> None:
        with self._lock:
            self._executing = value

    @property
    def is_executing(self) -> bool:
        with self._lock:
            return self._executing
```

The callback checks `guard.is_executing` before calling `execute_command`. The guard is set to True before execution and False after. This is simpler and more reliable than tracking PIDs and comparing paths -- since the watcher watches the same path the command operates in, any event during execution is a self-trigger.

### Pattern 3: Time Window Check (D-09, D-10)

**What:** Parse "HH:MM-HH:MM" and check current local time.
**When to use:** Before dispatching the command in the debounced callback.

```python
from datetime import datetime, time

def parse_time_window(window_str: str) -> tuple[time, time]:
    """Parse 'HH:MM-HH:MM' into (start, end) time objects."""
    start_str, end_str = window_str.split("-")
    start = datetime.strptime(start_str.strip(), "%H:%M").time()
    end = datetime.strptime(end_str.strip(), "%H:%M").time()
    return start, end

def is_within_window(window_str: str | None) -> bool:
    """Check if current local time is within the active window."""
    if window_str is None:
        return True
    start, end = parse_time_window(window_str)
    now = datetime.now().time()
    if start <= end:
        return start <= now <= end
    # Overnight window (e.g., "22:00-06:00")
    return now >= start or now <= end
```

### Pattern 4: Daemon Foreground Process

**What:** The watcher daemon runs as a foreground process that loads all active watchers and monitors them.
**When to use:** `navigator watch --start` or similar CLI command to start the daemon.

```python
def run_daemon(config: NavigatorConfig) -> None:
    """Start the watcher daemon -- blocks until interrupted."""
    observer = Observer()
    # Load all active watchers from DB
    watchers = get_active_watchers(conn)
    for w in watchers:
        handler = DebouncedHandler(
            callback=make_trigger_callback(w, config),
            debounce_seconds=w.debounce_ms / 1000.0,
            patterns=w.patterns,
            ignore_patterns=w.ignore_patterns,
        )
        observer.schedule(handler, str(w.watch_path), recursive=w.recursive)
    observer.start()
    try:
        while observer.is_alive():
            observer.join(timeout=1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

### Anti-Patterns to Avoid
- **Polling instead of inotify:** watchdog defaults to inotify on Linux. Never use `PollingObserver` unless on a network filesystem -- it wastes CPU.
- **No debounce:** File saves often produce multiple events (write, close, modify). Without debounce, the command fires multiple times per save.
- **Blocking in event handler:** Watchdog event handlers run in the Observer thread. Never call `execute_command` directly in `on_any_event` -- it blocks all event processing. Use the debounce timer to fire in a separate thread, or dispatch to a worker thread.
- **Global observer state:** Each watcher should have its own handler instance. Do not share mutable state across handlers without locks.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Filesystem monitoring | Custom inotify wrapper | watchdog Observer | Handles platform differences, recursive watching, event deduplication |
| Glob pattern matching | Custom fnmatch logic | watchdog PatternMatchingEventHandler | Built-in ignore_patterns parameter, tested edge cases |
| Timer debounce | Custom time tracking | threading.Timer with cancel/restart | Stdlib, thread-safe, well-understood pattern |
| Time parsing | Custom string parsing | datetime.strptime | Handles validation, raises ValueError on bad input |

**Key insight:** watchdog already handles the two hardest parts (inotify abstraction and pattern matching). The custom code is focused on debounce, self-trigger guards, and time windows -- all relatively straightforward with stdlib threading.

## Common Pitfalls

### Pitfall 1: Multiple Events Per File Save
**What goes wrong:** A single file save in an editor produces 2-4 events (modified, closed, sometimes created+deleted for atomic saves). Without debounce, the command fires multiple times.
**Why it happens:** Editors use different save strategies (direct write, write-to-temp-then-rename, backup+write).
**How to avoid:** Timer-based debounce (D-05) with 500ms default handles this. The timer resets on each event and only fires after the quiet period.
**Warning signs:** Command executes 2-3 times per single file edit.

### Pitfall 2: Observer Thread Blocking
**What goes wrong:** If execute_command is called synchronously in the event handler, the observer thread blocks. No further events are processed until execution completes (could be minutes).
**Why it happens:** Watchdog dispatches events from its internal thread.
**How to avoid:** The debounce timer's callback already runs in a new thread (threading.Timer creates a new thread). Ensure the callback does not rejoin the observer thread.
**Warning signs:** Events queue up and all fire at once after a command finishes.

### Pitfall 3: Self-Trigger Infinite Loop
**What goes wrong:** Command modifies watched files, which triggers the watcher, which runs the command again, ad infinitum.
**Why it happens:** No guard against events caused by the triggered command itself.
**How to avoid:** D-07 self-trigger guard. Set a flag before execution, clear after. Skip events while flag is set. Simple boolean guard is sufficient because the debounce timer serializes dispatches anyway.
**Warning signs:** Command keeps running in a loop, high CPU usage.

### Pitfall 4: Stale Watchers After Command Deletion
**What goes wrong:** A command is deleted (REG-05) but its watcher remains in the database and active in the daemon.
**Why it happens:** No cleanup cascade.
**How to avoid:** Add watcher cleanup to the command delete flow (similar to how schedule delete removes crontab entries). Also validate command exists when daemon loads watchers.
**Warning signs:** Daemon errors when trying to execute a deleted command.

### Pitfall 5: SQLite Connection from Multiple Threads
**What goes wrong:** The daemon runs watchdog in a thread, debounce timers fire in threads, all trying to access SQLite.
**Why it happens:** sqlite3 connections are not thread-safe by default.
**How to avoid:** Create a new connection per operation (the existing pattern in CLI commands), or use `check_same_thread=False` with a lock. The per-operation pattern is simpler and consistent with the project.
**Warning signs:** "ProgrammingError: SQLite objects created in a thread can only be used in that same thread."

### Pitfall 6: inotify Watch Limit
**What goes wrong:** Recursive watching on large directories can exceed the Linux inotify watch limit (default 8192).
**Why it happens:** Each subdirectory consumes one inotify watch.
**How to avoid:** Document the limit. For this personal tool, the default is usually sufficient. If needed, `sudo sysctl fs.inotify.max_user_watches=65536`.
**Warning signs:** `OSError: [Errno 28] inotify watch limit reached`.

## Code Examples

### SQLite Watchers Table Schema
```sql
-- Source: Follows db.py pattern (D-01)
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
);
CREATE INDEX IF NOT EXISTS idx_watchers_command ON watchers(command_name);
CREATE INDEX IF NOT EXISTS idx_watchers_status ON watchers(status);
```

Note: `patterns` and `ignore_patterns` are stored as JSON text (same pattern as `allowed_tools` in commands table). `recursive` is stored as integer (SQLite boolean convention). Foreign key with CASCADE ensures D-04 cleanup on command deletion.

### CLI Watch Command Pattern
```python
# Source: Follows schedule command pattern in cli.py
@app.command()
def watch(
    command: str | None = typer.Argument(None, help="Command name"),
    path: str | None = typer.Option(None, "--path", help="Directory to watch"),
    pattern: str | None = typer.Option(None, "--pattern", help="Glob pattern"),
    debounce: int = typer.Option(500, "--debounce", help="Debounce in ms"),
    ignore: list[str] | None = typer.Option(None, "--ignore", help="Ignore pattern"),
    active_hours: str | None = typer.Option(None, "--active-hours", help="HH:MM-HH:MM"),
    remove: bool = typer.Option(False, "--remove", help="Remove watcher"),
    list_all: bool = typer.Option(False, "--list", help="List all watchers"),
    start: bool = typer.Option(False, "--start", help="Start watcher daemon"),
) -> None:
    """Register a file watcher or manage the watcher daemon."""
```

### Trigger Callback Factory
```python
# Source: Integration between watcher and executor
def make_trigger_callback(
    watcher: Watcher,
    config: NavigatorConfig,
    guard: SelfTriggerGuard,
) -> Callable[[], None]:
    """Create a callback that executes the watched command with guards."""
    def callback():
        if guard.is_executing:
            logger.debug("Skipping event for '%s': command still executing", watcher.command_name)
            return
        if not is_within_window(watcher.active_hours):
            logger.debug("Skipping event for '%s': outside active hours", watcher.command_name)
            return
        # Load command from DB (fresh connection per invocation -- thread safety)
        conn = get_connection(config.db_path)
        try:
            init_db(conn)
            cmd = get_command_by_name(conn, watcher.command_name)
            if cmd is None or cmd.status == "paused":
                logger.debug("Skipping: command '%s' not found or paused", watcher.command_name)
                return
        finally:
            conn.close()
        guard.set_executing(True)
        try:
            execute_command(cmd, config)
        finally:
            guard.set_executing(False)
    return callback
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| watchdog PollingObserver | watchdog InotifyObserver (default on Linux) | Always default on Linux | No CPU waste from polling; instant event detection |
| watchdog < 4.0 (sync only) | watchdog 6.0.0 (thread-based Observer) | v4.0+ | Stable threaded observer, Python 3.9+ required |
| Manual inotify-simple | watchdog abstraction | N/A | Cross-platform, recursive watching handled |

**Deprecated/outdated:**
- watchdog `Watchmedo` CLI: Not relevant for this project (we build our own daemon)
- `Observer.daemon` attribute: Observer thread is daemonic by default in recent versions

## Open Questions

1. **Daemon restart on watcher changes**
   - What we know: The daemon loads watchers at startup. If a user adds/removes a watcher while the daemon is running, the daemon would not pick it up.
   - What's unclear: Whether to support hot-reload in this phase.
   - Recommendation: For Phase 6, require daemon restart after watcher changes. Hot-reload (e.g., via signal or polling DB for changes) can be added in Phase 9 with systemd integration. This keeps the daemon simple.

2. **Multiple watchers per command**
   - What we know: D-01 says "stores watcher config (command, path, pattern...)". Schema allows multiple watchers per command.
   - What's unclear: Whether a command should have at most one watcher.
   - Recommendation: Allow multiple watchers per command (e.g., watch different directories). The schema supports it via separate rows. No artificial limit needed.

3. **Overnight time windows**
   - What we know: D-09 specifies "HH:MM-HH:MM" format. D-11 says single window.
   - What's unclear: Whether "22:00-06:00" should mean "10pm to 6am" (overnight).
   - Recommendation: Support overnight windows by checking `now >= start OR now <= end` when start > end. Simple logic, no user confusion.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_watcher.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WATCH-01 | Register/list/remove watchers via CLI and DB | unit + integration | `uv run pytest tests/test_watcher.py -x -k "register or list or remove"` | Wave 0 |
| WATCH-02 | Debounce fires once after quiet period | unit | `uv run pytest tests/test_watcher_handler.py -x -k "debounce"` | Wave 0 |
| WATCH-03 | Self-trigger guard blocks events during execution | unit | `uv run pytest tests/test_watcher_handler.py -x -k "self_trigger"` | Wave 0 |
| WATCH-04 | Time window check allows/blocks events | unit | `uv run pytest tests/test_watcher_handler.py -x -k "time_window"` | Wave 0 |
| WATCH-05 | Ignore patterns filter events | unit | `uv run pytest tests/test_watcher_handler.py -x -k "ignore"` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_watcher.py tests/test_watcher_handler.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_watcher.py` -- covers WATCH-01 (CRUD, CLI integration)
- [ ] `tests/test_watcher_handler.py` -- covers WATCH-02, WATCH-03, WATCH-04, WATCH-05 (debounce, guard, time window, ignore)
- [ ] `watchdog` dependency: `uv add watchdog>=6.0.0` -- not yet in pyproject.toml

### Test Strategy Recommendation (Discretion Area)

**Use real tmpdir with watchdog for integration tests, mock for unit tests:**

- **Unit tests (handler logic):** Test DebouncedHandler, SelfTriggerGuard, time window parsing, and ignore pattern behavior by calling handler methods directly with constructed `FileSystemEvent` objects. No real filesystem needed. Use `threading.Event` to assert debounce timing.
- **Integration tests (CLI + DB):** Use `tmp_config_dir` fixture (existing pattern) to test watcher CRUD. No watchdog needed.
- **Smoke test (optional):** One test that creates a real tmpdir, starts an Observer, writes a file, and asserts the callback fires. Use `threading.Event.wait(timeout=2)` for synchronization. Mark with `@pytest.mark.slow` if desired.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| watchdog | WATCH-01, WATCH-02 | Not installed | -- | Must install: `uv add watchdog>=6.0.0` |
| sqlite3 | WATCH-01 (storage) | Available | stdlib | -- |
| threading | WATCH-02 (debounce) | Available | stdlib | -- |
| inotify | WATCH-02 (Linux backend) | Available | kernel | -- |

**Missing dependencies with no fallback:**
- watchdog must be added to pyproject.toml dependencies

**Missing dependencies with fallback:**
- None

## Sources

### Primary (HIGH confidence)
- [watchdog PyPI](https://pypi.org/project/watchdog/) -- version 6.0.0, release date 2024-11-01
- [watchdog API docs](https://python-watchdog.readthedocs.io/en/stable/api.html) -- Observer, PatternMatchingEventHandler, event classes
- [watchdog GitHub](https://github.com/gorakhargosh/watchdog) -- source of truth for API behavior
- Project source: `src/navigator/db.py`, `src/navigator/executor.py`, `src/navigator/scheduler.py` -- established patterns

### Secondary (MEDIUM confidence)
- [DEV.to watchdog guide](https://dev.to/devasservice/mastering-file-system-monitoring-with-watchdog-in-python-483c) -- debounce pattern with threading.Timer
- [Developer Service Blog](https://developer-service.blog/mastering-file-system-monitoring-with-watchdog-in-python/) -- event handler patterns

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- watchdog is the only serious Python filesystem watcher, already in recommended stack
- Architecture: HIGH -- follows established project patterns (SQLite CRUD, Typer CLI, Pydantic models), threading.Timer debounce is well-understood
- Pitfalls: HIGH -- inotify behavior, thread safety, and self-trigger loops are well-documented problems with known solutions

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (stable domain, watchdog 6.0.0 is mature)
