# Navigator

## What This Is

A private, Python-based orchestrator that schedules, triggers, and chains Claude Code sessions with proper context, secrets, and permissions. Navigator manages the system's actual crontab and file watchers to run registered commands — wrapping each invocation with environment variables, secret injection, and pre-configured tool permissions. It is globally installed, never exposed to the public internet, and controlled via local CLI or a private messaging bot (Telegram/Discord).

## Core Value

Autonomous task orchestration — registered commands run on schedule or on file changes, with the right context and secrets, without human intervention unless something fails.

## Requirements

### Validated

- ✓ Globally installed via pip/uv (`navigator` CLI on PATH) — Phase 1
- ✓ Configuration file at `~/.config/navigator/config.toml` — Phase 1
- ✓ Absolute path resolution at registration time — Phase 1
- ✓ Living command registry with CRUD operations (register, list, show, update, pause, resume, delete) — Phase 2
- ✓ Registry persists in SQLite with crash-safe atomic transactions — Phase 2
- ✓ List registered commands by created date for housekeeping — Phase 2
- ✓ Secret injection — reads secrets from a path, passes them as environment variables to Claude Code subprocess — Phase 3
- ✓ Environment path (`--environment`) defines the working directory and shared state location for a command — Phase 3
- ✓ Pre-configured Claude Code permissions (`--allowedTools`) per registered command — Phase 3
- ✓ Retry with backoff (`--retries N`) on failure — Phase 4
- ✓ Cron-based scheduling via system crontab — Navigator reads and manages real crontab entries — Phase 5
- ✓ File/folder watching as a trigger pattern (inotify via watchdog), with debounce, self-trigger guard, time-window constraints, and ignore patterns — Phase 6

- ✓ Multi-project namespacing — commands namespaced by project with isolated secrets and cross-namespace references — Phase 7

- ✓ Command chaining — sequential triggers with shared state, depth limits, cycle detection, correlation IDs — Phase 8

- ✓ Survives reboots — systemd user service with auto-restart and linger support — Phase 9

### Active

- [ ] MkDocs documentation site with full project docs (installation, configuration, CLI reference, guides)
- [ ] Comprehensive README.md with installation instructions, quick start, and usage examples
- [ ] CLI reference documentation for all commands and subcommands
- [ ] Feature guides for scheduling, watching, chaining, secrets, namespaces, and systemd
- [ ] Getting started / quick start tutorial

### Future

- [ ] Push notifications on failure via messaging bot
- [ ] Remote CLI via private messaging bot (Telegram/Discord) — full CRUD, long-polling, never exposed publicly
- [ ] Globally installed via pip (`pip install navigator`, `navigator` CLI command)
- [ ] Claude Code can understand and invoke the CLI API from other sessions
- [ ] Exposes skills usable from Claude Code sessions

### Out of Scope

- Public internet exposure — interaction is only via local CLI or private messaging bot through third-party APIs
- Building the actual skills (scraping, video generation, publishing) — Navigator orchestrates, skills do the work
- GUI/web dashboard — CLI and messaging bot are the interfaces
- Multi-user support — this is a single-user private system
- Replacing PAI (Daniel Miessler's Personal AI Infrastructure) — Navigator is complementary, handling the operational/scheduling layer that PAI does not

## Context

- **User:** Runs Gamescout, a hunting social media/newsletter/consulting company for Vancouver Island, BC. Needs daily content pipelines (5 short video scripts, trend scraping), weekly long-form content (blog + 10min video), Thursday newsletters, and event-driven publishing.
- **Personal routines:** Workout, dryfire, meditation, nutrition scheduling — eventually managed through Obsidian vault agents that register tasks with Navigator.
- **Obsidian integration:** Other Claude Code sessions running from an Obsidian vault will call Navigator's CLI to register and manage recurring/one-off tasks.
- **PAI comparison:** Daniel Miessler's PAI is a contextual wrapper (identity, memory, learning around Claude Code). Navigator is an operational orchestrator (scheduling, triggering, chaining, secret management). They are complementary — PAI skills could run inside Navigator-orchestrated sessions.
- **Platform:** Currently Pop!_OS/Ubuntu personal machine, will promote to VPS later. Never allow remote access directly — only through messaging bot APIs.

## Constraints

- **Tech stack**: Python — globally installable via pip
- **Scheduling**: Must use the system's actual crontab, not a reimplementation
- **Privacy**: Never exposed to public internet. All remote interaction via third-party messaging APIs (Telegram/Discord long-polling)
- **Portability**: Must work on Pop!_OS, Ubuntu, and eventually VPS environments
- **Persistence**: Must survive reboots via systemd
- **Claude Code integration**: CLI must be understandable and invokable by Claude Code agents

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python over TypeScript | Globally installable via pip, user preference | — Pending |
| System crontab over internal scheduler | Don't reinvent scheduling, leverage battle-tested system tooling | — Pending |
| Telegram/Discord bot over web API | Privacy-first, never expose to public internet, use existing encrypted channels | — Pending |
| Navigator (name) | Dune reference — Guild Navigators fold space, routing tasks through the right paths autonomously | — Pending |
| Complement PAI, don't compete | PAI handles context/identity/memory; Navigator handles scheduling/triggering/orchestration | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
## Current Milestone: v1.1 Documentation

**Goal:** Comprehensive project documentation using MkDocs and a README.md with full installation and usage instructions.

**Target features:**
- MkDocs documentation site with full project docs
- Comprehensive README.md with installation, quick start, usage examples
- CLI reference for all commands and subcommands
- Feature guides for each major capability (scheduling, watching, chaining, secrets, namespaces, systemd)
- Getting started tutorial

---
*Last updated: 2026-03-25 after milestone v1.1 start*
