"""Navigator doctor -- health-check system with auto-fix capability.

Runs structured health checks against database, binary, registered paths,
crontab sync, and systemd service. Each check returns pass/fail/warn.
Auto-fix mode applies safe remediations (directory creation, stale entry cleanup).
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from navigator.config import NavigatorConfig


@dataclass
class CheckResult:
    """Result of a single health check."""

    name: str
    status: str  # "pass", "fail", "warn"
    message: str
    fixable: bool = False
    fixed: bool = False


@dataclass
class DoctorResult:
    """Aggregated result of all health checks."""

    checks: list[CheckResult] = field(default_factory=list)

    @property
    def summary(self) -> dict[str, int]:
        return {
            "total": len(self.checks),
            "passed": sum(1 for c in self.checks if c.status == "pass"),
            "failed": sum(1 for c in self.checks if c.status == "fail"),
            "warned": sum(1 for c in self.checks if c.status == "warn"),
        }


def _check_database(config: NavigatorConfig) -> CheckResult:
    """Check database connectivity and table existence."""
    from navigator.db import get_connection, init_db

    try:
        conn = get_connection(config.db_path)
        init_db(conn)
        row = conn.execute("SELECT count(*) FROM commands").fetchone()
        count = row[0]
        conn.close()
        return CheckResult(
            name="Database",
            status="pass",
            message=f"Database OK ({count} commands)",
        )
    except Exception as e:
        return CheckResult(
            name="Database",
            status="fail",
            message=f"Database error: {e}",
        )


def _check_navigator_binary() -> CheckResult:
    """Check if navigator binary is on PATH."""
    path = shutil.which("navigator")
    if path is not None:
        return CheckResult(
            name="Navigator binary",
            status="pass",
            message=f"Found at {path}",
        )
    return CheckResult(
        name="Navigator binary",
        status="fail",
        message="navigator not found on PATH",
    )


def _check_registered_paths(config: NavigatorConfig) -> list[CheckResult]:
    """Check that all registered command environments exist."""
    from navigator.db import get_all_commands, get_connection, init_db

    results: list[CheckResult] = []
    try:
        conn = get_connection(config.db_path)
        init_db(conn)
        commands = get_all_commands(conn)
        conn.close()
    except Exception:
        return [
            CheckResult(
                name="Registered paths",
                status="fail",
                message="Could not read commands from database",
            )
        ]

    if not commands:
        return [
            CheckResult(
                name="Registered paths",
                status="pass",
                message="No commands registered",
            )
        ]

    missing = []
    for cmd in commands:
        env_path = Path(cmd.environment)
        if not env_path.is_dir():
            missing.append(cmd.name)
            results.append(
                CheckResult(
                    name=f"Path: {cmd.name}",
                    status="warn",
                    message=f"Environment directory missing: {env_path}",
                    fixable=False,
                )
            )

    if not missing:
        results.append(
            CheckResult(
                name="Registered paths",
                status="pass",
                message=f"All {len(commands)} command paths exist",
            )
        )

    return results


def _check_crontab_sync(config: NavigatorConfig) -> list[CheckResult]:
    """Check that crontab entries match registered commands."""
    from navigator.config import get_data_dir
    from navigator.db import get_all_commands, get_connection, init_db
    from navigator.scheduler import CrontabManager

    results: list[CheckResult] = []

    try:
        conn = get_connection(config.db_path)
        init_db(conn)
        commands = get_all_commands(conn)
        conn.close()
        command_names = {cmd.name for cmd in commands}
    except Exception:
        return [
            CheckResult(
                name="Crontab sync",
                status="fail",
                message="Could not read commands from database",
            )
        ]

    try:
        lock_path = get_data_dir() / "crontab.lock"
        manager = CrontabManager(lock_path)
        entries = manager.list_schedules()
    except Exception as e:
        return [
            CheckResult(
                name="Crontab sync",
                status="warn",
                message=f"Could not read crontab: {e}",
            )
        ]

    stale = []
    for entry in entries:
        cmd_name = entry["command"]
        if cmd_name not in command_names:
            stale.append(cmd_name)
            results.append(
                CheckResult(
                    name=f"Crontab: {cmd_name}",
                    status="warn",
                    message=f"Stale crontab entry for '{cmd_name}' (not in registry)",
                    fixable=True,
                )
            )

    if not stale:
        results.append(
            CheckResult(
                name="Crontab sync",
                status="pass",
                message=f"All {len(entries)} crontab entries match registered commands"
                if entries
                else "No crontab entries",
            )
        )

    return results


def _check_service() -> CheckResult:
    """Check systemd service status."""
    from navigator.service import get_service_path, service_control

    service_path = get_service_path()
    if not service_path.exists():
        return CheckResult(
            name="Service",
            status="pass",
            message="Service not installed (optional)",
        )

    try:
        result = service_control("status")
        if result.returncode == 0:
            return CheckResult(
                name="Service",
                status="pass",
                message="Service is active",
            )
        return CheckResult(
            name="Service",
            status="warn",
            message=f"Service is not active (exit code {result.returncode})",
        )
    except Exception as e:
        return CheckResult(
            name="Service",
            status="warn",
            message=f"Could not check service: {e}",
        )


def _apply_fixes(checks: list[CheckResult], config: NavigatorConfig) -> None:
    """Apply safe auto-fixes for fixable issues."""
    from navigator.config import get_data_dir
    from navigator.scheduler import CrontabManager

    # Always ensure log and data directories exist
    config.log_dir.mkdir(parents=True, exist_ok=True)
    get_data_dir().mkdir(parents=True, exist_ok=True)

    for check in checks:
        if not check.fixable or check.status not in ("fail", "warn"):
            continue

        # Stale crontab entries: remove them
        if "crontab" in check.name.lower() and "stale" in check.message.lower():
            try:
                # Extract command name from check name "Crontab: cmd_name"
                cmd_name = check.name.split(": ", 1)[1]
                lock_path = get_data_dir() / "crontab.lock"
                manager = CrontabManager(lock_path)
                manager.unschedule(cmd_name)
                check.fixed = True
            except Exception:
                pass  # Could not fix, leave as-is


def run_doctor(config: NavigatorConfig, fix: bool = False) -> DoctorResult:
    """Run all health checks and optionally apply fixes.

    Args:
        config: Navigator configuration.
        fix: If True, apply safe auto-fixes for fixable issues.

    Returns:
        DoctorResult with all check results and summary.
    """
    checks: list[CheckResult] = []
    checks.append(_check_database(config))
    checks.append(_check_navigator_binary())
    checks.extend(_check_registered_paths(config))
    checks.extend(_check_crontab_sync(config))
    checks.append(_check_service())

    if fix:
        _apply_fixes(checks, config)

    return DoctorResult(checks=checks)
