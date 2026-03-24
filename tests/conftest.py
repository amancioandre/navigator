"""Shared test fixtures for Navigator test suite."""

from __future__ import annotations

import pytest
import typer.testing

from navigator.cli import app as navigator_app


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
