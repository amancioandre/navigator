# Phase 4: Execution Hardening - Research

**Researched:** 2026-03-24
**Domain:** Python subprocess lifecycle management, retry logic, execution logging
**Confidence:** HIGH

## Summary

This phase hardens the existing `execute_command()` function in `src/navigator/executor.py` with four capabilities: retry with exponential backoff, per-execution log files, configurable timeouts with graceful termination, and process group isolation for zombie prevention. All five requirements (EXEC-04, EXEC-05, EXEC-06, EXEC-09, EXEC-10) are achievable entirely with Python stdlib (`subprocess.Popen`, `os.killpg`, `signal`, `atexit`, `time.sleep`) plus the already-installed Rich and Typer libraries for CLI output.

The current executor uses `subprocess.run()` with `capture_output=True`. This must change to `subprocess.Popen` for process group control, real-time output capture, and timeout enforcement. The key architectural shift is moving from a simple synchronous call to a managed process lifecycle with explicit PID tracking, signal handling, and cleanup guarantees.

**Primary recommendation:** Refactor `execute_command()` to use `subprocess.Popen` with `start_new_session=True`, implement retry as a wrapper around the single-execution function, and add a separate `execution_logger.py` module for log file management. Keep the `logs` CLI command in `cli.py` following established patterns.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Exponential backoff formula: `2^attempt * 1s` (1s, 2s, 4s, 8s...).
- **D-02:** Default retry count from `config.default_retry_count` (currently 3) -- already in NavigatorConfig.
- **D-03:** Failure = non-zero exit code from subprocess. Simple, universal.
- **D-04:** Log each retry attempt with attempt number and delay before sleeping.
- **D-05:** Log directory structure: `{config.log_dir}/{command_name}/{ISO_timestamp}.log`.
- **D-06:** Log file content: combined stdout + stderr with metadata header (command name, timestamp, exit code, duration, attempt number).
- **D-07:** `navigator logs <command>` shows last N log entries as Rich table. `--tail` flag shows full content of last log.
- **D-08:** No automatic log cleanup this phase -- future enhancement if needed.
- **D-09:** Default timeout from `config.default_timeout` (currently 300s/5min) -- already in NavigatorConfig.
- **D-10:** Termination signal chain: SIGTERM first, wait 5s grace period, then SIGKILL if still alive.
- **D-11:** Timeout produces exit code 124 (matching the `timeout` command convention), logged to execution log.
- **D-12:** `--timeout` optional flag on `navigator exec` -- overrides config default for that execution.
- **D-13:** Process group isolation via `start_new_session=True` in subprocess.run/Popen -- isolates entire child process tree.
- **D-14:** Kill entire process group on timeout/cleanup: `os.killpg(pgid, signal)`.
- **D-15:** Log PID at spawn for targeted cleanup and debugging.
- **D-16:** `atexit` handler + signal handlers (SIGTERM, SIGINT) to kill any active child processes on navigator exit.

### Claude's Discretion
- Whether to refactor executor.py or create separate retry.py / logging.py modules
- Popen vs subprocess.run for timeout support (Popen likely needed for process group + timeout)
- Rich table column design for `navigator logs` output
- Test approach for retry timing (mock time.sleep vs real delays)
- Whether to add `--retries` override flag on `navigator exec` alongside `--timeout`

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EXEC-04 | Executor retries failed commands with exponential backoff (`--retries N`) | Retry wrapper with `time.sleep(2**attempt)`, mock sleep in tests |
| EXEC-05 | Each execution captures stdout/stderr to per-execution log files | `execution_logger.py` module writing to `{log_dir}/{cmd_name}/{timestamp}.log` |
| EXEC-06 | User can view execution logs via `navigator logs <command>` | Typer command scanning log directory, Rich table output |
| EXEC-09 | Executor tracks child PIDs and uses process groups for cleanup (no zombies) | `Popen(start_new_session=True)` + `os.killpg()` + atexit/signal handlers |
| EXEC-10 | Executor enforces timeout per command execution | `Popen.wait(timeout=N)` with SIGTERM/SIGKILL escalation on `TimeoutExpired` |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| subprocess (stdlib) | Python 3.12 | Process spawning and management | `Popen` with `start_new_session=True` is the only way to get process group isolation + timeout + output capture in Python |
| os (stdlib) | Python 3.12 | Process group signals | `os.killpg(pgid, signal)` kills entire process tree; `os.getpgid(pid)` gets group ID |
| signal (stdlib) | Python 3.12 | Signal constants and handlers | SIGTERM (15), SIGKILL (9), SIGINT (2) for termination chain; `signal.signal()` for cleanup handlers |
| atexit (stdlib) | Python 3.12 | Exit cleanup registration | Registers cleanup function to kill active children on navigator exit |
| time (stdlib) | Python 3.12 | Retry delays | `time.sleep()` for exponential backoff; `time.monotonic()` for duration measurement |
| pathlib (stdlib) | Python 3.12 | Log directory and file management | Already used throughout project for path operations |

