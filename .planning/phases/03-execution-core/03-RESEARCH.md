# Phase 3: Execution Core - Research

**Researched:** 2026-03-24
**Domain:** Python subprocess management, secret injection, Claude Code CLI invocation
**Confidence:** HIGH

## Summary

This phase implements `navigator exec <command>` -- the core execution engine that launches Claude Code subprocesses with secret injection and environment isolation. The domain is well-understood: Python's `subprocess.run` with explicit `env` and `cwd` parameters, combined with `python-dotenv` for `.env` file parsing.

The key technical challenges are: (1) building a clean environment whitelist that gives Claude Code enough to function without leaking parent state, (2) parsing secrets from `.env` files without exposing them in logs or CLI arguments, and (3) correctly assembling the `claude` CLI command with `--allowedTools` flags.

**Primary recommendation:** Use `subprocess.run` with an explicitly constructed `env` dict (whitelist approach) and `cwd` set to the command's environment path. Parse secrets with `dotenv_values()` from python-dotenv. Never interpolate secret values into log messages or command-line arguments.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Invoke Claude Code via `claude` CLI using `subprocess.run`
- **D-02:** Pass the prompt using the `--print` flag with `-p` for the prompt text: `claude -p "..." --print`
- **D-03:** Pass allowed tools via `--allowedTools` flag, one per tool: `--allowedTools "tool1" --allowedTools "tool2"`
- **D-04:** Do NOT use `--dangerously-skip-permissions` -- explicit `--allowedTools` per command is safer and more granular
- **D-05:** Secret files use `.env` format (KEY=VALUE per line)
- **D-06:** Parse secrets using `python-dotenv` library
- **D-07:** If the secrets file does not exist or path is None, skip injection and log a warning. Command may work without secrets.
- **D-08:** No validation of secret values -- values are opaque strings. Only validate the file exists and is readable.
- **D-09:** Whitelist approach -- start with empty environment, then add only: PATH, HOME, LANG, TERM, SHELL from parent process, plus injected secrets
- **D-10:** PATH must pass through -- Claude Code needs it to find executables. HOME needed for config files.
- **D-11:** Include LANG, TERM, SHELL -- needed for proper terminal behavior in subprocess
- **D-12:** No custom environment variables in this phase
- **D-13:** Attempting to exec a paused command returns error: "Command 'X' is paused. Run `navigator resume X` first."
- **D-14:** Exit code 1 when attempting to exec a paused command

### Claude's Discretion
- Internal module organization (single `executor.py` vs multiple files)
- Whether to create a helper function for building the subprocess command list
- How to structure the secret-loading utility (inline vs separate module)
- Test approach for subprocess execution (mock subprocess.run vs integration tests)

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EXEC-01 | User can run a registered command as a Claude Code subprocess with pre-configured `--allowedTools` | subprocess.run with command list built from Command model fields; `--allowedTools` flag per tool |
| EXEC-02 | Executor reads secrets from the command's secrets path and injects them as environment variables | python-dotenv `dotenv_values()` returns dict; merge into subprocess env dict |
| EXEC-03 | Secrets are never logged, never passed as CLI arguments, and never visible in process tables | Secrets go in env dict only (not in args); log redaction of secret keys; env vars visible in /proc only to same user (acceptable for single-user) |
| EXEC-07 | Executor runs commands in the registered environment path (working directory) | subprocess.run `cwd` parameter set to `cmd.environment` |
| EXEC-08 | Executor builds a clean environment (not inheriting full parent env) with only declared variables | Explicit `env` dict with whitelist of PATH, HOME, LANG, TERM, SHELL from parent, plus secrets |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Tech stack:** Python, globally installable via pip/uv
- **Build:** hatchling backend, uv for project management
- **CLI:** Typer with Annotated syntax, Rich for output
- **Lint/Format:** ruff (configured in pyproject.toml)
- **Testing:** pytest with `uv run pytest`
- **Patterns:** Lazy imports inside CLI commands, Rich Console at module level, connection close in finally blocks
- **DB:** SQLite with WAL mode, autocommit=True for PRAGMAs then autocommit=False

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-dotenv | 1.2.2 | Parse .env secret files | `dotenv_values()` returns a dict without side effects. Handles comments, quoting, multiline. Locked decision D-06. |
| subprocess (stdlib) | N/A | Launch Claude Code CLI | `subprocess.run` with `env`, `cwd`, `capture_output`. Locked decision D-01. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shutil (stdlib) | N/A | `shutil.which("claude")` | Validate claude CLI is on PATH before attempting execution |
| os (stdlib) | N/A | `os.environ.get()` for whitelist vars | Build clean environment from parent process |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| python-dotenv | Manual parsing | Manual parsing misses edge cases (quoted values, multiline, comments, export prefix). Not worth the risk. |
| subprocess.run | asyncio.create_subprocess_exec | Async is overkill for Phase 3 (single command, wait for completion). Async may be needed in Phase 4+ for timeouts/streaming. |

