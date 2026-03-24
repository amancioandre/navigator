# Roadmap: Navigator

## Overview

Navigator delivers autonomous task orchestration in 10 phases, starting from a pip-installable package skeleton, building up the command registry and execution engine, then layering scheduling, file watching, namespacing, chaining, daemon persistence, and operational tooling. Each phase delivers a coherent, testable capability. The ordering ensures that foundational components (registry, executor) are solid before dependent features (scheduling, chaining, watchers) build on top.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Project Scaffold** - Installable Python package with CLI entry point and configuration
- [ ] **Phase 2: Command Registry** - Full CRUD for registered commands backed by SQLite
- [ ] **Phase 3: Execution Core** - Run registered commands as Claude Code subprocesses with secrets and clean environments
- [ ] **Phase 4: Execution Hardening** - Retry, timeouts, logging, and process lifecycle management
- [ ] **Phase 5: Cron Scheduling** - Schedule commands via real system crontab with lock-safe writes
- [ ] **Phase 6: File Watching** - Trigger commands on filesystem changes with debounce and guards
- [ ] **Phase 7: Namespacing** - Multi-project command isolation with per-namespace secrets
- [ ] **Phase 8: Command Chaining** - Sequential command triggers with depth limits and cycle detection
- [ ] **Phase 9: Daemon and systemd** - Persistent watcher daemon and systemd service installation
- [ ] **Phase 10: Operational Polish** - Health checks, JSON output, and dry-run for Claude Code agents

## Phase Details

### Phase 1: Project Scaffold
**Goal**: Navigator is installable and responds to CLI commands
**Depends on**: Nothing (first phase)
**Requirements**: INFRA-01, INFRA-05, INFRA-07
**Success Criteria** (what must be TRUE):
  1. User can run `pip install .` (or `uv tool install .`) and get a `navigator` command on PATH
  2. User can run `navigator --help` and see available subcommands
  3. Configuration file at `~/.config/navigator/config.toml` is created on first run with sensible defaults
  4. All internal path references are resolved to absolute paths at registration time
**Plans**: 2 plans
Plans:
- [x] 01-01-PLAN.md — Package skeleton, CLI entry point with 8 subcommand stubs, test infrastructure
- [x] 01-02-PLAN.md — Config system with TOML persistence and absolute path resolution

### Phase 2: Command Registry
**Goal**: Users can register, browse, and manage commands through the CLI
**Depends on**: Phase 1
**Requirements**: REG-01, REG-02, REG-03, REG-04, REG-05, REG-06, REG-07, REG-08, REG-10
**Success Criteria** (what must be TRUE):
  1. User can register a command with name, prompt, environment path, secrets path, and allowed tools
  2. User can list, show, update, and delete registered commands
  3. User can pause and resume a command without deleting it
  4. User can list commands sorted by created date for housekeeping
  5. Registry data persists across restarts in SQLite with crash-safe atomic writes
**Plans**: 2 plans
Plans:
- [x] 02-01-PLAN.md — Command model, SQLite database layer, and data layer tests
- [x] 02-02-PLAN.md — All 7 CLI subcommands (register, list, show, update, delete, pause, resume) and CLI integration tests

### Phase 3: Execution Core
**Goal**: Registered commands run as Claude Code subprocesses with proper secrets and environment isolation
**Depends on**: Phase 2
**Requirements**: EXEC-01, EXEC-02, EXEC-03, EXEC-07, EXEC-08
**Success Criteria** (what must be TRUE):
  1. User can run `navigator exec <command>` and it launches a Claude Code subprocess with the registered `--allowedTools`
  2. Secrets from the command's secrets path are injected as environment variables into the subprocess
  3. Secrets never appear in logs, CLI arguments, or process tables
  4. Subprocess runs in a clean environment (only declared variables) in the registered working directory
**Plans**: 2 plans
Plans:
- [x] 03-01-PLAN.md — Secrets module, executor module with environment isolation, and unit tests
- [x] 03-02-PLAN.md — Wire exec CLI subcommand to executor with CLI integration tests

### Phase 4: Execution Hardening
**Goal**: Executions are robust with retry, logging, timeouts, and clean process lifecycle
**Depends on**: Phase 3
**Requirements**: EXEC-04, EXEC-05, EXEC-06, EXEC-09, EXEC-10
**Success Criteria** (what must be TRUE):
  1. Failed commands retry with exponential backoff up to the configured retry count
  2. Each execution captures stdout/stderr to per-execution log files
  3. User can view execution logs via `navigator logs <command>`
  4. Long-running commands are terminated after the configured timeout
  5. Child processes are tracked by PID and cleaned up via process groups (no zombies)
