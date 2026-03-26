# Phase 1: Project Scaffold - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver an installable Python package (`navigator`) with a CLI entry point, subcommand stubs, and a config file system. After this phase, `pip install .` (or `uv tool install .`) produces a working `navigator` command on PATH that responds to `--help` and creates a config file on first run.

</domain>

<decisions>
## Implementation Decisions

### Package Structure
- **D-01:** Use src layout (`src/navigator/`) — modern Python best practice, avoids import ambiguity during development vs installed usage.
- **D-02:** Entry point via `pyproject.toml` `[project.scripts]`: `navigator = "navigator.cli:app"`

### CLI Command Hierarchy
- **D-03:** Flat subcommands — `navigator register`, `navigator list`, `navigator exec`, `navigator schedule`, `navigator watch`, `navigator chain`, `navigator logs`, `navigator doctor`. No nested command groups.
- **D-04:** Typer as the CLI framework — type-hint driven, auto-generates `--help`, discoverable by Claude Code agents.

### Config File
- **D-05:** TOML format at `~/.config/navigator/config.toml` — Python 3.12+ has stdlib `tomllib` for reading. Use `tomli-w` for writing.
- **D-06:** Config created on first run with sensible defaults (db path, log directory, secrets base path, default retry count, default timeout).

### Project Tooling
- **D-07:** uv for project management and virtual environments.
- **D-08:** pytest for testing.
- **D-09:** ruff for linting and formatting (replaces black/isort/flake8).
- **D-10:** hatchling as build backend.

### Path Resolution
- **D-11:** All internal path references resolved to absolute paths at registration time (INFRA-07). Use `pathlib.Path.resolve()`.

### Claude's Discretion
- SQLite database location default (e.g., `~/.local/share/navigator/registry.db` or `~/.config/navigator/registry.db`)
- Log directory default
- Whether to include a `navigator version` subcommand in the initial scaffold

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Research
- `.planning/research/STACK.md` — Recommended stack with versions (uv, Typer, Pydantic, ruff, hatchling)
- `.planning/research/ARCHITECTURE.md` — Component boundaries and project structure
- `.planning/research/PITFALLS.md` — Pitfall #8 (stale crontab paths) and #9 (state file corruption) apply to path resolution and config decisions

### Requirements
- `.planning/REQUIREMENTS.md` — INFRA-01 (global install), INFRA-05 (config file), INFRA-07 (absolute path resolution)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project

### Established Patterns
- None — this phase establishes the patterns

### Integration Points
- `pyproject.toml` — entry point, dependencies, build system
- `src/navigator/cli.py` — Typer app instance, subcommand registration
- `src/navigator/config.py` — config loading/creation logic

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. Follow the stack recommendations from research.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-project-scaffold*
*Context gathered: 2026-03-23*
