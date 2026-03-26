# Roadmap: Navigator

## Milestones

- ✅ **v1.0 Navigator Core** — Phases 1-10 (shipped 2026-03-25)
- ✅ **v1.1 Documentation** — Phases 11-16 (shipped 2026-03-26)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

<details>
<summary>v1.0 Navigator Core (Phases 1-10) - SHIPPED 2026-03-25</summary>

- [x] **Phase 1: Project Scaffold** - Installable Python package with CLI entry point and configuration
- [x] **Phase 2: Command Registry** - Full CRUD for registered commands backed by SQLite
- [x] **Phase 3: Execution Core** - Run registered commands as Claude Code subprocesses with secrets and clean environments
- [x] **Phase 4: Execution Hardening** - Retry, timeouts, logging, and process lifecycle management
- [x] **Phase 5: Cron Scheduling** - Schedule commands via real system crontab with lock-safe writes
- [x] **Phase 6: File Watching** - Trigger commands on filesystem changes with debounce and guards
- [x] **Phase 7: Namespacing** - Multi-project command isolation with per-namespace secrets
- [x] **Phase 8: Command Chaining** - Sequential command triggers with depth limits and cycle detection
- [x] **Phase 9: Daemon and systemd** - Persistent watcher daemon and systemd service installation
- [x] **Phase 10: Operational Polish** - Health checks, JSON output, and dry-run for Claude Code agents

</details>

<details>
<summary>v1.1 Documentation (Phases 11-16) - SHIPPED 2026-03-26</summary>

- [x] **Phase 11: Docs Foundation** - MkDocs scaffold with Material theme, dependency group, and strict build validation (completed 2026-03-25)
- [x] **Phase 12: CLI Reference** - Auto-generated CLI reference covering all commands and subcommands (completed 2026-03-25)
- [x] **Phase 13: Getting Started** - Installation guide and quick start tutorial (completed 2026-03-25)
- [x] **Phase 14: Feature Guides** - Seven task-oriented guides for each major Navigator capability (completed 2026-03-26)
- [x] **Phase 15: README** - Comprehensive README.md with install, quick start, and links to docs site (completed 2026-03-26)
- [x] **Phase 16: Docs Maintenance** - Strict build enforcement and maintenance conventions for future milestones (completed 2026-03-26)

</details>