### Supporting (already installed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Rich | >=14.0 | Log table display | `navigator logs` command output -- Rich Table for log entries, syntax highlighting for log content |
| Typer | >=0.24.0 | CLI flags | `--timeout`, `--retries`, `--tail`, `--count` flags on exec and logs commands |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| subprocess.Popen | subprocess.run | run() has timeout param but cannot do process group kill on timeout -- it only kills the direct child, not grandchildren. Popen is required. |
| time.sleep for backoff | asyncio.sleep | Would require async executor. Current architecture is synchronous. No benefit for a blocking subprocess call. |
| Manual log files | Python logging module | logging module is for application logs, not execution output capture. Per-execution files with metadata headers are better served by direct file writes. |

**Installation:** No new dependencies needed. All functionality from Python stdlib + existing project dependencies.

## Architecture Patterns

### Recommended Module Structure
```
src/navigator/
    executor.py          # Refactored: Popen-based execution with process groups + timeout
    execution_logger.py  # NEW: Log file writing, reading, listing
    cli.py               # Extended: --timeout/--retries on exec, logs command implementation
    config.py            # Unchanged: already has default_retry_count and default_timeout
```

**Recommendation on discretion item:** Create a separate `execution_logger.py` module rather than putting logging logic in executor.py. Reasons: (1) executor.py handles process lifecycle, logger handles file I/O -- different concerns; (2) `navigator logs` CLI needs to read logs without importing execution machinery; (3) keeps executor.py focused and testable.

### Pattern 1: Popen with Process Group Isolation
**What:** Use `subprocess.Popen` with `start_new_session=True` to create an isolated process group for each execution. This ensures the child and all its descendants can be signaled as a group.
**When to use:** Every execution -- this is the core subprocess pattern for this phase.
**Example:**
```python
import os
import signal
import subprocess
import time

def _run_once(args, env, cwd, timeout):
    """Run a single subprocess with process group isolation and timeout."""
    proc = subprocess.Popen(
        args,
        env=env,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,  # D-13: new process group
    )
    pgid = os.getpgid(proc.pid)  # D-15: track PID/PGID

    try:
        stdout, stderr = proc.communicate(timeout=timeout)  # D-10: timeout enforcement
        return proc.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        # D-10: SIGTERM first
        os.killpg(pgid, signal.SIGTERM)
        try:
            proc.wait(timeout=5)  # D-10: 5s grace period
        except subprocess.TimeoutExpired:
            os.killpg(pgid, signal.SIGKILL)  # D-10: then SIGKILL
            proc.wait()
        return 124, proc.stdout.read() or "", proc.stderr.read() or ""  # D-11: exit code 124
```

### Pattern 2: Retry with Exponential Backoff
**What:** Wrap the single-execution function in a retry loop using the formula `2^attempt * 1s`.
**When to use:** Called from `execute_command()` which is the public API.
**Example:**
```python
import time

def execute_with_retry(cmd, config, timeout_override=None, retries_override=None):
    """Execute a command with retry on failure."""
    max_retries = retries_override if retries_override is not None else config.default_retry_count
    timeout = timeout_override if timeout_override is not None else config.default_timeout

    for attempt in range(max_retries + 1):  # attempt 0 is the first try
        if attempt > 0:
            delay = 2 ** attempt  # D-01: 2s, 4s, 8s...
            logger.info("Retry %d/%d for '%s' after %ds", attempt, max_retries, cmd.name, delay)
            time.sleep(delay)

        returncode, stdout, stderr = _run_once(args, env, cwd, timeout)

        if returncode == 0:  # D-03: success = zero exit code
            break

    return returncode, stdout, stderr
```

