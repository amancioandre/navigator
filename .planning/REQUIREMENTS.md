# Requirements: Navigator

**Defined:** 2026-03-23
**Core Value:** Autonomous task orchestration — registered commands run on schedule or on file changes, with the right context and secrets, without human intervention unless something fails.

## v1.0 Requirements (Complete)

All 48 requirements shipped. See MILESTONES.md for details.

<details>
<summary>v1.0 requirement categories (all complete)</summary>

### Registry (REG-01 through REG-10) — Phase 1, 2, 10
### Execution (EXEC-01 through EXEC-10) — Phase 3, 4
### Scheduling (SCHED-01 through SCHED-05) — Phase 5
### File Watching (WATCH-01 through WATCH-06) — Phase 6, 9
### Chaining (CHAIN-01 through CHAIN-06) — Phase 8
### Namespacing (NS-01 through NS-04) — Phase 7
### Infrastructure (INFRA-01 through INFRA-07) — Phase 1, 9, 10

</details>

## v1.1 Requirements

Requirements for documentation milestone. Each maps to roadmap phases.

### Documentation Infrastructure

- [ ] **DINF-01**: MkDocs site scaffold with Material theme, mkdocs.yml config, and dependency group in pyproject.toml
- [ ] **DINF-02**: Auto-generated CLI reference from Typer app covering all commands and subcommands
- [ ] **DINF-03**: Strict build validation (mkdocs build --strict) integrated into dev workflow

### Getting Started

- [ ] **START-01**: Installation guide covering pip, uv, and global install methods
- [ ] **START-02**: Quick start tutorial walking through registering and executing a first command

### Feature Guides

- [ ] **GUIDE-01**: Scheduling guide — cron-based scheduling with examples
- [ ] **GUIDE-02**: File watching guide — watchdog triggers with debounce, ignore patterns, time windows
- [ ] **GUIDE-03**: Command chaining guide — sequential triggers, correlation IDs, cycle detection
- [ ] **GUIDE-04**: Secrets management guide — .env loading, environment isolation, security model
- [ ] **GUIDE-05**: Namespaces guide — multi-project organization, cross-namespace references
- [ ] **GUIDE-06**: Systemd service guide — daemon persistence, install/uninstall, reboot survival
- [ ] **GUIDE-07**: Configuration reference — config.toml options, paths, defaults

### README

- [ ] **READ-01**: Comprehensive README.md with installation, quick start, feature overview, and links to docs site

### Maintenance

- [ ] **MAINT-01**: Documentation maintenance conventions established (future milestones update docs, strict build in workflow)

## Future Requirements

### Remote Access & Notifications

- **BOT-01**: Push notifications on failure via messaging bot
- **BOT-02**: Remote CLI via private messaging bot (Telegram/Discord)
- **BOT-03**: Claude Code skill exposure for cross-session invocation

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Hosted documentation (GitHub Pages) | Navigator is a private tool; local `mkdocs serve` is sufficient |
| Auto-generated Python API docs | Navigator is a CLI tool, not a library; CLI reference is the right abstraction |
| Video tutorials | Maintenance trap for a private tool; written guides are sufficient |
| Changelog page | Git log is authoritative; a separate changelog adds drift risk |
| Versioned docs (mike) | Single-user tool with one active version; versioning adds complexity for no benefit |
| Web dashboard / GUI | Massive surface area, security exposure, violates privacy constraint |
| Internal cron reimplementation | System crontab is battle-tested |
| Multi-user / RBAC | Single-user private system |
| Plugin / extension system | Premature abstraction |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DINF-01 | Phase 11 | Pending |
| DINF-02 | Phase 12 | Pending |
| DINF-03 | Phase 11 | Pending |
| START-01 | Phase 13 | Pending |
| START-02 | Phase 13 | Pending |
| GUIDE-01 | Phase 14 | Pending |
| GUIDE-02 | Phase 14 | Pending |
| GUIDE-03 | Phase 14 | Pending |
| GUIDE-04 | Phase 14 | Pending |
| GUIDE-05 | Phase 14 | Pending |
| GUIDE-06 | Phase 14 | Pending |
| GUIDE-07 | Phase 14 | Pending |
| READ-01 | Phase 15 | Pending |
| MAINT-01 | Phase 16 | Pending |

**Coverage:**
- v1.1 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0

---
*Requirements defined: 2026-03-23*
*Last updated: 2026-03-25 after v1.1 roadmap creation*
