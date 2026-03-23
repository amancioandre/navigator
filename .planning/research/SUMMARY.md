# Project Research Summary

**Project:** Navigator — Python CLI task orchestrator
**Domain:** Personal automation CLI (crontab, file watchers, subprocess execution, messaging bot)
**Researched:** 2026-03-23
**Confidence:** HIGH

## Executive Summary

Navigator is a personal task orchestration tool that wraps Claude Code as a first-class subprocess executor. Research across comparable tools (Taskfile, Just, Supervisor, n8n, Rundeck) shows the core differentiator is Navigator's deliberate integration with the real system crontab and Claude Code's `--allowedTools` / `--environment` flags — no existing tool does this. The recommended approach is a registry-driven architecture built on Python 3.12+/uv, with SQLite as the single source of truth, system crontab for scheduling, and async daemons under systemd for file watching and bot communication.

The most important architectural insight is separating concerns: cron-triggered tasks require zero daemon, file-watch and bot-triggered tasks live in separate systemd services, and the CLI is a thin layer over a thick core that all interfaces share equally. This minimizes failure surface and ensures scheduled tasks survive daemon crashes.

The primary risks are operational correctness bugs that are silent by nature: crontab corruption via concurrent writes, secret leakage through process tables, zombie subprocesses, and file watcher event storms. All of these must be addressed in Phase 1 and Phase 2 — they cannot be retrofitted safely. Security hardening of the messaging bot (auth allowlisting, no shell=True, input sanitization) must also ship from day one of that component.

## Key Findings

### Recommended Stack

Navigator's stack is well-established for the domain. Typer (built on Click) provides self-documenting, type-hint-driven CLI subcommands that Claude Code agents can introspect via `--help`. Pydantic v2 handles config and registry validation with Rust-backed performance. SQLite (via raw SQL + dataclasses) stores the registry with crash-safe atomic transactions. The key library choices are motivated by system-level requirements: `python-crontab` for real crontab integration, `watchdog` for inotify-based file watching, and `python-telegram-bot` (async, long-polling, no public endpoint) for bot communication.

See [STACK.md](./STACK.md) for full version table, alternatives considered, and what NOT to use.

**Core technologies:**
- Python 3.12+ / uv 0.10.12: Runtime and toolchain — performance improvements, stdlib `tomllib`, and the user's required toolchain
- Typer 0.24.1 + Rich 14.3.3: CLI framework and terminal output — type-hint-driven, auto-generates `--help`, machine-readable by Claude Code agents
- Pydantic 2.12.5: Data validation for registry entries, config, and bot schemas — Rust-backed V2
- SQLite (stdlib): Command registry persistence — atomic transactions, crash recovery, WAL mode for concurrent access
- python-crontab 3.3.0: Real system crontab CRUD — Navigator entries are visible to standard tools
- watchdog 6.0.0: inotify-based file system monitoring — cross-platform, handles recursive watching
- python-telegram-bot 22.7: Async long-polling bot — no webhook/public exposure needed
- hatchling 1.29.0 + ruff 0.15.7: Build backend and linter/formatter — pyproject.toml-native

### Expected Features

Navigator's MVP targets a focused set of table-stakes features, with differentiating capabilities added after validation. The feature dependency graph is clear: everything depends on the command registry, which depends on the storage layer. Crontab management and file watching both depend on systemd persistence. The messaging bot is independent of trigger types but requires the same registry and systemd foundation.

See [FEATURES.md](./FEATURES.md) for full prioritization matrix, competitor analysis, and anti-features to avoid.

**Must have (table stakes — v1 launch):**
- Command registry with CRUD — the foundation everything else references
- Claude Code subprocess orchestration — the core differentiator; `--allowedTools`, env injection, output capture
- Secret injection from `~/.secrets/<namespace>/` — per-command, principle of least privilege
- Crontab management — schedule/unschedule with tagged entries (`# navigator:<id>`)
- Logging with stdout/stderr capture — `navigator logs <command>`, per-execution files
- Retry on failure with exponential backoff — `--retries N`
- systemd service — daemon survives reboots, manages watcher and bot lifecycle
- Global install via `uv tool install` — `navigator` on PATH

**Should have (competitive — v1.x after validation):**
- File/folder watching with debounce and time-window constraints
- Command chaining with shared state and failure semantics
- Multi-project namespacing (`namespace:command`)
- Push notifications on failure via bot
- Dry-run mode for schedule/registration validation
- Pre-configured tool permissions per command

**Defer (v2+):**
- Messaging bot remote control — high complexity, validate CLI workflow first
- Cross-namespace chaining — only needed when projects actively interoperate
- Claude Code skill exposure — requires stable CLI API first
- Time-window constraints on file watchers

### Architecture Approach