### Pattern 3: Execution Log File Format
**What:** Write a log file per execution with a metadata header followed by combined output.
**When to use:** After every execution attempt (including retries).
**Example:**
```python
from datetime import datetime, UTC
from pathlib import Path

def write_execution_log(log_dir, command_name, attempt, returncode, duration, stdout, stderr):
    """Write per-execution log file. D-05, D-06."""
    cmd_log_dir = log_dir / command_name
    cmd_log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    log_path = cmd_log_dir / f"{timestamp}.log"

    header = (
        f"command: {command_name}\n"
        f"timestamp: {datetime.now(UTC).isoformat()}\n"
        f"attempt: {attempt}\n"
        f"exit_code: {returncode}\n"
        f"duration: {duration:.2f}s\n"
        f"---\n"
    )

    log_path.write_text(header + stdout + stderr)
    return log_path
```

### Pattern 4: Global Process Tracking with Cleanup
**What:** Track active child processes in a module-level set; register atexit and signal handlers to kill them on navigator exit.
**When to use:** Registered once at module import; updated on each process spawn/completion.
**Example:**
```python
import atexit
import os
import signal

_active_processes: set[int] = set()  # PIDs of active children

def _cleanup_children():
    """Kill all active child process groups. D-16."""
    for pid in list(_active_processes):
        try:
            pgid = os.getpgid(pid)
            os.killpg(pgid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass  # Already dead
    _active_processes.clear()

atexit.register(_cleanup_children)

def _signal_handler(signum, frame):
    """Handle SIGTERM/SIGINT by cleaning up children then re-raising."""
    _cleanup_children()
    # Re-raise the signal with default handler
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum)

signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)
```

### Anti-Patterns to Avoid
- **Using subprocess.run() with timeout:** `subprocess.run(timeout=N)` only kills the direct child process, not the process group. Any grandchild processes (common with Claude Code) become orphans. Must use Popen for group control.
- **Catching TimeoutExpired without SIGKILL fallback:** A process may ignore SIGTERM. Always follow SIGTERM with a grace period and SIGKILL escalation.
- **Using proc.kill() instead of os.killpg():** `proc.kill()` only kills the direct child. `os.killpg()` kills the entire process group tree.
- **Reading proc.stdout after communicate():** After `communicate()` returns, the pipes are consumed. After `TimeoutExpired` from `communicate()`, must use `proc.stdout.read()` or `proc.stderr.read()` carefully -- the pipes may have partial data.
- **ISO timestamps with colons in filenames:** Windows-hostile but more importantly hard to tab-complete. Use `%Y%m%dT%H%M%SZ` format (no colons) for filenames, full ISO for metadata inside the log.
- **Registering signal handlers inside functions:** Signal handlers must be registered in the main thread. Registering them from a worker thread raises `ValueError`. Register at module level or in a guarded init function.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Exponential backoff | Custom retry decorator with jitter, circuit breakers | Simple `time.sleep(2**attempt)` loop per D-01 | The decision specifies a simple formula. Adding jitter/circuit breakers is overengineering for a single-user CLI tool. |
| Process tree walking | Custom /proc scanning to find child PIDs | `start_new_session=True` + `os.killpg()` | Process groups are the kernel's mechanism for this. Walking /proc is fragile, race-prone, and platform-specific. |
| Log rotation/cleanup | Custom log size checking, age-based deletion | Nothing (D-08: deferred) | User explicitly deferred log cleanup. Don't build it. |
| Structured log parsing | Custom log file parser with regex | Simple `key: value` header format + `split("---", 1)` | Metadata header is trivially parseable. No need for a log parsing library. |

**Key insight:** This phase uses exclusively Python stdlib for all heavy lifting. The temptation is to reach for `tenacity` (retry library) or `psutil` (process management) -- resist it. The backoff formula is trivial, and process groups handle cleanup. No new dependencies.

## Common Pitfalls

### Pitfall 1: Zombie Processes from Orphaned Grandchildren
**What goes wrong:** Claude Code spawns child processes (node, language servers). If you kill only the direct child, grandchildren become zombies owned by PID 1.
**Why it happens:** `subprocess.run()` and `proc.terminate()` only affect the direct child process, not descendants.
**How to avoid:** Always use `start_new_session=True` and `os.killpg()` to kill the entire process group.
**Warning signs:** `ps aux | grep defunct` shows zombie processes after navigator exits.

