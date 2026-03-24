"""Tests for Navigator watcher model, DB CRUD, and WatcherManager."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from navigator.db import (
    delete_command,
    delete_watcher,
    delete_watchers_for_command,
    get_active_watchers,
    get_connection,
    get_watcher_by_id,
    get_watchers_for_command,
    init_db,
    insert_command,
    insert_watcher,
)
from navigator.models import Command, Watcher, WatcherStatus


@pytest.fixture()
def sample_watcher(sample_command):
    """A valid Watcher instance for testing."""
    return Watcher(
        command_name=sample_command.name,
        watch_path=Path("/tmp/watched"),
    )


class TestWatcherModel:
    """Tests for the Watcher Pydantic model."""

    def test_defaults(self):
        w = Watcher(command_name="test-cmd", watch_path=Path("/tmp"))
        assert w.id  # UUID generated
        assert w.debounce_ms == 500
        assert w.status == WatcherStatus.ACTIVE
        assert w.patterns == ["*"]
        assert ".git/**" in w.ignore_patterns
        assert "*.swp" in w.ignore_patterns
        assert w.recursive is True
        assert w.active_hours is None

    def test_debounce_ms_must_be_positive(self):
        with pytest.raises(ValueError, match="greater than 0"):
            Watcher(command_name="test-cmd", watch_path=Path("/tmp"), debounce_ms=0)

    def test_debounce_ms_negative_rejected(self):
        with pytest.raises(ValueError, match="greater than 0"):
            Watcher(command_name="test-cmd", watch_path=Path("/tmp"), debounce_ms=-1)

    def test_active_hours_valid(self):
        w = Watcher(
            command_name="test-cmd",
            watch_path=Path("/tmp"),
            active_hours="09:00-17:00",
        )
        assert w.active_hours == "09:00-17:00"

    def test_active_hours_overnight_valid(self):
        w = Watcher(
            command_name="test-cmd",
            watch_path=Path("/tmp"),
            active_hours="22:00-06:00",
        )
        assert w.active_hours == "22:00-06:00"

    def test_active_hours_invalid_format(self):
        with pytest.raises(ValueError, match="HH:MM-HH:MM"):
            Watcher(
                command_name="test-cmd",
                watch_path=Path("/tmp"),
                active_hours="bad-format",
            )

    def test_active_hours_invalid_time(self):
        with pytest.raises(ValueError):
            Watcher(
                command_name="test-cmd",
                watch_path=Path("/tmp"),
                active_hours="25:00-17:00",
            )


class TestWatcherStatusEnum:
    """Tests for WatcherStatus enum."""

    def test_active_value(self):
        assert WatcherStatus.ACTIVE == "active"

    def test_paused_value(self):
        assert WatcherStatus.PAUSED == "paused"


class TestWatcherDbSchema:
    """Tests for watchers table creation."""

    def test_creates_watchers_table(self, db_conn):
        result = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='watchers'"
        ).fetchone()
        assert result is not None


class TestInsertWatcher:
    """Tests for inserting and retrieving watchers."""

    def test_insert_and_retrieve(self, db_conn, sample_command, sample_watcher):
        insert_command(db_conn, sample_command)
        insert_watcher(db_conn, sample_watcher)
        retrieved = get_watcher_by_id(db_conn, sample_watcher.id)
        assert retrieved is not None
        assert retrieved.command_name == sample_watcher.command_name
        assert retrieved.watch_path == sample_watcher.watch_path
        assert retrieved.debounce_ms == 500


class TestGetWatchersForCommand:
    """Tests for retrieving watchers by command name."""

    def test_returns_watchers_for_command(self, db_conn, sample_command):
        insert_command(db_conn, sample_command)
        w1 = Watcher(command_name=sample_command.name, watch_path=Path("/tmp/a"))
        w2 = Watcher(command_name=sample_command.name, watch_path=Path("/tmp/b"))
        insert_watcher(db_conn, w1)
        insert_watcher(db_conn, w2)
        result = get_watchers_for_command(db_conn, sample_command.name)
        assert len(result) == 2

    def test_returns_empty_for_unknown(self, db_conn):
        result = get_watchers_for_command(db_conn, "nonexistent")
        assert result == []


class TestGetActiveWatchers:
    """Tests for retrieving only active watchers."""

    def test_returns_only_active(self, db_conn, sample_command):
        insert_command(db_conn, sample_command)
        w1 = Watcher(command_name=sample_command.name, watch_path=Path("/tmp/a"))
        w2 = Watcher(
            command_name=sample_command.name,
            watch_path=Path("/tmp/b"),
            status=WatcherStatus.PAUSED,
        )
        insert_watcher(db_conn, w1)
        insert_watcher(db_conn, w2)
        result = get_active_watchers(db_conn)
        assert len(result) == 1
        assert result[0].status == WatcherStatus.ACTIVE


class TestDeleteWatcher:
    """Tests for deleting watchers."""

    def test_delete_removes_watcher(self, db_conn, sample_command, sample_watcher):
        insert_command(db_conn, sample_command)
        insert_watcher(db_conn, sample_watcher)
        rows = delete_watcher(db_conn, sample_watcher.id)
        assert rows == 1
        assert get_watcher_by_id(db_conn, sample_watcher.id) is None

    def test_delete_nonexistent_returns_zero(self, db_conn):
        rows = delete_watcher(db_conn, "nonexistent-id")
        assert rows == 0


class TestDeleteWatchersForCommand:
    """Tests for deleting all watchers for a command."""

    def test_deletes_all_for_command(self, db_conn, sample_command):
        insert_command(db_conn, sample_command)
        w1 = Watcher(command_name=sample_command.name, watch_path=Path("/tmp/a"))
        w2 = Watcher(command_name=sample_command.name, watch_path=Path("/tmp/b"))
        insert_watcher(db_conn, w1)
        insert_watcher(db_conn, w2)
        count = delete_watchers_for_command(db_conn, sample_command.name)
        assert count == 2
        assert get_watchers_for_command(db_conn, sample_command.name) == []


class TestForeignKeyCascade:
    """Tests for FK CASCADE deleting watchers when command is deleted."""

    def test_cascade_delete(self, db_conn, sample_command, sample_watcher):
        insert_command(db_conn, sample_command)
        insert_watcher(db_conn, sample_watcher)
        # Delete the command -- watcher should cascade-delete
        delete_command(db_conn, sample_command.name)
        assert get_watcher_by_id(db_conn, sample_watcher.id) is None
