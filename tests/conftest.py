"""Shared test fixtures for Navigator test suite."""

from __future__ import annotations

from pathlib import Path

import pytest
import typer.testing

from navigator.cli import app as navigator_app


@pytest.fixture(autouse=True)
def _reset_output_format():
    """Reset the global output_format after each test to prevent state leakage."""
    import navigator.output as nav_output

    nav_output.output_format = "text"
    yield
    nav_output.output_format = "text"


@pytest.fixture()
def cli_runner() -> typer.testing.CliRunner:
    """Return a Typer CLI test runner."""
    return typer.testing.CliRunner()


@pytest.fixture()
def app() -> typer.Typer:
    """Return the Navigator Typer app."""
    return navigator_app


@pytest.fixture()
def tmp_config_dir(tmp_path, monkeypatch):
    """Create isolated config and data directories for testing.

    Monkeypatches navigator.config path functions to use temp directories,
    ensuring tests never touch the real ~/.config/navigator/.
    """
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"

    monkeypatch.setattr("navigator.config.get_config_dir", lambda: config_dir)
    monkeypatch.setattr("navigator.config.get_data_dir", lambda: data_dir)

    return {"config_dir": config_dir, "data_dir": data_dir}


@pytest.fixture()
def db_conn(tmp_path):
    """In-memory-like SQLite connection using temp file."""
    from navigator.db import get_connection, init_db

    db_path = tmp_path / "test_registry.db"
    conn = get_connection(db_path)
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture()
def sample_command():
    """A valid Command instance for testing."""
    from navigator.models import Command

    return Command(
        name="test-cmd",
        prompt="Run tests",
        environment=Path("/tmp/test-project"),
    )
