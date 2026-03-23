<!-- GSD:project-start source:PROJECT.md -->
## Project

**Navigator**

A private, Python-based orchestrator that schedules, triggers, and chains Claude Code sessions with proper context, secrets, and permissions. Navigator manages the system's actual crontab and file watchers to run registered commands — wrapping each invocation with environment variables, secret injection, and pre-configured tool permissions. It is globally installed, never exposed to the public internet, and controlled via local CLI or a private messaging bot (Telegram/Discord).

**Core Value:** Autonomous task orchestration — registered commands run on schedule or on file changes, with the right context and secrets, without human intervention unless something fails.

### Constraints

- **Tech stack**: Python — globally installable via pip
- **Scheduling**: Must use the system's actual crontab, not a reimplementation
- **Privacy**: Never exposed to public internet. All remote interaction via third-party messaging APIs (Telegram/Discord long-polling)
- **Portability**: Must work on Pop!_OS, Ubuntu, and eventually VPS environments
- **Persistence**: Must survive reboots via systemd
- **Claude Code integration**: CLI must be understandable and invokable by Claude Code agents
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Python | >=3.12 | Runtime | 3.12+ has significant performance improvements (specializing adaptive interpreter), better error messages, and `tomllib` in stdlib. 3.12 is the floor for new projects in 2025/2026. | HIGH |
| uv | 0.10.12 | Package/project management | Replaces pip, pip-tools, virtualenv, and hatch CLI in one tool. 10-100x faster than pip. Handles lockfiles, Python version management, and `uv tool install` for global CLI apps. The user's preferred toolchain. | HIGH |
| Typer | 0.24.1 | CLI framework | Built on Click, adds type-hint-driven argument parsing. Auto-generates `--help`, shell completion, and subcommand groups. Claude Code agents can read `--help` output to self-discover the API. Rich integration built in. | HIGH |
| Pydantic | 2.12.5 | Data validation / config | Validates command registry entries, config files, bot message schemas. V2 is Rust-backed (pydantic-core), dramatically faster than V1. Standard for any structured data in Python. | HIGH |
| watchdog | 6.0.0 | File system monitoring | Cross-platform file watcher using inotify on Linux. Mature, well-maintained, handles recursive watching. The standard choice -- no real competitor in Python. | HIGH |
| python-crontab | 3.3.0 | Crontab management | Reads/writes the system crontab programmatically. Handles cron expression parsing, validation, and entry CRUD. The project explicitly requires system crontab management, not an internal scheduler. | HIGH |
| python-telegram-bot | 22.7 | Telegram bot interface | Async-native (v20+), supports long-polling (no webhook/public exposure needed). Handles commands, conversations, inline keyboards. Most mature Python Telegram library. | HIGH |
| Rich | 14.3.3 | Terminal output | Beautiful tables, progress bars, syntax highlighting, logging. Typer uses it internally. Makes CLI output readable for both humans and Claude Code agents parsing structured output. | HIGH |
### Supporting Libraries
| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| TinyDB | 4.8.2 | Command registry storage | JSON-based document store for the command registry. No server process, file-based, queryable. Perfect for single-user CLI tools that need persistent structured data without SQLite overhead. | HIGH |
| discord.py | 2.7.1 | Discord bot interface | If Discord is chosen over/alongside Telegram. Async-native, supports slash commands, long-polling via gateway. | MEDIUM |
| tomli-w | ~1.1 | TOML writing | For writing config files. Python 3.12+ has `tomllib` for reading but no writer in stdlib. Only needed if config is TOML-based. | MEDIUM |
| platformdirs | ~4.3 | XDG-compliant paths | Resolves `~/.config/navigator/`, `~/.local/share/navigator/` etc. correctly across Linux distros. Avoids hardcoding paths. | HIGH |
| python-dotenv | ~1.1 | Secret loading from .env | Reads `.env` files for secret injection into subprocesses. Lightweight, well-known pattern. Only if secrets are stored as `.env` files rather than a custom format. | MEDIUM |
### Development Tools
| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| uv | 0.10.12 | Project management, virtualenv, locking | Use `uv init`, `uv sync`, `uv run`, `uv tool install`. Replaces pip, virtualenv, hatch CLI. |
| hatchling | 1.29.0 | Build backend | Declared in `pyproject.toml` `[build-system]`. uv uses it to build the package. Supports dynamic versioning, entry points. |
| ruff | 0.15.7 | Linter + formatter | Replaces flake8, isort, black in one tool. Rust-based, sub-second on large codebases. Configure in `pyproject.toml`. |
| pytest | 9.0.2 | Testing | Standard test runner. Use with `uv run pytest`. |
| pytest-asyncio | 1.1.0 | Async test support | Required for testing the Telegram/Discord bot handlers and any async file watcher code. |
| mypy | latest | Static type checking | Optional but recommended. Pydantic + Typer are fully typed, so mypy catches real bugs. |
## Installation
# Initialize project
# Core dependencies (added to pyproject.toml)
# Optional: Discord support
# Dev dependencies
# Install globally as CLI tool (after building)
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Typer | Click | If you need lower-level control over argument parsing or Typer's magic feels too implicit. Typer is built on Click, so you can drop down when needed. |
| Typer | argparse | Never for this project. argparse requires verbose boilerplate, no auto-completion, poor discoverability. |
| TinyDB | SQLite (via sqlite3) | If you need relational queries, joins, or the registry grows beyond ~10K entries. SQLite is in stdlib and zero-config. For a personal orchestrator with <500 commands, TinyDB is simpler. |
| TinyDB | SQLModel | If you want ORM-style access with Pydantic models over SQLite. Heavier dependency but good DX. Only if queries get complex. |
| python-crontab | crontab subprocess calls | If python-crontab has a bug or limitation. You can always shell out to `crontab -l` and `crontab -e` directly. python-crontab is a thin wrapper anyway. |
| watchdog | inotify-simple | If you want lower-level inotify access on Linux only. Loses cross-platform support. watchdog abstracts this correctly. |
| python-telegram-bot | aiogram | If you prefer a more "framework-like" approach with middleware/routers. aiogram 3.x is solid but smaller community. python-telegram-bot has better docs and wider adoption. |
| hatchling | setuptools | If you have legacy requirements. hatchling is cleaner for new projects with `pyproject.toml`-only config. |
| platformdirs | hardcoded ~/.config | Never. Hardcoded paths break on non-standard setups and are a maintenance burden. |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| APScheduler | The project explicitly requires system crontab management. APScheduler is an in-process scheduler that dies with the process and doesn't survive reboots without its own persistence layer. It reimplements what cron already does. | python-crontab + systemd for the watcher daemon |
| Celery | Massive overkill for a single-user CLI tool. Requires a message broker (Redis/RabbitMQ), worker processes, and complex configuration. Designed for distributed task queues, not personal orchestration. | Direct subprocess execution with `subprocess.run()` / `asyncio.create_subprocess_exec()` |
| schedule (the library) | In-process scheduler, same problem as APScheduler. Dies when process dies. No crontab integration. | python-crontab for scheduling, systemd for persistence |
| Flask/FastAPI | No web server needed. The project is CLI + messaging bot, never exposed to public internet. Adding an HTTP API adds attack surface for zero benefit. | Typer CLI + Telegram/Discord bot |
| Poetry | uv has superseded Poetry for new projects. Faster resolution, better lockfile format, handles Python version management, and the user explicitly requires uv. | uv with hatchling backend |
| pip (directly) | uv replaces pip with 10-100x better performance, proper lockfiles, and reproducible installs. | uv |
| Black + isort + flake8 | Three separate tools with overlapping config. Ruff replaces all three in a single Rust-based binary that runs in milliseconds. | ruff |
| Pydantic V1 | V2 is a ground-up rewrite with Rust core. V1 is in maintenance mode. No reason to start a new project on V1. | Pydantic >=2.12 |
| Click (directly) | Typer provides the same functionality with less boilerplate via type hints. Since Typer is built on Click, you get Click's power without the verbosity. | Typer |
## Stack Patterns by Variant
- Switch to SQLite via `sqlite3` stdlib module or SQLModel
- TinyDB data can be migrated with a simple script since it's JSON
- Because TinyDB has no indexing or query optimizer; SQLite handles complex queries natively
- Run both bots as async tasks in the same daemon process
- Use a shared command dispatcher that both bots call into
- Because both libraries are async-native and can share an event loop
- Add `keyring` library for OS keychain integration (GNOME Keyring on Pop!_OS)
- Or use `age`/`sops` for encrypted files decrypted at runtime
- Because `.env` files are plaintext -- acceptable for single-user local machine, but encrypt if moving to VPS
- Secrets must be encrypted (see above)
- systemd unit files travel with the project
- Telegram/Discord long-polling works identically on VPS (no port exposure needed)
- Because the architecture deliberately avoids inbound connections
## Version Compatibility
| Package | Compatible With | Notes |
|---------|-----------------|-------|
| Typer 0.24.x | Python >=3.7 | Typer supports wide Python range but we target 3.12+ for performance |
| Pydantic 2.12.x | Python >=3.8 | Pydantic V2 requires pydantic-core Rust extension; pre-built wheels for all platforms |
| python-telegram-bot 22.x | Python >=3.9 | V20+ is async-only; no sync fallback. This is correct for our architecture. |
| watchdog 6.x | Python >=3.9 | Uses inotify on Linux, FSEvents on macOS, ReadDirectoryChangesW on Windows |
| hatchling 1.29.x | Python >=3.10 | Build backend only; does not constrain runtime Python version |
| TinyDB 4.8.x | Python >=3.8 | Pure Python, no native dependencies |
| discord.py 2.7.x | Python >=3.9 | Async-only, uses aiohttp internally |
## Architecture Notes
### Why These Choices Fit Navigator Specifically
## Sources
- PyPI JSON API (pypi.org/pypi/{package}/json) -- verified all version numbers on 2026-03-23
- PROJECT.md -- project requirements and constraints
- Training data knowledge for library capabilities and architecture patterns (confidence: HIGH for established libraries, MEDIUM for version-specific features)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