**Plans**: 2 plans
Plans:
- [x] 04-01-PLAN.md — Execution engine hardening: Popen with process groups, retry, timeout, execution logging module
- [x] 04-02-PLAN.md — CLI wiring: --timeout/--retries flags on exec, navigator logs command

### Phase 5: Cron Scheduling
**Goal**: Users can schedule commands to run automatically via the system crontab
**Depends on**: Phase 4
**Requirements**: SCHED-01, SCHED-02, SCHED-03, SCHED-04, SCHED-05
**Success Criteria** (what must be TRUE):
  1. User can schedule a command with `navigator schedule <command> --cron <expr>`
  2. Scheduled commands appear as tagged entries in the real system crontab (`# navigator:<id>`)
  3. User can unschedule a command and the crontab entry is removed
  4. Concurrent crontab writes are file-locked to prevent corruption
  5. Crontab entries invoke `navigator exec <id>` so scheduled tasks work even if the daemon is down
**Plans**: 2 plans
Plans:
- [ ] 05-01-PLAN.md -- CrontabManager module with file locking, scheduler tests, python-crontab dependency
- [ ] 05-02-PLAN.md -- Wire schedule CLI command (--cron, --remove, --list) with integration tests

### Phase 6: File Watching
**Goal**: Commands can be triggered by filesystem changes with proper debounce and safety guards
**Depends on**: Phase 4
**Requirements**: WATCH-01, WATCH-02, WATCH-03, WATCH-04, WATCH-05
**Success Criteria** (what must be TRUE):
  1. User can register a file/folder watcher that triggers a command on changes
  2. Watchers debounce rapid events (configurable, default 500ms) using inotify via watchdog
  3. Changes made by the triggered command itself do not re-trigger the watcher
  4. Watchers support time-window constraints (e.g., only trigger between 9am-5pm)
  5. Watchers support ignore patterns for editor temp files, .git, etc.
**Plans**: TBD

### Phase 7: Namespacing
**Goal**: Commands are organized by project with isolated secrets and cross-namespace visibility
**Depends on**: Phase 2
**Requirements**: NS-01, NS-02, NS-03, NS-04
**Success Criteria** (what must be TRUE):
  1. User can register commands in `namespace:command` format
  2. User can create, list, and delete namespaces
  3. Commands can reference commands in other namespaces
  4. Secrets are isolated per namespace under `~/.secrets/<namespace>/`
**Plans**: TBD

### Phase 8: Command Chaining
**Goal**: Completing one command can automatically trigger the next with shared state and safety limits
**Depends on**: Phase 4, Phase 7
**Requirements**: CHAIN-01, CHAIN-02, CHAIN-03, CHAIN-04, CHAIN-05, CHAIN-06
**Success Criteria** (what must be TRUE):
  1. User can chain commands so completing one triggers the next with shared state via environment path
  2. Chained commands run as separate Claude Code sessions
  3. Chain failure semantics are configurable (stop-on-failure default, continue option)
  4. Chain depth is limited (default 10) and cycles are detected and rejected at registration time
  5. Each chain run gets a correlation ID visible in logs for tracing
**Plans**: TBD

### Phase 9: Daemon and systemd
**Goal**: File watchers and future services survive reboots as systemd-managed daemons
**Depends on**: Phase 6
**Requirements**: WATCH-06, INFRA-02, INFRA-06
**Success Criteria** (what must be TRUE):
  1. Watcher daemon runs as a systemd user service that starts on boot
  2. User can run `navigator install-service` to generate and install systemd unit files
  3. Service restarts automatically on failure
  4. Daemon survives reboots and resumes watching registered paths
**Plans**: TBD

### Phase 10: Operational Polish
**Goal**: Navigator is introspectable by humans and Claude Code agents with health checks and machine-readable output
**Depends on**: Phase 5, Phase 9
**Requirements**: REG-09, INFRA-03, INFRA-04
**Success Criteria** (what must be TRUE):
  1. User can dry-run a command to see what would execute without running it
  2. `navigator doctor` verifies crontab entries, paths, permissions, and service health
  3. `navigator --output json` provides machine-readable output for Claude Code agents
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10
(Phases 5 and 6 can run in parallel after Phase 4; Phase 7 can start after Phase 2)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Project Scaffold | 2/2 | Complete | 2026-03-24 |
| 2. Command Registry | 0/2 | Planning | - |
| 3. Execution Core | 0/2 | Planning | - |
| 4. Execution Hardening | 0/2 | Planning | - |
| 5. Cron Scheduling | 0/2 | Planning | - |
| 6. File Watching | 0/TBD | Not started | - |
| 7. Namespacing | 0/TBD | Not started | - |
| 8. Command Chaining | 0/TBD | Not started | - |
| 9. Daemon and systemd | 0/TBD | Not started | - |
| 10. Operational Polish | 0/TBD | Not started | - |
