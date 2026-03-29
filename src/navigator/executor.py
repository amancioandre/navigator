"""Navigator execution engine -- launches Claude Code subprocesses with environment isolation.

Provides Popen-based execution with process group isolation, retry with
exponential backoff, timeout enforcement (SIGTERM/SIGKILL escalation),
and per-execution log file writing.
"""

from __future__ import annotations

import atexit
import logging
import os
import shutil
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from navigator.config import NavigatorConfig
from navigator.execution_logger import write_execution_log
from navigator.models import Command

logger = logging.getLogger(__name__)

ENV_WHITELIST: tuple[str, ...] = ("PATH", "HOME", "LANG", "TERM", "SHELL")

# Track active child process PIDs for cleanup on exit
_active_processes: set[int] = set()


@dataclass
class ExecutionResult:
    """Result of executing a command, possibly after retries."""

    command_name: str
    returncode: int
    stdout: str
    stderr: str
    attempts: int
    duration: float
    timed_out: bool
    log_path: Path | None


def _cleanup_children() -> None:
    """Kill all tracked child process groups on exit."""
    for pid in list(_active_processes):
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError, OSError):
            pass


# Register cleanup at module import time
atexit.register(_cleanup_children)


def _signal_handler(signum: int, frame: object) -> None:
    """Handle SIGTERM/SIGINT by cleaning up children then re-raising."""
    _cleanup_children()
    # Restore the default handler and re-raise the signal
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum)


# Only register signal handlers from the main thread
if threading.current_thread() is threading.main_thread():
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)


def build_clean_env(
    secrets: dict[str, str] | None = None,
    extra_env: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build a clean environment dict from whitelisted parent vars plus secrets.

    Only PATH, HOME, LANG, TERM, and SHELL are copied from the parent
    process environment. All other parent variables are excluded.
    Secrets (if provided) are merged in after the whitelist.
    Extra env vars (if provided) are merged last, for chain correlation IDs etc.
    """
    env: dict[str, str] = {}

    for key in ENV_WHITELIST:
        value = os.environ.get(key)
        if value is not None:
            env[key] = value

    if secrets:
        for key, value in secrets.items():
            env[key] = value

    if extra_env:
        for key, value in extra_env.items():
            env[key] = value

    return env


def build_command_args(prompt: str, allowed_tools: list[str], claude_path: str = "claude") -> list[str]:
    """Build the claude CLI argument list.

    Constructs: <claude_path> -p <prompt> --print [--allowedTools <tool>]...
    Never includes --dangerously-skip-permissions.

    Args:
        prompt: The prompt text to pass to claude.
        allowed_tools: List of tool names to allow via --allowedTools.
        claude_path: Absolute path to the claude binary. Defaults to "claude"
            for backward compatibility, but callers should pass the resolved
            path from shutil.which() to support cron's minimal PATH.
    """
    args = [claude_path, "-p", prompt, "--print"]

    for tool in allowed_tools:
        args.extend(["--allowedTools", tool])

    return args


def _run_once(
    args: list[str],
    env: dict[str, str],
    cwd: str,
    timeout: int | None,
) -> tuple[int, str, str]:
    """Run a subprocess once with process group isolation and timeout.

    Returns (returncode, stdout, stderr). On timeout, sends SIGTERM to the
    process group, waits 5s grace, then SIGKILL. Returns exit code 124
    on timeout (matching coreutils timeout convention).
    """
    proc = subprocess.Popen(
        args,
        env=env,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )

    pgid = os.getpgid(proc.pid)
    _active_processes.add(proc.pid)

    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return (proc.returncode, stdout, stderr)
    except subprocess.TimeoutExpired:
        # SIGTERM the entire process group
        try:
            os.killpg(pgid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError, OSError):
            pass

        # Wait 5s grace period for graceful shutdown
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # SIGKILL the process group
            try:
                os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                pass
            proc.wait()

        # Collect any partial output
        stdout = proc.stdout.read() if proc.stdout else ""
        stderr = proc.stderr.read() if proc.stderr else ""

        return (124, stdout, stderr)
    finally:
        _active_processes.discard(proc.pid)


def execute_command(
    cmd: Command,
    config: NavigatorConfig,
    timeout_override: int | None = None,
    retries_override: int | None = None,
    extra_env: dict[str, str] | None = None,
) -> ExecutionResult:
    """Execute a registered command as a Claude Code subprocess.

    Validates that the claude CLI is available and the working directory
    exists before launching. Builds a clean environment with only
    whitelisted variables plus injected secrets.

    Retries on failure with exponential backoff (2^attempt seconds).
    Enforces timeout with SIGTERM/SIGKILL escalation.

    Raises:
        FileNotFoundError: If claude CLI is not on PATH or cwd does not exist.
    """
    claude_path = shutil.which("claude")
    if claude_path is None:
        msg = "claude CLI not found on PATH. Install Claude Code or verify PATH."
        raise FileNotFoundError(msg)

    if not cmd.environment.is_dir():
        msg = f"Working directory does not exist: {cmd.environment}"
        raise FileNotFoundError(msg)

    from navigator.secrets import load_secrets

    secrets = load_secrets(cmd.secrets)
    env = build_clean_env(secrets, extra_env=extra_env)
    args = build_command_args(cmd.prompt, cmd.allowed_tools, claude_path=claude_path)

    max_retries = retries_override if retries_override is not None else config.default_retry_count
    timeout = timeout_override if timeout_override is not None else config.default_timeout

    cwd = str(cmd.environment)
    start_time = time.monotonic()
    last_returncode = -1
    last_stdout = ""
    last_stderr = ""
    last_log_path: Path | None = None
    timed_out = False

    total_attempts = 1 + max_retries  # first attempt + retries

    for attempt in range(total_attempts):
        if attempt > 0:
            delay = 2 ** attempt
            logger.info(
                "Retrying command '%s' (attempt %d/%d) after %ds delay",
                cmd.name,
                attempt + 1,
                total_attempts,
                delay,
            )
            time.sleep(delay)

        logger.info("Executing command '%s' in %s (attempt %d)", cmd.name, cmd.environment, attempt + 1)

        returncode, stdout, stderr = _run_once(args, env, cwd, timeout)

        timed_out = returncode == 124
        last_returncode = returncode
        last_stdout = stdout
        last_stderr = stderr

        duration_so_far = time.monotonic() - start_time

        last_log_path = write_execution_log(
            log_dir=config.log_dir,
            command_name=cmd.name,
            attempt=attempt + 1,
            returncode=returncode,
            duration=duration_so_far,
            stdout=stdout,
            stderr=stderr,
        )

        if returncode == 0:
            logger.info("Command '%s' succeeded on attempt %d", cmd.name, attempt + 1)
            break

        logger.warning("Command '%s' failed with code %d on attempt %d", cmd.name, returncode, attempt + 1)

    total_duration = time.monotonic() - start_time

    return ExecutionResult(
        command_name=cmd.name,
        returncode=last_returncode,
        stdout=last_stdout,
        stderr=last_stderr,
        attempts=attempt + 1,
        duration=total_duration,
        timed_out=timed_out,
        log_path=last_log_path,
    )
