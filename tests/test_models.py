"""Tests for Navigator command models — validation, defaults, and enums."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

import pytest
from pydantic import ValidationError

from navigator.models import Command, CommandStatus


class TestCommandStatus:
    """Tests for the CommandStatus enum."""

    def test_status_active_value(self):
        assert CommandStatus.ACTIVE == "active"

    def test_status_paused_value(self):
        assert CommandStatus.PAUSED == "paused"

    def test_status_has_exactly_two_members(self):
        assert len(CommandStatus) == 2


class TestCommandValidation:
    """Tests for Command name validation."""

    def test_valid_name_lowercase_with_hyphens(self):
        cmd = Command(name="my-command", prompt="test", environment=Path("/tmp"))
        assert cmd.name == "my-command"

    def test_valid_name_digits_only(self):
        cmd = Command(name="123", prompt="test", environment=Path("/tmp"))
        assert cmd.name == "123"

    def test_valid_name_mixed(self):
        cmd = Command(name="a1-b2-c3", prompt="test", environment=Path("/tmp"))
        assert cmd.name == "a1-b2-c3"

    def test_invalid_name_uppercase(self):
        with pytest.raises(ValidationError):
            Command(name="MyCommand", prompt="test", environment=Path("/tmp"))

    def test_invalid_name_spaces(self):
        with pytest.raises(ValidationError):
            Command(name="my command", prompt="test", environment=Path("/tmp"))

    def test_invalid_name_leading_hyphen(self):
        with pytest.raises(ValidationError):
            Command(name="-bad", prompt="test", environment=Path("/tmp"))

    def test_invalid_name_empty(self):
        with pytest.raises(ValidationError):
            Command(name="", prompt="test", environment=Path("/tmp"))


class TestCommandDefaults:
    """Tests for Command default field values."""

    def test_default_id_is_valid_uuid4(self):
        cmd = Command(name="test-cmd", prompt="test", environment=Path("/tmp"))
        # Should not raise
        parsed = uuid.UUID(cmd.id, version=4)
        assert str(parsed) == cmd.id

    def test_default_status_is_active(self):
        cmd = Command(name="test-cmd", prompt="test", environment=Path("/tmp"))
        assert cmd.status == CommandStatus.ACTIVE

    def test_default_namespace_is_default(self):
        cmd = Command(name="test-cmd", prompt="test", environment=Path("/tmp"))
        assert cmd.namespace == "default"

    def test_default_allowed_tools_is_empty_list(self):
        cmd = Command(name="test-cmd", prompt="test", environment=Path("/tmp"))
        assert cmd.allowed_tools == []

    def test_created_at_is_iso8601(self):
        cmd = Command(name="test-cmd", prompt="test", environment=Path("/tmp"))
        # ISO 8601 basic check: contains T separator and timezone info
        assert "T" in cmd.created_at
        assert "+" in cmd.created_at or cmd.created_at.endswith("Z") or ":" in cmd.created_at.split("T")[1]

    def test_updated_at_is_iso8601(self):
        cmd = Command(name="test-cmd", prompt="test", environment=Path("/tmp"))
        assert "T" in cmd.updated_at

    def test_secrets_none_is_valid(self):
        cmd = Command(name="test-cmd", prompt="test", environment=Path("/tmp"), secrets=None)
        assert cmd.secrets is None

    def test_environment_accepts_path(self):
        cmd = Command(name="test-cmd", prompt="test", environment=Path("/home/user/project"))
        assert isinstance(cmd.environment, Path)
        assert cmd.environment == Path("/home/user/project")