Navigator uses a registry-driven, thin-interface architecture: all executable units are registered commands in SQLite; CLI, messaging bot, and skills API are thin adapters that parse input and call identical core functions; scheduling is delegated to the real system crontab (not a reimplemented loop); and only continuous triggers (file watching, bot listening) require long-lived daemons. The crontab is a derived output from the registry — never a source of truth. SQLite is the single source of truth for all state.

See [ARCHITECTURE.md](./ARCHITECTURE.md) for full component diagram, data flow diagrams, project structure, and build order.

**Major components:**
1. CLI layer (`cli/`) — Typer subcommand groups; calls into `core/` only, never touches DB directly
2. Registry (`core/registry.py`) — CRUD against SQLite; all other components resolve through here
3. Executor (`core/executor.py`) — subprocess runner with clean env construction, secrets injection, retry, timeout, process group cleanup
4. Scheduler (`core/scheduler.py`) — one-way sync from registry to system crontab; file-locked read-modify-write
5. Watcher (`core/watcher.py`) — watchdog-based inotify daemon with debounce, ignore patterns, self-trigger guard
6. Chain Engine (`core/chain.py`) — sequential runner with depth limit, cycle detection, correlation ID logging
7. Bot Service (`services/bot_service.py`) — async long-polling Telegram/Discord; user ID allowlist; calls same core functions as CLI
8. systemd units — `navigator-watcher.service` and `navigator-bot.service`; separate restart domains

### Critical Pitfalls

See [PITFALLS.md](./PITFALLS.md) for all 10 pitfalls with warning signs, recovery strategies, and the "Looks Done But Isn't" checklist.

1. **Crontab corruption via concurrent writes** — use `fcntl.flock` on a lock file around all crontab read-modify-write cycles; implement `crontab_manager` as the single code path; verify after every write
2. **Secret leakage through process tables and logs** — never pass secrets as CLI arguments; build env from scratch (not `os.environ | new_vars`); `sanitize_output()` before any logging; validate `0600` permissions on startup
3. **Zombie/orphan subprocesses** — track child PIDs in `running.json`; use process groups (`os.setpgrp()`, `os.killpg()`); register `atexit` + `SIGTERM` handlers; systemd `KillMode=control-group`
4. **File watcher event storms and self-triggering** — 500ms debounce; default-ignore editor temp files; track files being modified by active sessions; per-watcher mutex for concurrency control
5. **Messaging bot as unauthenticated remote shell** — user ID allowlist (reject silently); `shell=False` always; no raw shell execution via bot; rate-limit commands; store token in `0600` secrets file
6. **Unbounded command chains** — depth counter via `NAVIGATOR_CHAIN_DEPTH` env var (default limit: 10); cycle detection at registration time; explicit failure semantics (stop-on-failure default)
7. **State file corruption** — use SQLite (not flat JSON) for the registry from day one; atomic writes (`os.rename()`) for any config files
8. **Stale crontab paths after reinstall** — resolve absolute path at registration time; `navigator doctor` verifies all entries; `navigator repair-crontab` updates paths; redirect stderr to `~/.navigator/cron.log`

## Implications for Roadmap

Based on research, the build order from ARCHITECTURE.md maps naturally to phases. Each phase produces a usable increment and addresses specific pitfalls.

### Phase 1: Foundation + Execution Core
**Rationale:** Everything depends on the registry and executor. Pitfalls 1, 2, 3, 7, 8, 9, and 10 must be addressed here — they cannot be safely retrofitted.
**Delivers:** `navigator register`, `navigator list`, `navigator exec`, `navigator logs`; SQLite registry; secrets injection; subprocess execution with clean env, retry, process group lifecycle
**Addresses:** Command registry CRUD, Claude Code subprocess orchestration, secret injection, logging, retry on failure, global install
**Avoids:** Crontab corruption (file lock), secret leakage (clean env, sanitize_output), zombie processes (PID tracking, process groups), state file corruption (SQLite), stale paths (absolute path resolution)

### Phase 2: Scheduling
**Rationale:** Crontab integration depends on a working registry and executor (Phase 1). The crontab manager must be lock-safe from the first implementation.
**Delivers:** `navigator schedule`, `navigator unschedule`; system crontab sync; tagged entries; `navigator doctor` for path verification
**Uses:** python-crontab, fcntl locking, `MAILTO=""`, stderr redirect to cron.log
**Implements:** Scheduler component, one-way registry→crontab sync pattern

### Phase 3: File Watching + Daemon
**Rationale:** File watching requires the executor (Phase 1) and a persistent daemon. Self-trigger and debounce must ship with the initial watcher.
**Delivers:** `navigator watch`, watcher daemon, `navigator-watcher.service` systemd unit; debounce; ignore patterns; self-trigger guard
**Uses:** watchdog, systemd user service, `loginctl enable-linger`
**Avoids:** File watcher race conditions and event storms

