---
phase: 06-file-watching
plan: 01
subsystem: file-watching
tags: [watchdog, inotify, debounce, pydantic, sqlite, threading]

# Dependency graph
requires:
  - phase: 02-registry
    provides: "Command model, SQLite CRUD, DB connection with WAL mode and FK support"
  - phase: 04-execution
    provides: "execute_command function for triggering commands from watcher"
provides:
  - "Watcher and WatcherStatus models with validation in models.py"
  - "Watchers SQLite table with FK CASCADE to commands"
  - "Full CRUD operations for watchers in db.py"
  - "WatcherManager class for high-level watcher CRUD"
  - "DebouncedHandler for filesystem event debouncing"
  - "SelfTriggerGuard for preventing re-entry during execution"
  - "Time window utilities (parse_time_window, is_within_window)"
  - "make_trigger_callback wiring guard + time window + executor"
affects: [06-02-cli-watcher, 09-daemon]

# Tech tracking
tech-stack:
  added: ["watchdog>=6.0.0"]
  patterns: ["DebouncedHandler with threading.Timer for event coalescing", "SelfTriggerGuard with threading.Lock for re-entry prevention", "Per-method DB connections for thread safety"]

key-files:
  created:
    - "src/navigator/watcher.py"
    - "src/navigator/watcher_handler.py"
    - "tests/test_watcher.py"
    - "tests/test_watcher_handler.py"
  modified:
    - "src/navigator/models.py"
    - "src/navigator/db.py"
    - "pyproject.toml"

key-decisions:
  - "Per-method DB connections in WatcherManager for thread safety (watchdog handler threads)"
  - "DebouncedHandler uses daemon Timer threads to avoid blocking shutdown"
  - "Directory modified events skipped in DebouncedHandler (noisy on Linux inotify)"

patterns-established:
  - "Thread-safe guard pattern: SelfTriggerGuard with Lock for concurrent access"
  - "Debounce pattern: cancel-and-restart Timer on each event, fire after quiet period"
  - "Time window pattern: HH:MM-HH:MM with overnight support (start > end means wrap)"

requirements-completed: [WATCH-01, WATCH-02, WATCH-03, WATCH-04, WATCH-05]

# Metrics
duration: 3min
completed: 2026-03-24
---

# Phase 6 Plan 1: Watcher Core Summary

**Watchdog-based file watcher with Pydantic model, SQLite CRUD, debounced event handler, self-trigger guard, and time-window filtering**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-24T19:02:53Z
- **Completed:** 2026-03-24T19:06:10Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Watcher and WatcherStatus models with debounce_ms and active_hours validation
- Watchers SQLite table with FK CASCADE to commands, indexes, and full CRUD
- DebouncedHandler coalesces rapid filesystem events into single callback
- SelfTriggerGuard prevents re-triggering during command execution
- Time window utilities with overnight range support
- make_trigger_callback wires all guards together with executor
- 37 new unit tests (190 total), all passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Watcher model, DB schema + CRUD, and watchdog dependency** - `37c1d88` (feat)
2. **Task 2: Event handler with debounce, guard, time window, and ignore patterns** - `9806443` (feat)

_Note: TDD tasks -- tests written first (RED), then implementation (GREEN), committed together._

## Files Created/Modified
- `src/navigator/models.py` - Added WatcherStatus enum and Watcher model with validation
- `src/navigator/db.py` - Added watchers table schema, indexes, and CRUD functions
- `src/navigator/watcher.py` - WatcherManager class with register/remove/list operations
- `src/navigator/watcher_handler.py` - DebouncedHandler, SelfTriggerGuard, time window utils, make_trigger_callback
- `tests/test_watcher.py` - 18 tests for model, DB CRUD, and FK cascade
- `tests/test_watcher_handler.py` - 19 tests for debounce, guard, time window, trigger callback
- `pyproject.toml` - Added watchdog>=6.0.0 dependency

## Decisions Made
- Per-method DB connections in WatcherManager for thread safety (watchdog handler threads run in separate threads)
- DebouncedHandler uses daemon Timer threads to avoid blocking process shutdown
- Directory modified events skipped in DebouncedHandler (noisy on Linux inotify)
- make_trigger_callback opens fresh DB connection per trigger for thread safety

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Watcher core infrastructure complete, ready for Plan 02 (CLI integration)
- WatcherManager provides the CRUD API that CLI commands will call
- DebouncedHandler and make_trigger_callback ready for daemon wiring

---
*Phase: 06-file-watching*
*Completed: 2026-03-24*
