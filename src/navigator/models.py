"""Navigator command models — Pydantic models for command validation and serialization."""

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
