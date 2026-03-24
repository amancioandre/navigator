"""Tests for namespace model, database CRUD, and utilities."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from navigator.db import (
    delete_namespace,
    get_all_namespaces,
    get_namespace_by_name,
    insert_command,
    insert_namespace,
)
from navigator.models import Command, Namespace


class TestNamespaceModel:
    """Tests for the Namespace Pydantic model."""

    def test_valid_name(self):
        ns = Namespace(name="myproject")
        assert ns.name == "myproject"

    def test_valid_name_with_hyphens(self):
        ns = Namespace(name="my-project-2")
        assert ns.name == "my-project-2"

    def test_invalid_uppercase_raises(self):
        with pytest.raises(ValueError, match="Invalid.*name"):
            Namespace(name="INVALID")

    def test_invalid_leading_hyphen_raises(self):
        with pytest.raises(ValueError, match="Invalid.*name"):
            Namespace(name="-bad")

    def test_empty_description_defaults_to_none(self):
        ns = Namespace(name="test")
        assert ns.description is None

    def test_description_set(self):
        ns = Namespace(name="test", description="My test namespace")
        assert ns.description == "My test namespace"

    def test_created_at_auto_set(self):
        ns = Namespace(name="test")
        assert ns.created_at is not None
        assert "T" in ns.created_at  # ISO format


class TestNamespaceDbCrud:
    """Tests for namespace database CRUD operations."""

    def test_default_namespace_auto_created(self, db_conn):
        ns = get_namespace_by_name(db_conn, "default")
        assert ns is not None
        assert ns.name == "default"
        assert ns.description == "Default namespace"

    def test_insert_namespace(self, db_conn):
        ns = Namespace(name="myproject", description="My project")
        insert_namespace(db_conn, ns)
        retrieved = get_namespace_by_name(db_conn, "myproject")
        assert retrieved is not None
        assert retrieved.name == "myproject"
        assert retrieved.description == "My project"

    def test_insert_duplicate_raises(self, db_conn):
        ns = Namespace(name="dup-ns")
        insert_namespace(db_conn, ns)
        with pytest.raises(sqlite3.IntegrityError):
            insert_namespace(db_conn, Namespace(name="dup-ns"))

    def test_get_all_namespaces(self, db_conn):
        ns1 = Namespace(name="proj-a")
        ns2 = Namespace(name="proj-b")
        insert_namespace(db_conn, ns1)
        insert_namespace(db_conn, ns2)
        result = get_all_namespaces(db_conn)
        names = [n.name for n in result]
        assert "default" in names
        assert "proj-a" in names
        assert "proj-b" in names
        assert len(result) == 3

    def test_get_namespace_by_name_nonexistent(self, db_conn):
        result = get_namespace_by_name(db_conn, "no-such-ns")
        assert result is None

    def test_delete_namespace_empty(self, db_conn):
        ns = Namespace(name="empty-ns")
        insert_namespace(db_conn, ns)
        rows = delete_namespace(db_conn, "empty-ns")
        assert rows == 1
        assert get_namespace_by_name(db_conn, "empty-ns") is None

    def test_delete_namespace_with_commands_raises(self, db_conn):
        ns = Namespace(name="has-cmds")
        insert_namespace(db_conn, ns)
        cmd = Command(
            name="my-cmd",
            prompt="test",
            environment=Path("/tmp"),
            namespace="has-cmds",
        )
        insert_command(db_conn, cmd)
        with pytest.raises(ValueError, match="commands exist"):
            delete_namespace(db_conn, "has-cmds")

    def test_delete_namespace_force_cascades(self, db_conn):
        ns = Namespace(name="force-ns")
        insert_namespace(db_conn, ns)
        cmd = Command(
            name="force-cmd",
            prompt="test",
            environment=Path("/tmp"),
            namespace="force-ns",
        )
        insert_command(db_conn, cmd)
        rows = delete_namespace(db_conn, "force-ns", force=True)
        assert rows == 1
        assert get_namespace_by_name(db_conn, "force-ns") is None
        # Command should also be deleted
        from navigator.db import get_command_by_name

        assert get_command_by_name(db_conn, "force-cmd") is None

    def test_delete_nonexistent_returns_zero(self, db_conn):
        rows = delete_namespace(db_conn, "ghost-ns")
        assert rows == 0
