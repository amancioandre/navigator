"""Navigator execution logger -- per-execution log file writing and reading."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class LogEntry:
    """Parsed metadata from an execution log file."""

    path: Path
    command: str
    timestamp: str
    exit_code: int
    duration: str
    attempt: int
    error: str | None = None


def write_execution_log(
    log_dir: Path,
    command_name: str,
    attempt: int,
    returncode: int,
    duration: float,
    stdout: str,
    stderr: str,
    error: str | None = None,
) -> Path:
    """Write a per-execution log file with metadata header and combined output.

    Creates ``{log_dir}/{command_name}/{YYYYMMDD}T{HHMMSS}_{microseconds}Z.log``.
    Returns the path to the created log file.
    """
    command_dir = log_dir / command_name
    command_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(UTC)
    filename = now.strftime("%Y%m%dT%H%M%S") + f"_{now.microsecond:06d}Z.log"
    log_path = command_dir / filename

    header_lines = [
        f"command: {command_name}",
        f"timestamp: {now.isoformat()}",
        f"attempt: {attempt}",
        f"exit_code: {returncode}",
        f"duration: {duration:.2f}s",
    ]
    if error:
        header_lines.append(f"error: {error}")

    combined_output = ""
    if stdout:
        combined_output += stdout
    if stderr:
        if combined_output and not combined_output.endswith("\n"):
            combined_output += "\n"
        combined_output += stderr

    content = "\n".join(header_lines) + "\n---\n" + combined_output
    log_path.write_text(content)

    return log_path


def list_execution_logs(
    log_dir: Path,
    command_name: str,
    count: int = 10,
) -> list[LogEntry]:
    """List recent execution logs for a command, newest first.

    Scans ``{log_dir}/{command_name}/`` for ``*.log`` files, sorts by
    filename descending (newest first), and returns up to ``count`` entries.
    Returns an empty list if the directory does not exist.
    """
    command_dir = log_dir / command_name
    if not command_dir.is_dir():
        return []

    log_files = sorted(command_dir.glob("*.log"), reverse=True)
    entries: list[LogEntry] = []

    for log_file in log_files[:count]:
        text = log_file.read_text()
        parts = text.split("---\n", 1)
        if not parts:
            continue

        header = parts[0]
        fields: dict[str, str] = {}
        for line in header.strip().splitlines():
            if ": " in line:
                key, value = line.split(": ", 1)
                fields[key.strip()] = value.strip()

        entries.append(
            LogEntry(
                path=log_file,
                command=fields.get("command", ""),
                timestamp=fields.get("timestamp", ""),
                exit_code=int(fields.get("exit_code", "-1")),
                duration=fields.get("duration", "0.00s"),
                attempt=int(fields.get("attempt", "0")),
                error=fields.get("error"),
            )
        )

    return entries


def read_log_content(log_path: Path) -> str:
    """Read the body content of a log file (everything after the ``---`` separator).

    Used by ``navigator logs --tail`` to display execution output.
    """
    text = log_path.read_text()
    parts = text.split("---\n", 1)
    if len(parts) < 2:
        return ""
    return parts[1]