**Installation:**
```bash
uv add python-dotenv>=1.2
```

**Version verification:** python-dotenv 1.2.2 is the latest on PyPI as of 2026-03-24 (verified via `pip index versions`).

## Architecture Patterns

### Recommended Module Structure
```
src/navigator/
    executor.py        # execute_command() + build_env() + build_command_args()
    secrets.py         # load_secrets() from .env files
    cli.py             # exec_command() Typer handler (existing stub)
```

**Recommendation:** Split into two new modules -- `executor.py` for subprocess orchestration and `secrets.py` for secret loading. This keeps concerns separated and makes both independently testable. The executor module owns the subprocess call; the secrets module owns .env parsing.

### Pattern 1: Clean Environment Construction
**What:** Build subprocess environment from scratch using a whitelist
**When to use:** Every exec invocation
**Example:**
```python
import os

# Whitelisted parent variables that Claude Code needs to function
ENV_WHITELIST = ("PATH", "HOME", "LANG", "TERM", "SHELL")

def build_clean_env(secrets: dict[str, str | None] | None = None) -> dict[str, str]:
    """Build a clean environment dict from whitelisted parent vars + secrets."""
    env: dict[str, str] = {}

    # Copy only whitelisted variables from parent
    for key in ENV_WHITELIST:
        value = os.environ.get(key)
        if value is not None:
            env[key] = value

    # Merge secrets (skip None values from dotenv)
    if secrets:
        for key, value in secrets.items():
            if value is not None:
                env[key] = value

    return env
```

### Pattern 2: Claude Code Command Assembly
**What:** Build the CLI argument list for subprocess.run
**When to use:** Every exec invocation
**Example:**
```python
def build_command_args(prompt: str, allowed_tools: list[str]) -> list[str]:
    """Build the claude CLI command list."""
    args = ["claude", "-p", prompt, "--print"]

    for tool in allowed_tools:
        args.extend(["--allowedTools", tool])

    return args
```

### Pattern 3: Secret-Safe Logging
**What:** Log that secrets were loaded without revealing values
**When to use:** When loading secrets, when building environment
**Example:**
```python
import logging

logger = logging.getLogger(__name__)

def load_secrets(secrets_path: Path | None) -> dict[str, str | None]:
    """Load secrets from .env file. Returns empty dict if path is None or missing."""
    if secrets_path is None:
        return {}

    if not secrets_path.exists():
        logger.warning("Secrets file not found: %s (continuing without secrets)", secrets_path)
        return {}

    if not secrets_path.is_file():
        logger.warning("Secrets path is not a file: %s (continuing without secrets)", secrets_path)
        return {}

    from dotenv import dotenv_values
    secrets = dotenv_values(secrets_path)
    # Log keys only, NEVER values
    logger.info("Loaded %d secret(s) from %s: %s", len(secrets), secrets_path, list(secrets.keys()))
    return secrets
```

### Pattern 4: Main Execution Flow
**What:** The full exec flow from command lookup to subprocess call
**When to use:** `navigator exec <command>`
**Example:**
```python
import subprocess
from pathlib import Path

def execute_command(cmd: Command) -> subprocess.CompletedProcess[str]:
    """Execute a registered command as a Claude Code subprocess."""
    # Load secrets
    secrets = load_secrets(cmd.secrets)

    # Build clean environment
    env = build_clean_env(secrets)

    # Build command args
    args = build_command_args(cmd.prompt, cmd.allowed_tools)

    # Execute
    result = subprocess.run(
        args,
        env=env,
        cwd=str(cmd.environment),
        capture_output=True,
        text=True,
    )

    return result
```

### Anti-Patterns to Avoid
- **Passing secrets as CLI arguments:** `claude -p "use API_KEY=abc123"` -- this leaks secrets in `ps` output and `/proc/PID/cmdline`. Secrets must go in env vars only.
- **Inheriting full parent environment:** `subprocess.run(..., env=None)` inherits everything. Always pass explicit `env` dict.
- **Logging secret values:** `logger.info(f"Secret: {key}={value}")` -- log key names only.
- **Using `shell=True`:** Opens shell injection risk. Always use list-form args with `shell=False` (the default).
- **String-building the command:** `f"claude -p '{prompt}'"` -- use list form to avoid quoting/injection issues.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| .env parsing | Custom KEY=VALUE parser | python-dotenv `dotenv_values()` | Handles quoting (`"val"`, `'val'`), comments (`# ...`), `export` prefix, multiline values, empty values, escaped characters |
| CLI arg assembly | String concatenation + shlex | List of strings to subprocess.run | Python's subprocess handles escaping correctly with list form |
| Path resolution | Manual `os.path.join` | `resolve_path()` from config.py | Already handles `~` expansion and absolute resolution |

