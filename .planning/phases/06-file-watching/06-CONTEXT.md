# Phase 6: File Watching - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver file/folder watching as a trigger pattern — users can register watchers that trigger commands on filesystem changes, with debounce, self-trigger guards, time-window constraints, and ignore patterns. After this phase, `navigator watch` supports full CRUD for watchers, and a watcher daemon process monitors registered paths.

</domain>

<decisions>
## Implementation Decisions

### Watcher Registration & Storage
- **D-01:** New `watchers` table in SQLite — stores watcher config (command, path, pattern, debounce, ignore patterns, active hours, status).
- **D-02:** Registration: `navigator watch <command> --path /dir --pattern "*.md"` — mirrors schedule command pattern.
- **D-03:** Unwatch: `navigator watch <command> --remove` — consistent with schedule --remove.
- **D-04:** List: `navigator watch --list` — Rich table showing path, pattern, command, status.

### Debounce & Self-Trigger Guards
- **D-05:** Timer-based debounce: accumulate events for configurable period (default 500ms), fire command once after quiet period.
- **D-06:** Default debounce: 500ms. Configurable per-watcher via `--debounce` flag (milliseconds).
- **D-07:** Self-trigger guard: track child PID + working directory during command execution; ignore filesystem events from paths modified by the triggered command.
- **D-08:** Default ignore patterns: `.git/**`, `*.swp`, `*.tmp`, `*~`, `__pycache__/**`. Configurable per-watcher via `--ignore` flag.

### Time Windows
- **D-09:** Time window format: `--active-hours "09:00-17:00"` — HH:MM range in local time.
- **D-10:** Outside window: silently skip the event, log at debug level. No queuing.
- **D-11:** Single time window per watcher this phase — keep it simple.

### Claude's Discretion
- Module organization (single `watcher.py` vs separate `watcher_db.py` + `watcher_daemon.py`)
- Whether the watcher daemon runs as a foreground process or background daemon in this phase (Phase 9 adds systemd)
- Watchdog observer configuration details
- Test strategy for filesystem events (real tmpdir vs mocked observer)
- Pydantic model for Watcher record vs simple dataclass

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project
- `.planning/PROJECT.md` — Core value, constraints
- `.planning/REQUIREMENTS.md` — WATCH-01 through WATCH-05

### Prior Phases
- `.planning/phases/02-command-registry/02-CONTEXT.md` — Command model, DB patterns
- `.planning/phases/04-execution-hardening/04-CONTEXT.md` — Executor with retry/timeout
- `src/navigator/db.py` — SQLite patterns (get_connection, init_db, parameterized queries)
- `src/navigator/executor.py` — execute_command() that watchers will trigger

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/navigator/db.py` — SQLite patterns: get_connection, init_db, parameterized queries, row_to_model
- `src/navigator/executor.py` — execute_command(cmd, config) for triggering commands
- `src/navigator/models.py` — Command model, CommandStatus enum
- `src/navigator/config.py` — NavigatorConfig, get_data_dir()

### Established Patterns
- SQLite table with get_connection + init_db (from db.py)
- Pydantic/dataclass models for records
- Lazy imports in CLI functions
- Rich Console/Table for output
- TDD approach

### Integration Points
- `src/navigator/cli.py:watch()` — stub exists, needs implementation
- `src/navigator/db.py` — extend init_db with watchers table, or separate DB module
- watchdog library — already in recommended stack (CLAUDE.md)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-file-watching*
*Context gathered: 2026-03-24*
