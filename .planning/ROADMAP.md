# Roadmap: Navigator

## Milestones

- v1.0 Navigator Core (shipped 2026-03-25)
- v1.1 Documentation (in progress)

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

### v1.1 Documentation

- [x] **Phase 11: Docs Foundation** - MkDocs scaffold with Material theme, dependency group, and strict build validation (completed 2026-03-25)
- [ ] **Phase 12: CLI Reference** - Auto-generated CLI reference covering all commands and subcommands
- [ ] **Phase 13: Getting Started** - Installation guide and quick start tutorial
- [ ] **Phase 14: Feature Guides** - Seven task-oriented guides for each major Navigator capability
- [ ] **Phase 15: README** - Comprehensive README.md with install, quick start, and links to docs site
- [ ] **Phase 16: Docs Maintenance** - Strict build enforcement and maintenance conventions for future milestones

## Phase Details

### Phase 11: Docs Foundation
**Goal**: MkDocs project builds cleanly and the auto-generation plugin is validated against Navigator's CLI
**Depends on**: Phase 10 (v1.0 complete)
**Requirements**: DINF-01, DINF-03
**Success Criteria** (what must be TRUE):
  1. Running `uv sync --group docs` installs MkDocs, Material theme, and CLI auto-generation plugin without affecting runtime dependencies
  2. Running `mkdocs build --strict` produces a site with zero warnings from the project root
  3. Running `mkdocs serve` launches a local dev server showing the Material-themed docs skeleton
  4. The `site/` directory is gitignored and `mkdocs.yml` lives at the project root
**Plans**: 1 plan
Plans:
- [ ] 11-01-PLAN.md — MkDocs scaffold with Material theme, mkdocs-click plugin, and strict build validation

### Phase 12: CLI Reference
**Goal**: Every Navigator command and subcommand is documented automatically from the live Typer app
**Depends on**: Phase 11
**Requirements**: DINF-02
**Success Criteria** (what must be TRUE):
  1. A CLI reference page exists at `docs/reference/cli.md` that renders all Navigator commands and subcommands
  2. The reference is auto-generated from the Typer app object at build time (not hand-written)
  3. Every `--help` string in `cli.py` is reviewed and provides clear descriptions (no empty or placeholder help text)
**Plans**: 1 plan
Plans:
- [ ] 12-01-PLAN.md — Enhance CLI help strings and verify auto-generated reference

### Phase 13: Getting Started
**Goal**: A new user can go from zero to a running scheduled command by following the docs
**Depends on**: Phase 12
**Requirements**: START-01, START-02
**Success Criteria** (what must be TRUE):
  1. An installation guide covers pip install, uv install, and global install methods with prerequisites
  2. The installation guide includes a verification step using `navigator doctor`
  3. A quick start tutorial walks through registering a command, executing it, and verifying output end-to-end
  4. The tutorial is self-contained and completable without reading any other page
**Plans**: TBD

### Phase 14: Feature Guides
**Goal**: Each major Navigator capability has a task-oriented guide with real examples
**Depends on**: Phase 13
**Requirements**: GUIDE-01, GUIDE-02, GUIDE-03, GUIDE-04, GUIDE-05, GUIDE-06, GUIDE-07
**Success Criteria** (what must be TRUE):
  1. A scheduling guide covers cron expressions with working examples for common patterns (daily, hourly, weekday-only)
  2. A file watching guide covers watchdog triggers including debounce tuning, ignore patterns, and time-window constraints
  3. A chaining guide covers sequential triggers with correlation ID tracing and cycle detection behavior
  4. A secrets guide covers .env loading, environment isolation, and the security model for secret injection
  5. A namespaces guide covers multi-project organization with cross-namespace command references
  6. A systemd guide covers daemon persistence including install, uninstall, and reboot survival verification
  7. A configuration reference documents every config.toml option with types, defaults, and examples
**Plans**: TBD

### Phase 15: README
**Goal**: The project README serves as a concise entry point that links to the docs site for depth
**Depends on**: Phase 14
**Requirements**: READ-01
**Success Criteria** (what must be TRUE):
  1. README.md exists at the project root with installation instructions matching the docs site installation guide
  2. README includes a quick start section with 4-5 commands showing the core workflow
  3. README includes a feature overview listing all major capabilities with one-line descriptions
  4. README is under 150 lines and links to the docs site for CLI reference and detailed guides
**Plans**: TBD

### Phase 16: Docs Maintenance
**Goal**: Documentation stays current as Navigator evolves beyond this milestone
**Depends on**: Phase 15
**Requirements**: MAINT-01
**Success Criteria** (what must be TRUE):
  1. `mkdocs build --strict` passes with zero warnings across the complete docs site
  2. All docs pages are reachable from the navigation (no orphaned pages)
  3. A documented convention exists for updating docs when CLI commands change in future milestones
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 11 -> 12 -> 13 -> 14 -> 15 -> 16

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 11. Docs Foundation | 0/1 | Complete    | 2026-03-25 |
| 12. CLI Reference | 0/1 | Not started | - |
| 13. Getting Started | 0/0 | Not started | - |
| 14. Feature Guides | 0/0 | Not started | - |
| 15. README | 0/0 | Not started | - |
| 16. Docs Maintenance | 0/0 | Not started | - |