## Common Pitfalls

### Pitfall 1: Claude Code Needs More Than Just PATH
**What goes wrong:** Subprocess launches but Claude Code behaves oddly -- no color output, locale errors, or config not found.
**Why it happens:** Claude Code expects HOME (for `~/.config/`), LANG (for locale), TERM (for terminal capabilities), and SHELL.
**How to avoid:** Include all five whitelist vars: PATH, HOME, LANG, TERM, SHELL. Per D-09/D-10/D-11.
**Warning signs:** Encoding errors, missing config warnings, garbled terminal output.

### Pitfall 2: dotenv_values Returns None for Valueless Keys
**What goes wrong:** `.env` file has a key with no value (e.g., `MY_VAR` alone on a line), `dotenv_values` returns `{"MY_VAR": None}`, and passing `None` to `env` dict raises TypeError.
**Why it happens:** `dotenv_values` distinguishes between `KEY=` (empty string) and `KEY` (None).
**How to avoid:** Filter out None values when merging secrets into the env dict.
**Warning signs:** TypeError in subprocess.run about env values.

### Pitfall 3: cwd Must Exist
**What goes wrong:** `subprocess.run(cwd="/nonexistent")` raises `FileNotFoundError`.
**Why it happens:** The environment path was registered but the directory was later deleted or moved.
**How to avoid:** Validate that `cmd.environment` exists and is a directory before calling subprocess.run. Print a clear error message if not.
**Warning signs:** FileNotFoundError traceback.

### Pitfall 4: Secret File Permissions
**What goes wrong:** Secrets file is world-readable, leaking secrets to other users.
**Why it happens:** Default file permissions on Linux are often 644.
**How to avoid:** Warn (not error) if the secrets file has permissions broader than owner-only (mode 0o600). This is informational for a single-user system.
**Warning signs:** `ls -la` shows `-rw-r--r--` on secrets files.

### Pitfall 5: claude Binary Not on PATH
**What goes wrong:** `subprocess.run(["claude", ...])` raises `FileNotFoundError` because `claude` is not in the whitelisted PATH.
**Why it happens:** Claude Code is installed in a non-standard location not on the default PATH.
**How to avoid:** Use `shutil.which("claude")` to verify before execution. If not found, provide a clear error with suggestion to check PATH.
**Warning signs:** FileNotFoundError: [Errno 2] No such file or directory: 'claude'.

## Code Examples

### Full exec_command CLI Handler
```python
@app.command(name="exec")
def exec_command(
    name: Annotated[str, typer.Argument(help="Command name to execute")],
) -> None:
    """Execute a registered command."""
    from navigator.config import load_config
    from navigator.db import get_command_by_name, get_connection, init_db
    from navigator.executor import execute_command

    config = load_config()
    conn = get_connection(config.db_path)
    try:
        init_db(conn)
        cmd = get_command_by_name(conn, name)
        if cmd is None:
            console.print(f"[red]Command '{name}' not found.[/red]")
            raise typer.Exit(code=1)

        if cmd.status == "paused":
            console.print(
                f"[red]Command '{name}' is paused. "
                f"Run `navigator resume {name}` first.[/red]"
            )
            raise typer.Exit(code=1)

        result = execute_command(cmd)
        if result.stdout:
            console.print(result.stdout)
        if result.returncode != 0:
            console.print(f"[red]Command '{name}' exited with code {result.returncode}[/red]")
            if result.stderr:
                console.print(f"[dim]{result.stderr}[/dim]")
            raise typer.Exit(code=result.returncode)
    finally:
        conn.close()
```

### dotenv_values Usage
```python
from dotenv import dotenv_values
from pathlib import Path

# Returns dict[str, str | None]
secrets = dotenv_values(Path("/home/user/.secrets/my-cmd.env"))
# {"API_KEY": "abc123", "DB_HOST": "localhost", "EMPTY_VAR": ""}

# Filter None values for subprocess env
clean_secrets = {k: v for k, v in secrets.items() if v is not None}
```

