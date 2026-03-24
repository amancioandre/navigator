"""Navigator models — Pydantic models for command and watcher validation and serialization."""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class CommandStatus(StrEnum):
    """Status of a registered command."""

    ACTIVE = "active"
    PAUSED = "paused"


class WatcherStatus(StrEnum):
    """Status of a registered watcher."""

    ACTIVE = "active"
    PAUSED = "paused"


class Command(BaseModel):
    """A registered Navigator command.

    Validates command names against the pattern ^[a-z0-9][a-z0-9-]*$,
    generates UUID4 ids, and defaults to active status.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    prompt: str
    environment: Path
    secrets: Path | None = None
    allowed_tools: list[str] = Field(default_factory=list)
    namespace: str = "default"
    status: CommandStatus = CommandStatus.ACTIVE
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Enforce lowercase alphanumeric with hyphens, no leading hyphen."""
        if not re.match(r"^[a-z0-9][a-z0-9-]*$", v):
            msg = (
                f"Invalid command name '{v}': must match ^[a-z0-9][a-z0-9-]*$ "
                "(lowercase alphanumeric, hyphens allowed, no leading hyphen)"
            )
            raise ValueError(msg)
        return v


_DEFAULT_IGNORE_PATTERNS: list[str] = [
    ".git/**",
    "*.swp",
    "*.tmp",
    "*~",
    "__pycache__/**",
]


class Watcher(BaseModel):
    """A registered file watcher linked to a command.

    Monitors a filesystem path for changes and triggers the associated command
    with debounce, time-window, and ignore-pattern filtering.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    command_name: str
    watch_path: Path
    patterns: list[str] = Field(default_factory=lambda: ["*"])
    ignore_patterns: list[str] = Field(
        default_factory=lambda: list(_DEFAULT_IGNORE_PATTERNS)
    )
    debounce_ms: int = 500
    active_hours: str | None = None
    recursive: bool = True
    status: WatcherStatus = WatcherStatus.ACTIVE
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    @field_validator("debounce_ms")
    @classmethod
    def validate_debounce_ms(cls, v: int) -> int:
        """Ensure debounce_ms is greater than 0."""
        if v <= 0:
            msg = "debounce_ms must be greater than 0"
            raise ValueError(msg)
        return v

    @field_validator("active_hours")
    @classmethod
    def validate_active_hours(cls, v: str | None) -> str | None:
        """Validate active_hours format as HH:MM-HH:MM."""
        if v is None:
            return v
        pattern = r"^\d{2}:\d{2}-\d{2}:\d{2}$"
        if not re.match(pattern, v):
            msg = f"active_hours must match HH:MM-HH:MM format, got '{v}'"
            raise ValueError(msg)
        # Validate that times are actually parseable
        start_str, end_str = v.split("-")
        from datetime import time as dt_time

        try:
            parts = start_str.split(":")
            dt_time(int(parts[0]), int(parts[1]))
            parts = end_str.split(":")
            dt_time(int(parts[0]), int(parts[1]))
        except (ValueError, IndexError) as e:
            msg = f"active_hours contains invalid time values: {e}"
            raise ValueError(msg) from e
        return v
