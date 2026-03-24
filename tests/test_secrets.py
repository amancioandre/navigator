"""Tests for Navigator secret loading module."""

from __future__ import annotations

import logging
import os

from navigator.secrets import load_secrets


class TestLoadSecretsNoneAndMissing:
    """Tests for None path and missing file edge cases."""

    def test_load_secrets_none_returns_empty(self):
        """load_secrets(None) returns empty dict."""
        result = load_secrets(None)
        assert result == {}

    def test_load_secrets_nonexistent_returns_empty(self, tmp_path):
        """load_secrets with nonexistent path returns empty dict."""
        result = load_secrets(tmp_path / "nonexistent.env")
        assert result == {}

    def test_load_secrets_nonexistent_logs_warning(self, tmp_path, caplog):
        """load_secrets with nonexistent path logs a warning."""
        missing = tmp_path / "nonexistent.env"
        with caplog.at_level(logging.WARNING, logger="navigator.secrets"):
            load_secrets(missing)
        assert "Secrets file not found" in caplog.text
        assert str(missing) in caplog.text

    def test_load_secrets_directory_returns_empty(self, tmp_path):
        """load_secrets with a directory path returns empty dict."""
        result = load_secrets(tmp_path)
        assert result == {}

    def test_load_secrets_directory_logs_warning(self, tmp_path, caplog):
        """load_secrets with a directory path logs warning about not a file."""
        with caplog.at_level(logging.WARNING, logger="navigator.secrets"):
            load_secrets(tmp_path)
        assert "not a file" in caplog.text


class TestLoadSecretsValid:
    """Tests for valid .env file loading."""

    def test_load_secrets_basic(self, tmp_path):
        """load_secrets returns key-value pairs from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY=secret123\nDB_HOST=localhost\n")
        result = load_secrets(env_file)
        assert result == {"API_KEY": "secret123", "DB_HOST": "localhost"}

    def test_load_secrets_filters_none_values(self, tmp_path):
        """load_secrets filters out keys with no value (dotenv returns None)."""
        env_file = tmp_path / ".env"
        # A key alone on a line (no =) produces None in dotenv_values
        env_file.write_text("VALID_KEY=value\nVALUELESS_KEY\n")
        result = load_secrets(env_file)
        assert "VALID_KEY" in result
        assert "VALUELESS_KEY" not in result

    def test_load_secrets_comments_and_quotes(self, tmp_path):
        """load_secrets handles comments and quoted values."""
        env_file = tmp_path / ".env"
        env_file.write_text('# this is a comment\nQUOTED="hello world"\n')
        result = load_secrets(env_file)
        assert result == {"QUOTED": "hello world"}


class TestLoadSecretsLogging:
    """Tests for secret-safe logging behavior."""

    def test_log_contains_key_names(self, tmp_path, caplog):
        """Log output includes secret key names."""
        env_file = tmp_path / ".env"
        env_file.write_text("MY_SECRET=supersecretvalue\n")
        with caplog.at_level(logging.INFO, logger="navigator.secrets"):
            load_secrets(env_file)
        assert "MY_SECRET" in caplog.text

    def test_log_never_contains_secret_values(self, tmp_path, caplog):
        """Log output must NEVER contain actual secret values."""
        env_file = tmp_path / ".env"
        env_file.write_text("MY_SECRET=supersecretvalue42\n")
        with caplog.at_level(logging.DEBUG, logger="navigator.secrets"):
            load_secrets(env_file)
        assert "supersecretvalue42" not in caplog.text


class TestLoadSecretsPermissions:
    """Tests for file permission warnings."""

    def test_permissions_warning_group_readable(self, tmp_path, caplog):
        """Warn when secrets file is readable by group/others."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=value\n")
        os.chmod(env_file, 0o644)
        with caplog.at_level(logging.WARNING, logger="navigator.secrets"):
            load_secrets(env_file)
        assert "readable by group/others" in caplog.text

    def test_no_permissions_warning_owner_only(self, tmp_path, caplog):
        """No warning when secrets file has owner-only permissions."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=value\n")
        os.chmod(env_file, 0o600)
        with caplog.at_level(logging.WARNING, logger="navigator.secrets"):
            load_secrets(env_file)
        assert "readable by group/others" not in caplog.text