### subprocess.run with Environment Isolation
```python
import subprocess

result = subprocess.run(
    ["claude", "-p", "Do the thing", "--print", "--allowedTools", "Read", "--allowedTools", "Bash"],
    env={"PATH": "/usr/bin:/usr/local/bin", "HOME": "/home/user", "LANG": "en_US.UTF-8", "TERM": "xterm-256color", "SHELL": "/bin/zsh", "API_KEY": "secret-value"},
    cwd="/home/user/project",
    capture_output=True,
    text=True,
)
# result.returncode, result.stdout, result.stderr
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| python-dotenv 1.0.x | python-dotenv 1.2.x | 2025 | Added `dotenv_values` type hints, better multiline support |
| subprocess.Popen | subprocess.run | Python 3.5+ | `run` is the recommended high-level API; Popen only needed for streaming/advanced |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_executor.py tests/test_secrets.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXEC-01 | exec launches claude subprocess with --allowedTools | unit (mock subprocess.run) | `uv run pytest tests/test_executor.py::test_execute_builds_correct_args -x` | Wave 0 |
| EXEC-02 | Secrets loaded from .env and injected as env vars | unit | `uv run pytest tests/test_secrets.py::test_load_secrets_from_env -x` | Wave 0 |
| EXEC-03 | Secrets not in logs, not in CLI args | unit | `uv run pytest tests/test_executor.py::test_secrets_not_in_args -x` | Wave 0 |
| EXEC-07 | Subprocess runs in registered working directory | unit (mock subprocess.run, verify cwd) | `uv run pytest tests/test_executor.py::test_execute_uses_cwd -x` | Wave 0 |
| EXEC-08 | Clean environment with only whitelisted vars | unit | `uv run pytest tests/test_executor.py::test_build_clean_env -x` | Wave 0 |
| D-13 | Paused command returns error message | unit (CLI test) | `uv run pytest tests/test_cli.py::test_exec_paused_command -x` | Wave 0 |
| D-14 | Paused command exits code 1 | unit (CLI test) | `uv run pytest tests/test_cli.py::test_exec_paused_exit_code -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_executor.py tests/test_secrets.py tests/test_cli.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_executor.py` -- covers EXEC-01, EXEC-03, EXEC-07, EXEC-08
- [ ] `tests/test_secrets.py` -- covers EXEC-02
- [ ] New test cases in `tests/test_cli.py` -- covers D-13, D-14 (exec paused command)

### Test Strategy Recommendation
**Mock subprocess.run** for unit tests. Do NOT call the real `claude` CLI in unit tests -- it's slow, requires API keys, and is non-deterministic. Use `unittest.mock.patch("subprocess.run")` to verify:
- Correct argument list was built
- `env` dict contains only whitelisted keys + secrets
- `cwd` is set to the command's environment
- `capture_output=True` and `text=True` are passed

Integration tests (calling real claude) should be marked `@pytest.mark.integration` and skipped in CI.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| claude CLI | EXEC-01 (subprocess target) | Yes | 2.1.81 | None -- required |
| python3 | Runtime | Yes | 3.12.3 | None -- required |
| python-dotenv | EXEC-02 (secret parsing) | Not in project venv | 1.2.2 on PyPI | Must add to dependencies |

**Missing dependencies with no fallback:**
- python-dotenv must be added to pyproject.toml dependencies: `uv add "python-dotenv>=1.2"`

**Missing dependencies with fallback:**
- None

## Open Questions

1. **Should capture_output be True or should stdout/stderr pass through?**
   - What we know: `capture_output=True` collects output; without it, output goes to the terminal in real-time.
   - What's unclear: For interactive use (`navigator exec`), users may want to see output in real-time. For scheduled execution (Phase 4+), capture is needed for logging.
   - Recommendation: Use `capture_output=True` for Phase 3 (consistent with `--print` mode which is non-interactive). Phase 4 (logging) will need captured output anyway. Print stdout/stderr after completion.

2. **Should we validate that the claude binary exists before exec?**
   - What we know: `shutil.which("claude")` can check. subprocess.run raises FileNotFoundError if not found.
   - Recommendation: Pre-check with `shutil.which` for a better error message. This is a quality-of-life improvement, not strictly required.

## Sources

### Primary (HIGH confidence)
- Claude Code CLI `--help` output -- verified `--allowedTools`, `-p`, `--print` flags on version 2.1.81
- Python 3.12 stdlib subprocess documentation -- `subprocess.run` signature, `env` and `cwd` parameters
- python-dotenv PyPI -- version 1.2.2 verified as latest, `dotenv_values()` API confirmed
- Existing codebase -- models.py, db.py, cli.py, config.py, conftest.py patterns

### Secondary (MEDIUM confidence)
- /proc/PID/environ visibility test -- confirmed env vars are visible to same user in /proc, acceptable for single-user system

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - python-dotenv and subprocess are well-understood, versions verified
- Architecture: HIGH - patterns are straightforward subprocess management with clear separation
- Pitfalls: HIGH - verified through direct testing (env isolation, /proc visibility, dotenv None values)

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (stable domain, no fast-moving dependencies)
