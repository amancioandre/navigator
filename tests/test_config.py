"""Tests for Navigator config module — creation, loading, path resolution."""

from __future__ import annotations

from pathlib import Path

import tomllib

from navigator.config import (
    NavigatorConfig,
    get_config_dir,
    get_data_dir,
    load_config,
    resolve_path,
)


def test_first_run_creates_config(tmp_config_dir):
    """First invocation creates config.toml with defaults."""
    config_path = tmp_config_dir["config_dir"] / "config.toml"
    assert not config_path.exists()

    config = load_config()

    assert config_path.exists()
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    assert "db_path" in data
    assert "log_dir" in data
    assert "secrets_base_path" in data
    assert data["default_retry_count"] == 3
    assert data["default_timeout"] == 300


def test_load_existing_config(tmp_config_dir):
    """Existing config.toml is loaded with custom values."""
    import tomli_w

    config_dir = tmp_config_dir["config_dir"]
    config_dir.mkdir(exist_ok=True)
    config_path = config_dir / "config.toml"
    custom_data = {
        "db_path": "/tmp/custom.db",
        "log_dir": "/tmp/custom_logs",
        "secrets_base_path": "/tmp/custom_secrets",
        "default_retry_count": 5,
        "default_timeout": 600,
    }
    with open(config_path, "wb") as f:
        tomli_w.dump(custom_data, f)

    config = load_config()
    assert config.default_timeout == 600
    assert config.default_retry_count == 5


def test_paths_are_absolute(tmp_config_dir):
    """All path fields in config are resolved to absolute paths."""
    config = load_config()
    assert config.db_path.is_absolute()
    assert config.log_dir.is_absolute()
    assert config.secrets_base_path.is_absolute()


def test_resolve_path_tilde():
    """resolve_path expands ~ to home directory."""
    result = resolve_path("~/foo")
    assert result.is_absolute()
    assert str(result).startswith(str(Path.home()))


def test_resolve_path_relative():
    """resolve_path converts relative paths to absolute."""
    result = resolve_path("relative/path")
    assert result.is_absolute()


def test_resolve_path_absolute():
    """resolve_path preserves already-absolute paths."""
    result = resolve_path("/absolute/path")
    assert result == Path("/absolute/path")


def test_config_defaults():
    """NavigatorConfig has correct default values."""
    config = NavigatorConfig()
    assert config.default_retry_count == 3
    assert config.default_timeout == 300


def test_config_dir_created(tmp_config_dir):
    """load_config creates parent directories if they don't exist."""
    import shutil

    config_dir = tmp_config_dir["config_dir"]
    # Remove config dir to verify it gets created
    shutil.rmtree(config_dir, ignore_errors=True)
    assert not config_dir.exists()

    load_config()
    assert config_dir.exists()
