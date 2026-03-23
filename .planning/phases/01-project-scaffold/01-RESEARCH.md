# Phase 1: Project Scaffold - Research

**Researched:** 2026-03-23
**Domain:** Python packaging, CLI framework (Typer), TOML config, src-layout project structure
**Confidence:** HIGH

## Summary

Phase 1 delivers an installable Python package with a working CLI entry point, subcommand stubs, and a config file system. The technical surface is well-understood: `pyproject.toml` with hatchling build backend, src layout (`src/navigator/`), Typer for CLI, `tomllib`/`tomli-w` for config, and `platformdirs` for XDG-compliant paths. All libraries are stable, well-documented, and verified on PyPI as of today.

The critical configuration detail is hatchling's `packages` directive for src layout -- without `packages = ["src/navigator"]` in `[tool.hatch.build.targets.wheel]`, the package either fails to build or installs as `src.navigator` instead of `navigator`. The other common pitfall is the entry point import path: since we use src layout, the entry point in `[project.scripts]` must reference `navigator.cli:app` (not `src.navigator.cli:app`), because hatchling collapses the src prefix at build time.

**Primary recommendation:** Follow the locked decisions exactly. Use `uv init` to bootstrap, configure hatchling with explicit `packages = ["src/navigator"]`, wire up Typer with `no_args_is_help=True`, and implement first-run config creation via `platformdirs` + `tomli-w`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Use src layout (`src/navigator/`) -- modern Python best practice, avoids import ambiguity during development vs installed usage.
- **D-02:** Entry point via `pyproject.toml` `[project.scripts]`: `navigator = "navigator.cli:app"`
- **D-03:** Flat subcommands -- `navigator register`, `navigator list`, `navigator exec`, `navigator schedule`, `navigator watch`, `navigator chain`, `navigator logs`, `navigator doctor`. No nested command groups.
- **D-04:** Typer as the CLI framework -- type-hint driven, auto-generates `--help`, discoverable by Claude Code agents.
- **D-05:** TOML format at `~/.config/navigator/config.toml` -- Python 3.12+ has stdlib `tomllib` for reading. Use `tomli-w` for writing.
- **D-06:** Config created on first run with sensible defaults (db path, log directory, secrets base path, default retry count, default timeout).
- **D-07:** uv for project management and virtual environments.
- **D-08:** pytest for testing.
- **D-09:** ruff for linting and formatting (replaces black/isort/flake8).
- **D-10:** hatchling as build backend.
- **D-11:** All internal path references resolved to absolute paths at registration time (INFRA-07). Use `pathlib.Path.resolve()`.

### Claude's Discretion
- SQLite database location default (e.g., `~/.local/share/navigator/registry.db` or `~/.config/navigator/registry.db`)
- Log directory default
- Whether to include a `navigator version` subcommand in the initial scaffold

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-01 | Navigator installs globally via pip/uv (`navigator` CLI on PATH) | pyproject.toml `[project.scripts]` entry point + `uv tool install .` verified. hatchling src-layout config documented. |
| INFRA-05 | Configuration file at `~/.config/navigator/config.toml` | `platformdirs.user_config_dir("navigator")` for XDG path, `tomllib` (stdlib) for reading, `tomli-w` for writing. First-run creation pattern documented. |
| INFRA-07 | Absolute path resolution at registration time (prevents stale crontab refs after reinstall) | `pathlib.Path.resolve()` for all path fields. Config defaults must store resolved absolute paths. Pattern documented in code examples. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | >=3.12 | Runtime | stdlib `tomllib`, performance improvements, required floor |
| Typer | 0.24.1 | CLI framework | Type-hint driven, auto `--help`, Rich integration built in |
| tomli-w | 1.2.0 | TOML writing | stdlib `tomllib` reads only; `tomli-w` is the standard writer |
| platformdirs | 4.9.4 | XDG path resolution | Resolves `~/.config/`, `~/.local/share/` correctly per platform |
| Rich | 14.3.3 | Terminal output | Tables, colors, logging. Typer uses it internally |
| Pydantic | 2.12.5 | Config/data validation | Validates config schema, provides defaults, serialization |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| hatchling | 1.29.0 | Build backend | Declared in `[build-system]`, used by `uv build` |

