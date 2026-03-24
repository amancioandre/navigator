"""Tests for Navigator SQLite database layer — CRUD, WAL mode, and data integrity."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import pytest

from navigator.db import (
    delete_command,
    get_all_commands,
    get_command_by_name,
    get_connection,
    init_db,
    insert_command,
    update_command,
)
from navigator.models import Command


class TestGetConnection:
    """Tests for database connection setup."""

    def test_wal_mode_enabled(self, db_conn):
        result = db_conn.execute("PRAGMA journal_mode").fetchone()
        assert result[0] == "wal"

    def test_creates_parent_directories(self, tmp_path):
        nested = tmp_path / "deep" / "nested" / "dir" / "test.db"
        conn = get_connection(nested)
        assert nested.parent.exists()
        conn.close()


class TestInitDb:
    """Tests for database initialization."""

    def test_creates_commands_table(self, db_conn):
        result = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='commands'"
        ).fetchone()
        assert result is not None


class TestInsertCommand:
    """Tests for inserting commands."""

    def test_insert_and_retrieve(self, db_conn, sample_command):
        insert_command(db_conn, sample_command)
        retrieved = get_command_by_name(db_conn, "test-cmd")
        assert retrieved is not None
        assert retrieved.name == sample_command.name
        assert retrieved.prompt == sample_command.prompt
        assert retrieved.environment == sample_command.environment

    def test_insert_duplicate_name_raises(self, db_conn, sample_command):
        insert_command(db_conn, sample_command)
        dup = Command(name="test-cmd", prompt="other", environment=Path("/tmp"))
        with pytest.raises(sqlite3.IntegrityError):
            insert_command(db_conn, dup)


class TestGetCommandByName:
    """Tests for retrieving commands by name."""

    def test_nonexistent_returns_none(self, db_conn):
        result = get_command_by_name(db_conn, "no-such-command")
        assert result is None


class TestGetAllCommands:
    """Tests for listing commands."""

    def test_empty_returns_empty_list(self, db_conn):
        result = get_all_commands(db_conn)
        assert result == []

    def test_returns_all_inserted(self, db_conn):
        cmd1 = Command(name="cmd-a", prompt="test1", environment=Path("/tmp"))
        cmd2 = Command(name="cmd-b", prompt="test2", environment=Path("/tmp"))
        insert_command(db_conn, cmd1)
        insert_command(db_conn, cmd2)
        result = get_all_commands(db_conn)
        assert len(result) == 2

    def test_namespace_filter(self, db_conn):
        cmd1 = Command(name="cmd-a", prompt="test1", environment=Path("/tmp"), namespace="proj1")
        cmd2 = Command(name="cmd-b", prompt="test2", environment=Path("/tmp"), namespace="proj2")
        insert_command(db_conn, cmd1)
        insert_command(db_conn, cmd2)
        result = get_all_commands(db_conn, namespace="proj1")
        assert len(result) == 1
        assert result[0].name == "cmd-a"

    def test_sort_by_created(self, db_conn):
        cmd1 = Command(
            name="cmd-old",
            prompt="test1",
            environment=Path("/tmp"),
            created_at="2024-01-01T00:00:00+00:00",
        )
        cmd2 = Command(
            name="cmd-new",
            prompt="test2",
            environment=Path("/tmp"),
            created_at="2025-06-01T00:00:00+00:00",
        )
        insert_command(db_conn, cmd1)
        insert_command(db_conn, cmd2)
        result = get_all_commands(db_conn, sort_by_created=True)
        assert result[0].name == "cmd-new"
        assert result[1].name == "cmd-old"


class TestUpdateCommand:
    """Tests for updating commands."""

    def test_update_changes_fields(self, db_conn, sample_command):
        insert_command(db_conn, sample_command)
        original = get_command_by_name(db_conn, "test-cmd")
        time.sleep(0.01)  # Ensure updated_at differs
        rows = update_command(db_conn, "test-cmd", prompt="updated prompt")
        assert rows == 1
        updated = get_command_by_name(db_conn, "test-cmd")
        assert updated.prompt == "updated prompt"
        assert updated.updated_at >= original.updated_at

    def test_update_nonexistent_returns_zero(self, db_conn):
        rows = update_command(db_conn, "ghost", prompt="nope")
        assert rows == 0


class TestDeleteCommand:
    """Tests for deleting commands."""

    def test_delete_removes_command(self, db_conn, sample_command):
        insert_command(db_conn, sample_command)
        rows = delete_command(db_conn, "test-cmd")
        assert rows == 1
        assert get_command_by_name(db_conn, "test-cmd") is None

    def test_delete_nonexistent_returns_zero(self, db_conn):
        rows = delete_command(db_conn, "ghost")
        assert rows == 0


class TestPersistence:
    """Tests for data persistence across connections."""

    def test_data_persists_after_close_reopen(self, tmp_path):
        db_path = tmp_path / "persist_test.db"
        conn1 = get_connection(db_path)
        init_db(conn1)
        cmd = Command(name="persist-cmd", prompt="test", environment=Path("/tmp"))
        insert_command(conn1, cmd)
        conn1.close()

        conn2 = get_connection(db_path)
        init_db(conn2)
        retrieved = get_command_by_name(conn2, "persist-cmd")
        assert retrieved is not None
        assert retrieved.name == "persist-cmd"
        conn2.close()


class TestTransactionSafety:
    """Tests for transaction rollback behavior."""

    def test_rollback_on_duplicate_insert(self, db_conn):
        cmd1 = Command(name="unique-cmd", prompt="test", environment=Path("/tmp"))
        insert_command(db_conn, cmd1)
        dup = Command(name="unique-cmd", prompt="other", environment=Path("/tmp"))
        with pytest.raises(sqlite3.IntegrityError):
            insert_command(db_conn, dup)
        # Original should still be intact
        result = get_command_by_name(db_conn, "unique-cmd")
        assert result is not None
        assert result.prompt == "test"


class TestAllowedToolsRoundTrip:
    """Tests for JSON serialization of allowed_tools."""

    def test_allowed_tools_round_trip(self, db_conn):
        tools = ["Bash", "Read", "Write"]
        cmd = Command(
            name="tools-cmd",
            prompt="test",
            environment=Path("/tmp"),
            allowed_tools=tools,
        )
        insert_command(db_conn, cmd)
        retrieved = get_command_by_name(db_conn, "tools-cmd")
        assert retrieved.allowed_tools == tools