### Pitfall 2: TimeoutExpired Pipe Deadlock
**What goes wrong:** After `proc.communicate()` raises `TimeoutExpired`, calling `proc.communicate()` again can deadlock if the process is still running and the pipes are full.
**Why it happens:** `communicate()` reads until EOF. If the process is alive and writing, the read blocks.
**How to avoid:** After `TimeoutExpired`, kill the process group first, then call `proc.wait()`. For any remaining output, read from `proc.stdout`/`proc.stderr` directly (they may have partial data or be empty).
**Warning signs:** Navigator hangs during timeout handling.

### Pitfall 3: Signal Handlers in Non-Main Threads
**What goes wrong:** `signal.signal()` raises `ValueError: signal only works in main thread` if called from a thread.
**Why it happens:** Python restricts signal handler registration to the main thread.
**How to avoid:** Register signal handlers at module level (executed during import in main thread) or guard with `threading.current_thread() is threading.main_thread()`.
**Warning signs:** `ValueError` during test runs (pytest may import modules in threads).

### Pitfall 4: Log File Timestamp Collisions
**What goes wrong:** Two rapid executions get the same second-resolution timestamp, overwriting the first log.
**Why it happens:** ISO timestamps with second resolution are not unique under rapid retry.
**How to avoid:** Include microseconds in the filename: `%Y%m%dT%H%M%S_%fZ` or append the attempt number to the filename.
**Warning signs:** Log files disappearing or showing wrong content.

### Pitfall 5: atexit Not Called on SIGKILL
**What goes wrong:** If navigator itself is SIGKILL'd, atexit handlers never run, and child processes become orphans.
**Why it happens:** SIGKILL cannot be caught or handled -- the kernel terminates the process immediately.
**How to avoid:** This is unavoidable for SIGKILL. Handle SIGTERM and SIGINT (D-16) to cover normal shutdown. Process groups with `start_new_session=True` help because the kernel can send signals to the group independently.
**Warning signs:** Orphaned claude processes after force-killing navigator.

### Pitfall 6: Retry Attempt Numbering Off-by-One
**What goes wrong:** Retry count of 3 either runs 3 total attempts or 4 (1 original + 3 retries). Ambiguity causes bugs.
**Why it happens:** Unclear whether "retry count" means "total attempts" or "additional attempts after first failure."
**How to avoid:** Define clearly: `default_retry_count=3` means 3 retries AFTER the initial attempt, so 4 total attempts. Match user expectation from the config field name "retry_count" (count of retries, not count of attempts). Loop should be: first attempt, then up to `retry_count` additional attempts.
**Warning signs:** Tests expect different total attempt counts.

## Code Examples

### Complete Execution Flow (Recommended Architecture)
```python
# executor.py - refactored execute_command signature
def execute_command(
    cmd: Command,
    config: NavigatorConfig,
    timeout_override: int | None = None,
    retries_override: int | None = None,
) -> ExecutionResult:
    """Execute a registered command with retry, timeout, and logging."""
```

Note: `execute_command` currently takes only `Command`. The refactored version needs `NavigatorConfig` for retry count, timeout, and log directory. This changes the call site in `cli.py` -- the config is already loaded there, so pass it through.

### ExecutionResult Model
```python
# Could be a dataclass or Pydantic model
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    """Result of a command execution (possibly after retries)."""
    command_name: str
    returncode: int
    stdout: str
    stderr: str
    attempts: int
    duration: float
    timed_out: bool
    log_path: Path | None
```

### Log Directory Listing for `navigator logs`
```python
def list_execution_logs(log_dir: Path, command_name: str, count: int = 10) -> list[LogEntry]:
    """List recent execution logs for a command. D-07."""
    cmd_log_dir = log_dir / command_name
    if not cmd_log_dir.exists():
        return []

    log_files = sorted(cmd_log_dir.glob("*.log"), reverse=True)[:count]
    entries = []
    for log_file in log_files:
        header, _, body = log_file.read_text().partition("---\n")
        metadata = dict(line.split(": ", 1) for line in header.strip().splitlines() if ": " in line)
        entries.append(LogEntry(
            path=log_file,
            command=metadata.get("command", ""),
            timestamp=metadata.get("timestamp", ""),
            exit_code=int(metadata.get("exit_code", -1)),
            duration=metadata.get("duration", ""),
            attempt=int(metadata.get("attempt", 0)),
        ))
    return entries
```