### Dev Dependencies
| Library | Version | Purpose |
|---------|---------|---------|
| pytest | 9.0.2 | Test runner |
| ruff | 0.15.7 | Linter + formatter |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Typer | Click | More verbose, no type-hint magic. Typer is built on Click so you can drop down if needed. |
| platformdirs | Hardcoded `~/.config` | Breaks on non-standard XDG setups. Never do this. |
| Pydantic | dataclasses | No validation, no serialization helpers. Pydantic is worth the dependency. |
| tomli-w | tomlkit | tomlkit preserves comments but is heavier. tomli-w is minimal and correct for write-only. |

**Installation:**
```bash
uv init navigator
cd navigator
uv add typer platformdirs pydantic tomli-w rich
uv add --dev pytest ruff
```

**Version verification:** All versions confirmed against PyPI on 2026-03-23.

## Architecture Patterns

### Recommended Project Structure
```
navigator/
├── pyproject.toml
├── src/
│   └── navigator/
│       ├── __init__.py          # __version__, package metadata
│       ├── __main__.py          # python -m navigator support
│       ├── cli.py               # Typer app, subcommand stubs
│       └── config.py            # Config loading/creation/defaults
└── tests/
    ├── __init__.py
    ├── conftest.py              # Shared fixtures
    ├── test_cli.py              # CLI invocation tests
    └── test_config.py           # Config creation/loading tests
```

