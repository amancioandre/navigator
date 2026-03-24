# Requirements: Navigator

**Defined:** 2026-03-23
**Core Value:** Autonomous task orchestration — registered commands run on schedule or on file changes, with the right context and secrets, without human intervention unless something fails.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Registry

- [x] **REG-01**: User can register a command with a name, prompt, environment path, secrets path, and allowed tools
- [x] **REG-02**: User can list all registered commands with filtering by namespace
- [x] **REG-03**: User can show details of a specific registered command
- [x] **REG-04**: User can update any field of a registered command
- [x] **REG-05**: User can delete a registered command (cleans up crontab entry and watchers)
- [x] **REG-06**: User can pause a registered command (disables scheduling/watching without deleting)
- [x] **REG-07**: User can resume a paused command
- [x] **REG-08**: User can list commands sorted by created date for housekeeping
- [x] **REG-09**: User can dry-run a command to see what would execute without running it
- [x] **REG-10**: Registry persists in SQLite with crash-safe atomic transactions

### Execution

- [x] **EXEC-01**: User can run a registered command as a Claude Code subprocess with pre-configured `--allowedTools`
- [x] **EXEC-02**: Executor reads secrets from the command's secrets path and injects them as environment variables
- [x] **EXEC-03**: Secrets are never logged, never passed as CLI arguments, and never visible in process tables
- [x] **EXEC-04**: Executor retries failed commands with exponential backoff (`--retries N`)
- [x] **EXEC-05**: Each execution captures stdout/stderr to per-execution log files
- [x] **EXEC-06**: User can view execution logs via `navigator logs <command>`
- [x] **EXEC-07**: Executor runs commands in the registered environment path (working directory)
- [x] **EXEC-08**: Executor builds a clean environment (not inheriting full parent env) with only declared variables
- [x] **EXEC-09**: Executor tracks child PIDs and uses process groups for cleanup (no zombies)
- [x] **EXEC-10**: Executor enforces timeout per command execution

### Scheduling

- [x] **SCHED-01**: User can schedule a command with a cron expression via `navigator schedule <command> --cron <expr>`
- [x] **SCHED-02**: Scheduled commands create tagged entries in the real system crontab (`# navigator:<id>`)
- [x] **SCHED-03**: User can unschedule a command (removes crontab entry)
- [x] **SCHED-04**: Crontab writes are file-locked to prevent corruption from concurrent access
- [x] **SCHED-05**: Crontab entries invoke `navigator exec <id>` so tasks survive daemon downtime

### File Watching

- [x] **WATCH-01**: User can register a file/folder watcher that triggers a command on changes
- [x] **WATCH-02**: Watchers use inotify (via watchdog) with configurable debounce (default 500ms)
- [x] **WATCH-03**: Watchers have self-trigger guards (ignore changes made by the triggered command itself)
- [x] **WATCH-04**: Watchers support time-window constraints (e.g., only trigger between 9am-5pm)
- [x] **WATCH-05**: Watchers support ignore patterns (editor temp files, .git, etc.)
- [x] **WATCH-06**: Watcher daemon runs as a systemd service that survives reboots

### Chaining

- [x] **CHAIN-01**: User can chain commands so completing one triggers the next, with shared state via environment path
- [x] **CHAIN-02**: Chained commands run as separate Claude Code sessions (not the same session)
- [x] **CHAIN-03**: Chain execution has configurable failure semantics (stop-on-failure default, continue option)
- [x] **CHAIN-04**: Chain depth is limited (default 10) to prevent runaway execution
- [x] **CHAIN-05**: Cycles are detected at registration time and rejected
- [x] **CHAIN-06**: Each chain run gets a correlation ID for log tracing

### Namespacing

- [x] **NS-01**: Commands are namespaced by project (`namespace:command` format)
- [x] **NS-02**: User can create, list, and delete namespaces
- [x] **NS-03**: Commands can chain across namespaces (e.g., `gamescout:scrape` triggers `content:generate`)
- [x] **NS-04**: Secrets are isolated per namespace (`~/.secrets/<namespace>/`)

### Infrastructure

- [x] **INFRA-01**: Navigator installs globally via pip/uv (`navigator` CLI on PATH)
- [x] **INFRA-02**: systemd user services for watcher daemon and future bot listener
- [x] **INFRA-03**: `navigator doctor` verifies crontab entries, paths, permissions, and service health
- [x] **INFRA-04**: `navigator --output json` provides machine-readable output for Claude Code agents
- [x] **INFRA-05**: Configuration file at `~/.config/navigator/config.toml`
- [x] **INFRA-06**: `navigator install-service` generates and installs systemd unit files
- [x] **INFRA-07**: Absolute path resolution at registration time (prevents stale crontab refs after reinstall)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Remote Access

