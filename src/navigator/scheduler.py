"""Navigator scheduler -- crontab management with file locking.

Wraps python-crontab with fcntl-based file locking to prevent corruption
from concurrent crontab access. All entries are tagged with a navigator
comment prefix for identification and management.
"""

from __future__ import annotations

import fcntl
import shutil
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from crontab import CronTab

COMMENT_PREFIX = "navigator"


class CrontabManager:
    """Manages Navigator entries in the system crontab with file locking."""

    def __init__(self, lock_path: Path) -> None:
        self.lock_path = lock_path

    def _make_comment(self, command_name: str) -> str:
        """Build the tag comment for a crontab entry."""
        return f"{COMMENT_PREFIX}:{command_name}"

    def _resolve_navigator_path(self) -> str:
        """Get absolute path to navigator binary for crontab entries.

        Raises FileNotFoundError if navigator is not on PATH.
        """
        path = shutil.which("navigator")
        if path is None:
            msg = (
                "navigator CLI not found on PATH. "
                "Cannot create crontab entry. "
                "Ensure navigator is globally installed via 'uv tool install'."
            )
            raise FileNotFoundError(msg)
        return path

    @contextmanager
    def _lock(self):
        """Acquire exclusive file lock with 10-second timeout.

        Uses fcntl.flock with LOCK_EX|LOCK_NB in a retry loop.
        Covers the entire read-modify-write cycle (D-07).

        Raises TimeoutError if lock cannot be acquired within 10 seconds.
        """
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_fd = open(self.lock_path, "w")  # noqa: SIM115
        deadline = time.monotonic() + 10
        try:
            while True:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        lock_fd.close()
                        msg = (
                            "Could not acquire crontab lock within 10 seconds. "
                            "Another navigator process may be modifying the crontab."
                        )
                        raise TimeoutError(msg) from None
                    time.sleep(0.1)
            yield
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()

    def schedule(self, command_name: str, cron_expr: str) -> None:
        """Add or update a crontab entry for a command.

        Resolves the navigator binary path, removes any existing entry
        for the same command (idempotent update), creates a new tagged
        entry, validates, writes, and verifies.

        Raises:
            FileNotFoundError: If navigator is not on PATH.
            ValueError: If cron_expr is invalid.
            RuntimeError: If post-write verification fails.
        """
        nav_path = self._resolve_navigator_path()
        comment = self._make_comment(command_name)

        with self._lock():
            cron = CronTab(user=True)

            # Remove existing entry if any (idempotent update)
            existing = list(cron.find_comment(comment))
            for job in existing:
                cron.remove(job)

            # Create new entry
            job = cron.new(
                command=f"{nav_path} exec {command_name}",
                comment=comment,
            )

            try:
                job.setall(cron_expr)
            except (KeyError, ValueError) as exc:
                msg = f"Invalid cron expression '{cron_expr}': {exc}"
                raise ValueError(msg) from exc

            if not job.is_valid():
                msg = f"Invalid cron expression: {cron_expr}"
                raise ValueError(msg)

            cron.write()

        # Verify after write (D-11) -- outside lock since read-only
        if not self._verify_entry(command_name):
            msg = f"Post-write verification failed: entry for '{command_name}' not found in crontab"
            raise RuntimeError(msg)

    def unschedule(self, command_name: str) -> bool:
        """Remove a crontab entry for a command.

        Returns True if entries were found and removed, False otherwise.
        """
        comment = self._make_comment(command_name)

        with self._lock():
            cron = CronTab(user=True)
            existing = list(cron.find_comment(comment))

            if not existing:
                return False

            for job in existing:
                cron.remove(job)

            cron.write()

        return True

    def list_schedules(self) -> list[dict[str, Any]]:
        """List all navigator-tagged crontab entries.

        Returns a list of dicts with command, schedule, enabled, and
        cron_command keys. No lock needed (read-only, single atomic read).
        """
        cron = CronTab(user=True)
        entries: list[dict[str, Any]] = []

        for job in cron:
            if job.comment.startswith(f"{COMMENT_PREFIX}:"):
                cmd_name = job.comment.split(":", 1)[1]
                entries.append({
                    "command": cmd_name,
                    "schedule": str(job.slices),
                    "enabled": str(job.is_enabled()),
                    "cron_command": str(job.command),
                })

        return entries

    def _verify_entry(self, command_name: str) -> bool:
        """Re-read crontab and verify entry exists (D-11)."""
        cron = CronTab(user=True)
        comment = self._make_comment(command_name)
        return len(list(cron.find_comment(comment))) > 0
