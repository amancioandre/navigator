"""Navigator execution engine -- launches Claude Code subprocesses with environment isolation."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess

from navigator.models import Command

logger = logging.getLogger(__name__)

ENV_WHITELIST: tuple[str, ...] = ("PATH", "HOME", "LANG", "TERM", "SHELL")


def build_clean_env(secrets: dict[str, str] | None = None) -> dict[str, str]:
    """Build a clean environment dict from whitelisted parent vars plus secrets.

    Only PATH, HOME, LANG, TERM, and SHELL are copied from the parent
    process environment. All other parent variables are excluded.
    Secrets (if provided) are merged in after the whitelist.
    """
    env: dict[str, str] = {}

    for key in ENV_WHITELIST:
        value = os.environ.get(key)
        if value is not None:
            env[key] = value

    if secrets:
        for key, value in secrets.items():
            env[key] = value

    return env


def build_command_args(prompt: str, allowed_tools: list[str]) -> list[str]:
    """Build the claude CLI argument list.

    Constructs: claude -p <prompt> --print [--allowedTools <tool>]...
    Never includes --dangerously-skip-permissions.
    """
    args = ["claude", "-p", prompt, "--print"]

    for tool in allowed_tools:
        args.extend(["--allowedTools", tool])

    return args


def execute_command(cmd: Command) -> subprocess.CompletedProcess[str]:
    """Execute a registered command as a Claude Code subprocess.

    Validates that the claude CLI is available and the working directory
    exists before launching. Builds a clean environment with only
    whitelisted variables plus injected secrets.

    Raises:
        FileNotFoundError: If claude CLI is not on PATH or cwd does not exist.
    """
    if shutil.which("claude") is None:
        msg = "claude CLI not found on PATH. Install Claude Code or verify PATH."
        raise FileNotFoundError(msg)

    if not cmd.environment.is_dir():
        msg = f"Working directory does not exist: {cmd.environment}"
        raise FileNotFoundError(msg)

    from navigator.secrets import load_secrets

    secrets = load_secrets(cmd.secrets)
    env = build_clean_env(secrets)
    args = build_command_args(cmd.prompt, cmd.allowed_tools)

    logger.info("Executing command '%s' in %s", cmd.name, cmd.environment)

    result = subprocess.run(
        args,
        env=env,
        cwd=str(cmd.environment),
        capture_output=True,
        text=True,
    )

    logger.info("Command '%s' exited with code %d", cmd.name, result.returncode)

    return result