### CLI Extension for exec Command
```python
@app.command(name="exec")
def exec_command(
    name: Annotated[str, typer.Argument(help="Command name to execute")],
    timeout: Annotated[int | None, typer.Option("--timeout", help="Timeout in seconds")] = None,
    retries: Annotated[int | None, typer.Option("--retries", help="Max retry attempts")] = None,
) -> None:
    """Execute a registered command."""
    # ... load config, get command ...
    result = execute_command(cmd, config, timeout_override=timeout, retries_override=retries)
```

### CLI for navigator logs
```python
@app.command()
def logs(
    name: Annotated[str, typer.Argument(help="Command name")],
    count: Annotated[int, typer.Option("--count", "-n", help="Number of entries")] = 10,
    tail: Annotated[bool, typer.Option("--tail", help="Show full content of last log")] = False,
) -> None:
    """View execution logs for a command. D-07."""
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| subprocess.run with timeout | subprocess.Popen + communicate(timeout) + process groups | Always best practice for complex lifecycle | subprocess.run timeout only kills direct child |
| psutil for process tree management | os.killpg with start_new_session=True | Process groups are older, psutil is convenience | No dependency needed -- kernel handles it |
| tenacity for retry | Simple loop + time.sleep | N/A -- tenacity is for complex retry policies | Overkill for a 5-line backoff loop |

**Deprecated/outdated:**
- `os.popen()`: Replaced by subprocess module long ago. Never use.
- `subprocess.call()`: Replaced by `subprocess.run()`. For this phase, `Popen` is needed anyway.

## Open Questions

1. **Retry count semantics: total attempts or additional retries?**
   - What we know: Config field is `default_retry_count = 3`. The name suggests "count of retries" (additional attempts after first).
   - What's unclear: Whether user expects 3 total or 4 total attempts.
   - Recommendation: Treat as 3 retries = 4 total attempts (1 initial + 3 retries). Document in help text. This matches the semantic of "retry count" and is the common convention (e.g., `urllib3.Retry(total=3)` means 3 retries).

2. **Partial output capture on timeout**
   - What we know: After `communicate()` raises `TimeoutExpired`, stdout/stderr may have partial data.
   - What's unclear: How much output will be available from pipes after timeout.
   - Recommendation: After killing the process group, attempt to read remaining pipe data. Whatever is captured goes to the log. Note in log metadata that the execution was timed out.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0+ |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `uv run pytest tests/test_executor.py -x` |
| Full suite command | `uv run pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXEC-04 | Retry with exponential backoff | unit | `uv run pytest tests/test_executor.py::TestRetry -x` | Partial (test_executor.py exists, TestRetry class needed) |
| EXEC-05 | Stdout/stderr captured to log files | unit | `uv run pytest tests/test_execution_logger.py -x` | No -- Wave 0 |
| EXEC-06 | `navigator logs <command>` CLI | unit | `uv run pytest tests/test_cli.py::TestLogs -x` | Partial (test_cli.py exists, TestLogs class needed) |
| EXEC-09 | Process group isolation, no zombies | unit | `uv run pytest tests/test_executor.py::TestProcessGroups -x` | Partial |
| EXEC-10 | Timeout enforcement | unit | `uv run pytest tests/test_executor.py::TestTimeout -x` | Partial |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_executor.py tests/test_execution_logger.py -x`
- **Per wave merge:** `uv run pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_execution_logger.py` -- covers EXEC-05, EXEC-06 log reading/writing
- [ ] New test classes in `tests/test_executor.py` -- TestRetry, TestProcessGroups, TestTimeout

## Sources

### Primary (HIGH confidence)
- Python 3.12 subprocess documentation (stdlib) -- Popen, start_new_session, communicate, TimeoutExpired
- Python 3.12 os module documentation (stdlib) -- killpg, getpgid
- Python 3.12 signal module documentation (stdlib) -- signal constants, signal handlers
- Verified via `python3 -c` that `start_new_session`, `os.killpg`, `signal.SIGTERM/SIGKILL/SIGINT` are available on Python 3.12.3

### Secondary (MEDIUM confidence)
- Exit code 124 convention from GNU coreutils `timeout` command -- widely adopted standard

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All Python stdlib, verified available on target system
- Architecture: HIGH - Well-established process management patterns, locked decisions are specific
- Pitfalls: HIGH - Known subprocess/process group gotchas from years of production usage

**Research date:** 2026-03-24
**Valid until:** Indefinite - Python stdlib APIs are stable across versions
