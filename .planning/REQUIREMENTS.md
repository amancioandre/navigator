# Requirements: Navigator

**Defined:** 2026-03-23
**Core Value:** Autonomous task orchestration — registered commands run on schedule or on file changes, with the right context and secrets, without human intervention unless something fails.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Registry

- [x] **REG-01**: User can register a command with a name, prompt, environment path, secrets path, and allowed tools
- [ ] **REG-02**: User can list all registered commands with filtering by namespace
- [ ] **REG-03**: User can show details of a specific registered command
- [ ] **REG-04**: User can update any field of a registered command
- [ ] **REG-05**: User can delete a registered command (cleans up crontab entry and watchers)
- [ ] **REG-06**: User can pause a registered command (disables scheduling/watching without deleting)
- [ ] **REG-07**: User can resume a paused command
- [ ] **REG-08**: User can list commands sorted by created date for housekeeping
- [ ] **REG-09**: User can dry-run a command to see what would execute without running it
- [x] **REG-10**: Registry persists in SQLite with crash-safe atomic transactions

### Execution

- [ ] **EXEC-01**: User can run a registered command as a Claude Code subprocess with pre-configured `--allowedTools`
- [ ] **EXEC-02**: Executor reads secrets from the command's secrets path and injects them as environment variables
- [ ] **EXEC-03**: Secrets are never logged, never passed as CLI arguments, and never visible in process tables
- [ ] **EXEC-04**: Executor retries failed commands with exponential backoff (`--retries N`)
- [ ] **EXEC-05**: Each execution captures stdout/stderr to per-execution log files
- [ ] **EXEC-06**: User can view execution logs via `navigator logs <command>`
- [ ] **EXEC-07**: Executor runs commands in the registered environment path (working directory)
- [ ] **EXEC-08**: Executor builds a clean environment (not inheriting full parent env) with only declared variables
- [ ] **EXEC-09**: Executor tracks child PIDs and uses process groups for cleanup (no zombies)
- [ ] **EXEC-10**: Executor enforces timeout per command execution

### Scheduling

- [ ] **SCHED-01**: User can schedule a command with a cron expression via `navigator schedule <command> --cron <expr>`
- [ ] **SCHED-02**: Scheduled commands create tagged entries in the real system crontab (`# navigator:<id>`)
- [ ] **SCHED-03**: User can unschedule a command (removes crontab entry)
- [ ] **SCHED-04**: Crontab writes are file-locked to prevent corruption from concurrent access
- [ ] **SCHED-05**: Crontab entries invoke `navigator exec <id>` so tasks survive daemon downtime

### File Watching

- [ ] **WATCH-01**: User can register a file/folder watcher that triggers a command on changes
- [ ] **WATCH-02**: Watchers use inotify (via watchdog) with configurable debounce (default 500ms)
- [ ] **WATCH-03**: Watchers have self-trigger guards (ignore changes made by the triggered command itself)
- [ ] **WATCH-04**: Watchers support time-window constraints (e.g., only trigger between 9am-5pm)
- [ ] **WATCH-05**: Watchers support ignore patterns (editor temp files, .git, etc.)
- [ ] **WATCH-06**: Watcher daemon runs as a systemd service that survives reboots

### Chaining

- [ ] **CHAIN-01**: User can chain commands so completing one triggers the next, with shared state via environment path
- [ ] **CHAIN-02**: Chained commands run as separate Claude Code sessions (not the same session)
- [ ] **CHAIN-03**: Chain execution has configurable failure semantics (stop-on-failure default, continue option)
- [ ] **CHAIN-04**: Chain depth is limited (default 10) to prevent runaway execution
- [ ] **CHAIN-05**: Cycles are detected at registration time and rejected
- [ ] **CHAIN-06**: Each chain run gets a correlation ID for log tracing

### Namespacing

- [ ] **NS-01**: Commands are namespaced by project (`namespace:command` format)
- [ ] **NS-02**: User can create, list, and delete namespaces
- [ ] **NS-03**: Commands can chain across namespaces (e.g., `gamescout:scrape` triggers `content:generate`)
- [ ] **NS-04**: Secrets are isolated per namespace (`~/.secrets/<namespace>/`)

### Infrastructure

- [x] **INFRA-01**: Navigator installs globally via pip/uv (`navigator` CLI on PATH)
- [ ] **INFRA-02**: systemd user services for watcher daemon and future bot listener
- [ ] **INFRA-03**: `navigator doctor` verifies crontab entries, paths, permissions, and service health
- [ ] **INFRA-04**: `navigator --output json` provides machine-readable output for Claude Code agents
- [x] **INFRA-05**: Configuration file at `~/.config/navigator/config.toml`
- [ ] **INFRA-06**: `navigator install-service` generates and installs systemd unit files
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
| REG-02 | Phase 2 | Pending |
| REG-03 | Phase 2 | Pending |
| REG-04 | Phase 2 | Pending |
| REG-05 | Phase 2 | Pending |
| REG-06 | Phase 2 | Pending |
| REG-07 | Phase 2 | Pending |
| REG-08 | Phase 2 | Pending |
| REG-09 | Phase 10 | Pending |
| REG-10 | Phase 2 | Complete |
| EXEC-01 | Phase 3 | Pending |
| EXEC-02 | Phase 3 | Pending |
| EXEC-03 | Phase 3 | Pending |
| EXEC-04 | Phase 4 | Pending |
| EXEC-05 | Phase 4 | Pending |
| EXEC-06 | Phase 4 | Pending |
| EXEC-07 | Phase 3 | Pending |
| EXEC-08 | Phase 3 | Pending |
| EXEC-09 | Phase 4 | Pending |
| EXEC-10 | Phase 4 | Pending |
| SCHED-01 | Phase 5 | Pending |
| SCHED-02 | Phase 5 | Pending |
| SCHED-03 | Phase 5 | Pending |
| SCHED-04 | Phase 5 | Pending |
| SCHED-05 | Phase 5 | Pending |
| WATCH-01 | Phase 6 | Pending |
| WATCH-02 | Phase 6 | Pending |
| WATCH-03 | Phase 6 | Pending |
| WATCH-04 | Phase 6 | Pending |
| WATCH-05 | Phase 6 | Pending |
| WATCH-06 | Phase 9 | Pending |
| CHAIN-01 | Phase 8 | Pending |
| CHAIN-02 | Phase 8 | Pending |
| CHAIN-03 | Phase 8 | Pending |
| CHAIN-04 | Phase 8 | Pending |
| CHAIN-05 | Phase 8 | Pending |
| CHAIN-06 | Phase 8 | Pending |
| NS-01 | Phase 7 | Pending |
| NS-02 | Phase 7 | Pending |
| NS-03 | Phase 7 | Pending |
| NS-04 | Phase 7 | Pending |
| INFRA-01 | Phase 1 | Complete |
| INFRA-02 | Phase 9 | Pending |
| INFRA-03 | Phase 10 | Pending |
| INFRA-04 | Phase 10 | Pending |
| INFRA-05 | Phase 1 | Complete |
| INFRA-06 | Phase 9 | Pending |
| INFRA-07 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 48 total
- Mapped to phases: 48
- Unmapped: 0

---
*Requirements defined: 2026-03-23*
*Last updated: 2026-03-23 after roadmap creation*