### Pattern 1: Typer App with Flat Subcommands
**What:** Single `typer.Typer()` instance with `@app.command()` decorators for each subcommand. No nested command groups.
**When to use:** When all commands are top-level and the CLI is flat (as decided in D-03).
**Example:**
```python
# src/navigator/cli.py
import typer

app = typer.Typer(
    name="navigator",
    help="Autonomous task orchestrator for Claude Code sessions.",
    no_args_is_help=True,
)

@app.command()
def register():
    """Register a new command."""
    typer.echo("register: not yet implemented")

@app.command(name="list")
def list_commands():
    """List all registered commands."""
    typer.echo("list: not yet implemented")

@app.command()
def exec():
    """Execute a registered command."""
    typer.echo("exec: not yet implemented")

@app.command()
def schedule():
    """Schedule a command with a cron expression."""
    typer.echo("schedule: not yet implemented")

@app.command()
def watch():
    """Register a file watcher for a command."""
    typer.echo("watch: not yet implemented")

@app.command()
def chain():
    """Chain commands together."""
    typer.echo("chain: not yet implemented")

@app.command()
def logs():
    """View execution logs."""
    typer.echo("logs: not yet implemented")

@app.command()
def doctor():
    """Verify system health."""
    typer.echo("doctor: not yet implemented")
```
**Source:** [Typer Commands docs](https://typer.tiangolo.com/tutorial/commands/)

### Pattern 2: First-Run Config Creation
**What:** On any CLI invocation, check if config exists. If not, create it with defaults. Use Pydantic for schema validation.
**When to use:** Always -- the config must exist before any operation.
**Example:**
```python
# src/navigator/config.py
from __future__ import annotations

import tomllib
from pathlib import Path

import platformdirs
import tomli_w
from pydantic import BaseModel, Field


def get_config_dir() -> Path:
    """Return the XDG-compliant config directory."""
    return Path(platformdirs.user_config_dir("navigator"))


def get_data_dir() -> Path:
    """Return the XDG-compliant data directory."""
    return Path(platformdirs.user_data_dir("navigator"))


class NavigatorConfig(BaseModel):
    """Navigator configuration with sensible defaults."""

    db_path: Path = Field(default_factory=lambda: get_data_dir() / "registry.db")
    log_dir: Path = Field(default_factory=lambda: get_data_dir() / "logs")
    secrets_base_path: Path = Field(
        default_factory=lambda: Path.home() / ".secrets" / "navigator"
    )
    default_retry_count: int = 3
    default_timeout: int = 300  # seconds

    def resolve_paths(self) -> None:
        """Resolve all path fields to absolute paths (INFRA-07)."""
        self.db_path = self.db_path.resolve()
        self.log_dir = self.log_dir.resolve()
        self.secrets_base_path = self.secrets_base_path.resolve()


def get_config_path() -> Path:
    """Return the path to the config file."""
    return get_config_dir() / "config.toml"


def load_config() -> NavigatorConfig:
    """Load config from file, creating with defaults on first run."""
    config_path = get_config_path()

    if config_path.exists():
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        config = NavigatorConfig(**data)
    else:
        config = NavigatorConfig()
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        # Write defaults
        dump = config.model_dump(mode="json")
        # Convert Path objects to strings for TOML serialization
        for key, value in dump.items():
            if isinstance(value, Path):
                dump[key] = str(value)
        with open(config_path, "wb") as f:
            tomli_w.dump(dump, f)

    config.resolve_paths()
    return config
```

### Pattern 3: Version from Package Metadata
**What:** Use `importlib.metadata.version()` to read the version from the installed package, avoiding duplication.
**When to use:** Always. Single source of truth for version in `pyproject.toml`.
**Example:**
```python
# src/navigator/__init__.py
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("navigator")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"
```

### Anti-Patterns to Avoid
- **Hardcoded config paths:** Never use `~/.config/navigator/` directly. Use `platformdirs` so XDG overrides work.
- **Config in `__init__.py`:** Config loading should be in its own module, not at import time. Import-time side effects break testing.
- **`shell=True` anywhere:** Even in stubs. Set the pattern early -- always use list arguments with `subprocess`.
- **Relative paths in config defaults:** All default paths must be absolute. Use `.resolve()` everywhere.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| XDG path resolution | Custom `~/.config` detection | `platformdirs` | Handles `XDG_CONFIG_HOME`, `XDG_DATA_HOME` overrides, platform differences |
| CLI argument parsing | argparse boilerplate | Typer | Auto-generates help, completion, type validation from hints |
| TOML serialization | String formatting | `tomli-w` | Handles quoting, escaping, table formatting correctly |
| Config validation | Manual type checking | Pydantic `BaseModel` | Type coercion, defaults, error messages, serialization |
| Version string | Hardcoded in multiple places | `importlib.metadata.version()` | Single source of truth from `pyproject.toml` |

**Key insight:** Phase 1 sets the foundation patterns. Using the right libraries now prevents custom rewrites later. Every hand-rolled utility in the scaffold becomes a maintenance burden across all 10 phases.

## Common Pitfalls

### Pitfall 1: hatchling src-layout Misconfiguration
**What goes wrong:** Package installs as `src.navigator` or fails to find modules entirely.
**Why it happens:** hatchling needs explicit `packages = ["src/navigator"]` in `[tool.hatch.build.targets.wheel]` for src layout. Without it, auto-discovery may fail or include the wrong paths.
**How to avoid:** Always set `packages` explicitly:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/navigator"]
```
**Warning signs:** `ModuleNotFoundError: No module named 'navigator'` after `pip install .`

### Pitfall 2: Entry Point Import Path Mismatch
**What goes wrong:** `navigator` command fails with `ImportError` after installation.
**Why it happens:** The entry point must reference the *installed* module path (`navigator.cli:app`), not the source path (`src.navigator.cli:app`). hatchling collapses the `src/` prefix during build.
**How to avoid:** Entry point is `navigator = "navigator.cli:app"` -- no `src.` prefix.
**Warning signs:** The command installs but crashes immediately on invocation.

### Pitfall 3: Config File Created with Relative Paths
**What goes wrong:** Paths like `./logs` or `~/logs` are stored in config but resolve differently depending on the working directory where `navigator` is invoked.
**Why it happens:** Default paths use `~` or relative notation. If `resolve()` is not called before writing, the config stores unexpanded paths.
**How to avoid:** Call `Path.resolve()` on all path values before writing to config and before using them. Store only absolute paths in config.toml.
**Warning signs:** Commands fail when invoked from different working directories.

### Pitfall 4: Typer `list` Command Name Collision
**What goes wrong:** Naming a function `list` shadows Python's built-in `list()`.
**Why it happens:** `navigator list` is a natural subcommand name, but `def list():` in Python shadows the builtin.
**How to avoid:** Name the function `list_commands` and use `@app.command(name="list")` to set the CLI name explicitly.
**Warning signs:** Mysterious `TypeError` if anything in the module tries to use `list()` as a builtin.

### Pitfall 5: Missing `__main__.py` for `python -m navigator`
**What goes wrong:** `python -m navigator` fails even though `navigator` CLI works.
**Why it happens:** The `[project.scripts]` entry point creates a console script, but `python -m` requires `__main__.py` in the package.
**How to avoid:** Add `src/navigator/__main__.py` with `from navigator.cli import app; app()`.
**Warning signs:** Users (or CI) trying to run via `python -m navigator` get `No module named navigator.__main__`.

## Code Examples

### pyproject.toml (Complete)
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "navigator"
version = "0.1.0"
description = "Autonomous task orchestrator for Claude Code sessions"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.24.0",
    "platformdirs>=4.0",
    "pydantic>=2.12",
    "tomli-w>=1.0",
    "rich>=14.0",
]

[project.scripts]
navigator = "navigator.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["src/navigator"]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[dependency-groups]
dev = [
    "pytest>=9.0",
    "ruff>=0.15",
]
```
**Source:** [Python Packaging Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/), [Hatch build config](https://hatch.pypa.io/latest/config/build/#packages)

### CLI Entry Point with Version Callback
```python
# src/navigator/cli.py
from typing import Annotated

import typer

from navigator import __version__

app = typer.Typer(
    name="navigator",
    help="Autonomous task orchestrator for Claude Code sessions.",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"navigator {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """Autonomous task orchestrator for Claude Code sessions."""
    pass
```
**Source:** [Typer version option docs](https://typer.tiangolo.com/tutorial/options/version/)

### Absolute Path Resolution (INFRA-07)
```python
from pathlib import Path


def resolve_path(path: str | Path) -> Path:
    """Resolve any path to an absolute path.

    Expands ~ and resolves relative paths against cwd.
    This is used at registration time to prevent stale references.
    """
    return Path(path).expanduser().resolve()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `setup.py` + setuptools | `pyproject.toml` + hatchling | 2022-2023 | No `setup.py` needed. All config in one file. |
| `pip install -e .` | `uv pip install -e .` or `uv sync` | 2024 | 10-100x faster installs |
| `black` + `isort` + `flake8` | `ruff` | 2023-2024 | Single tool, sub-second, configured in pyproject.toml |
| `click` for CLI | `typer` (built on click) | 2020+ | Less boilerplate, type-hint driven |
| Manual `~/.config` paths | `platformdirs` | Long-standing | XDG-compliant, cross-platform |
| `configparser` / JSON config | TOML (stdlib `tomllib` in 3.11+) | Python 3.11 | No external dependency for reading |

**Deprecated/outdated:**
- `setup.py` / `setup.cfg`: Replaced by `pyproject.toml`. Do not create these files.
- `requirements.txt` for project deps: Use `pyproject.toml` `[project.dependencies]`. `uv lock` generates the lockfile.

## Discretion Recommendations

For the areas left to Claude's discretion:

### SQLite Database Location
**Recommendation:** `~/.local/share/navigator/registry.db` (via `platformdirs.user_data_dir("navigator")`).
**Rationale:** XDG convention puts mutable data in `~/.local/share/`, config in `~/.config/`. The DB is data, not config. This separation means config can be version-controlled or copied without carrying the database.

### Log Directory
**Recommendation:** `~/.local/share/navigator/logs/` (via `platformdirs.user_data_dir("navigator") / "logs"`).
**Rationale:** Same XDG reasoning. Logs are data artifacts, not configuration. Keeping them alongside the DB simplifies cleanup and backup.

### Version Subcommand
**Recommendation:** Yes, include `--version` flag on the main app callback (not as a separate subcommand).
**Rationale:** `navigator --version` is the standard UX pattern. A `navigator version` subcommand is unusual and adds noise to the help output. The `@app.callback()` approach with `is_eager=True` handles this cleanly.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12+ | Runtime | Yes | 3.12.3 | -- |
| uv | Package management (D-07) | Yes | 0.10.4 | -- |
| ruff | Linting (D-09) | No (not globally) | -- | Installed as dev dep via `uv add --dev ruff` |
| pytest | Testing (D-08) | No (not globally) | -- | Installed as dev dep via `uv add --dev pytest` |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** ruff and pytest will be installed as dev dependencies within the project virtualenv. No global install needed.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` -- see Wave 0 |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01 | `pip install .` produces `navigator` on PATH, `navigator --help` succeeds | integration | `uv run pytest tests/test_cli.py::test_help_output -x` | Wave 0 |
| INFRA-05 | Config file created at `~/.config/navigator/config.toml` on first run with defaults | unit | `uv run pytest tests/test_config.py::test_first_run_creates_config -x` | Wave 0 |
| INFRA-05 | Config file loaded correctly on subsequent runs | unit | `uv run pytest tests/test_config.py::test_load_existing_config -x` | Wave 0 |
| INFRA-07 | All path fields in config are resolved to absolute paths | unit | `uv run pytest tests/test_config.py::test_paths_are_absolute -x` | Wave 0 |
| INFRA-07 | `resolve_path()` handles `~`, relative, and absolute input | unit | `uv run pytest tests/test_config.py::test_resolve_path -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/__init__.py` -- package marker
- [ ] `tests/conftest.py` -- shared fixtures (tmp config dir, monkeypatched platformdirs)
- [ ] `tests/test_cli.py` -- CLI invocation tests (covers INFRA-01)
- [ ] `tests/test_config.py` -- config creation/loading tests (covers INFRA-05, INFRA-07)
- [ ] pytest config in `pyproject.toml` -- `testpaths` and `pythonpath` settings
- [ ] Framework install: `uv add --dev pytest` -- not yet in project

## Open Questions

1. **Typer `app()` callable as entry point**
   - What we know: Typer's `app` object is callable and works directly as a `[project.scripts]` entry point (no wrapper function needed). This is the standard pattern.
   - What's unclear: Nothing -- this is well-established.
   - Recommendation: Use `navigator = "navigator.cli:app"` directly.

2. **Config file permissions**
   - What we know: Config contains paths but no secrets. Secrets will be in a separate file.
   - What's unclear: Whether config.toml needs restrictive permissions (0600).
   - Recommendation: Default file permissions are fine for config.toml since it contains no secrets. The secrets file (future phase) will need 0600.

## Sources

### Primary (HIGH confidence)
- [Typer official docs](https://typer.tiangolo.com/tutorial/commands/) -- command registration, callbacks, version option
- [Python Packaging Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) -- pyproject.toml structure
- [Hatch build configuration](https://hatch.pypa.io/latest/config/build/#packages) -- src layout `packages` directive
- PyPI JSON API -- verified all package versions on 2026-03-23

### Secondary (MEDIUM confidence)
- STACK.md research (project-internal) -- stack selection rationale
- ARCHITECTURE.md research (project-internal) -- structure patterns
- PITFALLS.md research (project-internal) -- pitfalls #8 (state corruption) and #9 (stale crontab paths)

### Tertiary (LOW confidence)
- None -- all findings verified against primary sources.

## Project Constraints (from CLAUDE.md)

- GSD workflow enforcement: Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
- No specific coding conventions established yet (this phase establishes them).
- Technology stack fully specified in CLAUDE.md embedded STACK.md section.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries verified on PyPI, versions current, APIs confirmed via official docs
- Architecture: HIGH -- src layout + Typer + hatchling is the standard modern Python CLI pattern
- Pitfalls: HIGH -- hatchling src-layout misconfiguration is a well-documented issue; path resolution pitfall is domain-specific but straightforward

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable domain, 30-day validity)