- **REMOTE-01**: Messaging bot (Telegram/Discord) with full CRUD operations via long-polling
- **REMOTE-02**: User ID allowlist for bot authentication (reject unauthorized silently)
- **REMOTE-03**: Push notifications on task failure via messaging bot
- **REMOTE-04**: Rate limiting on bot commands
- **REMOTE-05**: Bot calls the same core functions as CLI (thin adapter, not separate logic)

### Claude Code Integration

- **CCINT-01**: Navigator exposed as a Claude Code skill for use from other sessions
- **CCINT-02**: Execution history with queryable past runs
- **CCINT-03**: `navigator ps` to show currently running commands
- **CCINT-04**: `navigator repair-crontab` to fix stale entries

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Web dashboard / GUI | Massive surface area, security exposure, violates privacy constraint. CLI + future bot covers all interaction |
| Internal cron reimplementation | System crontab is battle-tested. Reimplementing adds complexity and breaks tool visibility |
| Multi-user / RBAC | Single-user private system. Zero validated need for auth/permissions |
| Plugin / extension system | Premature abstraction. Well-structured codebase is sufficient; add only after 3+ concrete extension requests |
| Workflow DSL / DAG engine | Navigator chains are linear with fan-out at most. Full DAG engines are enormously complex |
| Docker isolation per command | Massive overhead for a personal tool. Trust the single-user environment |
| Real-time WebSocket streaming | Requires persistent server, violates no-public-exposure constraint |
| Auto-discovery of tasks | Magic behavior is hard to debug. Explicit registration is clearer |
| Public internet exposure | All remote access via third-party messaging APIs only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| REG-01 | Phase 2 | Complete |
| REG-02 | Phase 2 | Complete |
| REG-03 | Phase 2 | Complete |
| REG-04 | Phase 2 | Complete |
| REG-05 | Phase 2 | Complete |
| REG-06 | Phase 2 | Complete |
| REG-07 | Phase 2 | Complete |
| REG-08 | Phase 2 | Complete |
| REG-09 | Phase 10 | Complete |
| REG-10 | Phase 2 | Complete |
| EXEC-01 | Phase 3 | Complete |
| EXEC-02 | Phase 3 | Complete |
| EXEC-03 | Phase 3 | Complete |
| EXEC-04 | Phase 4 | Complete |
| EXEC-05 | Phase 4 | Complete |
| EXEC-06 | Phase 4 | Complete |
| EXEC-07 | Phase 3 | Complete |
| EXEC-08 | Phase 3 | Complete |
| EXEC-09 | Phase 4 | Complete |
| EXEC-10 | Phase 4 | Complete |
| SCHED-01 | Phase 5 | Complete |
| SCHED-02 | Phase 5 | Complete |
| SCHED-03 | Phase 5 | Complete |
| SCHED-04 | Phase 5 | Complete |
| SCHED-05 | Phase 5 | Complete |
| WATCH-01 | Phase 6 | Complete |
| WATCH-02 | Phase 6 | Complete |
| WATCH-03 | Phase 6 | Complete |
| WATCH-04 | Phase 6 | Complete |
| WATCH-05 | Phase 6 | Complete |
| WATCH-06 | Phase 9 | Complete |
| CHAIN-01 | Phase 8 | Complete |
| CHAIN-02 | Phase 8 | Complete |
| CHAIN-03 | Phase 8 | Complete |
| CHAIN-04 | Phase 8 | Complete |
| CHAIN-05 | Phase 8 | Complete |
| CHAIN-06 | Phase 8 | Complete |
| NS-01 | Phase 7 | Complete |
| NS-02 | Phase 7 | Complete |
| NS-03 | Phase 7 | Complete |
| NS-04 | Phase 7 | Complete |
| INFRA-01 | Phase 1 | Complete |
| INFRA-02 | Phase 9 | Complete |
| INFRA-03 | Phase 10 | Complete |
| INFRA-04 | Phase 10 | Complete |
| INFRA-05 | Phase 1 | Complete |
| INFRA-06 | Phase 9 | Complete |
| INFRA-07 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 48 total
- Mapped to phases: 48
- Unmapped: 0

---
*Requirements defined: 2026-03-23*
*Last updated: 2026-03-23 after roadmap creation*