### Phase 4: Chaining + Namespacing
**Rationale:** Chaining depends on registry and executor. Namespacing should precede the bot to avoid cross-project leakage.
**Delivers:** `navigator chain`, `navigator namespace`; depth limiting; cycle detection at registration; correlation ID logging; per-namespace secrets isolation
**Avoids:** Unbounded execution graphs, subprocess environment leakage across namespaces

### Phase 5: Notifications + Messaging Bot
**Rationale:** Bot is the highest-complexity component. CLI workflow should be validated first. Bot calls the same core functions, so correctness is established before adding the remote interface.
**Delivers:** Push notifications on failure, Telegram/Discord bot with user ID allowlist, `navigator-bot.service` systemd unit
**Uses:** python-telegram-bot, long-polling, `shell=False`, rate limiting
**Avoids:** Bot as unauthenticated remote shell, systemd boot failures

### Phase 6: Polish + Claude Code Skills API
**Rationale:** After all functional components are validated, expose structured output and introspection surfaces.
**Delivers:** `--output json` machine-readable mode, `navigator install-service`, `navigator doctor`, execution history, `navigator ps`, `navigator repair-crontab`
**Addresses:** Claude Code invokability, operational visibility, UX pitfalls (silent failures, opaque errors)

### Phase Ordering Rationale

- Phases 1-2 are strictly ordered by dependency: registry before scheduling, executor before crontab entries can call back into Navigator
- Phase 3 (file watching) can begin as soon as Phase 1 ships — it only needs the executor
- Phase 4 (chaining/namespacing) should precede Phase 5 (bot) so namespace isolation is in place before adding a remote execution surface
- Phase 5 (bot) is deliberately last among feature phases — it is the highest-risk component and benefits from a stable, tested core
- Phase 6 is polish and integration — it can be interleaved with earlier phases as time allows

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3:** inotify watch limits (`/proc/sys/fs/inotify/max_user_watches`) — check limit handling and user documentation
- **Phase 5:** python-telegram-bot v22 async handler patterns and message length limits for paginated output — API has changed significantly across major versions
- **Phase 5:** Discord.py gateway vs Telegram long-polling concurrency model if both are implemented simultaneously

Phases with standard patterns (skip research-phase):
- **Phase 1:** SQLite schema design, subprocess env injection, and retry logic are well-documented standard patterns
- **Phase 2:** python-crontab API is straightforward; crontab format is stable and well-documented
- **Phase 6:** Typer JSON output mode and systemd unit file installation are fully documented

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All library versions verified against PyPI on 2026-03-23; version compatibility confirmed |
| Features | HIGH | Surveyed 8+ comparable tools; feature landscape is well-understood for this domain |
| Architecture | HIGH | Standard patterns for CLI orchestrators; pitfall analysis validates the architectural choices |
| Pitfalls | HIGH | Pitfalls sourced from man pages, library docs, and established failure patterns |

**Overall confidence:** HIGH

### Gaps to Address

- **Timezone handling in crontab entries:** Research did not resolve whether Navigator should enforce `TZ=` in crontab entries or document the system timezone assumption. Address during Phase 2 planning.
- **SQLite vs TinyDB for MVP:** STACK.md notes TinyDB as an option for simpler initial implementation. Research consensus favors SQLite from day one due to corruption risk (Pitfall 8). Treat as resolved: use SQLite.
- **Discord as primary vs secondary bot:** If Discord is required alongside Telegram, both can share an event loop (both are async-native). Decision should be made before Phase 5 planning to avoid interface-level rework.

## Sources

### Primary (HIGH confidence)
- PyPI JSON API (pypi.org/pypi/{package}/json) — all version numbers verified 2026-03-23
- Linux `crontab(5)`, `inotify(7)`, POSIX `rename(2)` man pages — crontab format, inotify event model, atomic rename guarantees
- systemd `systemd.exec(5)` — KillMode, user services, lingering
- Python `subprocess` module documentation — shell=False, preexec_fn, env parameter
- SQLite documentation — atomic commit, crash recovery, WAL mode

### Secondary (MEDIUM confidence)
- python-telegram-bot documentation — long-polling vs webhook pattern, handler architecture
- watchdog library documentation — inotify backend, event types
- python-crontab library — CRUD API, comment marker pattern
- Click / Typer documentation — command groups, type-hint argument parsing
- Taskfile (taskfile.dev) — feature comparison
- Just (github.com/casey/just) — feature comparison
- Supervisor (supervisord.org), PM2 (pm2.keymetrics.io) — process manager patterns
- n8n (n8n.io), Huginn — self-hosted automation, anti-pattern reference
- Rundeck — job scheduler with secret management, feature reference

### Tertiary (LOW confidence)
- PAI by Daniel Miessler — complementary tool, not competitive; capabilities inferred from description
- Celery/Luigi/Airflow architectures — studied for patterns to adopt and avoid; specific details may not apply at Navigator's scale

---
*Research completed: 2026-03-23*
*Ready for roadmap: yes*
