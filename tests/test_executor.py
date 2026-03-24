"""Tests for Navigator execution engine."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from navigator.executor import (
    ENV_WHITELIST,
    build_clean_env,
    build_command_args,
    execute_command,
)
from navigator.models import Command


class TestBuildCleanEnv:
    """Tests for environment construction from whitelist."""

    def test_whitelist_only(self, monkeypatch):
        """build_clean_env returns only whitelisted vars from os.environ."""
        monkeypatch.setattr(
            os,
            "environ",
            {
                "PATH": "/usr/bin",
                "HOME": "/home/test",
                "LANG": "en_US.UTF-8",
                "TERM": "xterm",
                "SHELL": "/bin/bash",
                "SECRET_THING": "should-not-appear",
                "AWS_KEY": "also-excluded",
            },
        )
        result = build_clean_env()
        assert set(result.keys()) == {"PATH", "HOME", "LANG", "TERM", "SHELL"}
        assert "SECRET_THING" not in result
        assert "AWS_KEY" not in result

    def test_with_secrets(self, monkeypatch):
        """build_clean_env merges secrets into the environment."""
        monkeypatch.setattr(os, "environ", {"PATH": "/usr/bin", "HOME": "/home/test"})
        result = build_clean_env({"API_KEY": "val123", "DB_HOST": "localhost"})
        assert result["API_KEY"] == "val123"
        assert result["DB_HOST"] == "localhost"
        assert result["PATH"] == "/usr/bin"

    def test_skips_missing_vars(self, monkeypatch):
        """build_clean_env skips whitelist vars not present in os.environ."""
        monkeypatch.setattr(os, "environ", {"PATH": "/usr/bin"})
        result = build_clean_env()
        assert "PATH" in result
        assert "LANG" not in result
        assert "TERM" not in result

    def test_empty_secrets_same_as_no_secrets(self, monkeypatch):
        """Passing empty dict is equivalent to passing None."""
        monkeypatch.setattr(os, "environ", {"PATH": "/usr/bin", "HOME": "/home/test"})
        result_none = build_clean_env(None)
        result_empty = build_clean_env({})
        assert result_none == result_empty


class TestBuildCommandArgs:
    """Tests for claude CLI argument assembly."""

    def test_with_tools(self):
        """build_command_args includes --allowedTools for each tool."""
        result = build_command_args("do thing", ["Read", "Bash"])
        assert result == [
            "claude",
            "-p",
            "do thing",
            "--print",
            "--allowedTools",
            "Read",
            "--allowedTools",
            "Bash",
        ]

    def test_no_tools(self):
        """build_command_args without tools has no --allowedTools flags."""
        result = build_command_args("do thing", [])
        assert result == ["claude", "-p", "do thing", "--print"]

    def test_no_dangerously_skip_permissions(self):
        """--dangerously-skip-permissions never appears in args."""
        result = build_command_args("anything", ["Read", "Write", "Bash"])
        assert "--dangerously-skip-permissions" not in result


class TestExecuteCommand:
    """Tests for the full execution flow."""

    def _make_command(self, tmp_path, secrets_path=None, tools=None):
        """Helper to create a Command with a real tmp_path environment."""
        return Command(
            name="test-cmd",
            prompt="Run tests",
            environment=tmp_path,
            secrets=secrets_path,
            allowed_tools=tools or [],
        )

    @patch("navigator.executor.subprocess.run")
    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    def test_passes_env_and_cwd(self, mock_which, mock_run, tmp_path, monkeypatch):
        """execute_command passes clean env and correct cwd to subprocess.run."""
        monkeypatch.setattr(os, "environ", {"PATH": "/usr/bin", "HOME": "/home/test"})
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        cmd = self._make_command(tmp_path)
        execute_command(cmd)

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        assert call_kwargs.kwargs["cwd"] == str(tmp_path)
        assert call_kwargs.kwargs["capture_output"] is True
        assert call_kwargs.kwargs["text"] is True
        # env should only have whitelisted keys (no secrets for this command)
        env = call_kwargs.kwargs["env"]
        for key in env:
            assert key in ENV_WHITELIST

    @patch("navigator.executor.shutil.which", return_value=None)
    def test_claude_not_found(self, mock_which, tmp_path):
        """Raise FileNotFoundError if claude CLI is not on PATH."""
        cmd = self._make_command(tmp_path)
        try:
            execute_command(cmd)
            pytest.fail("Should have raised FileNotFoundError")
        except FileNotFoundError as exc:
            assert "claude CLI not found" in str(exc)

    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    def test_cwd_not_exist(self, mock_which):
        """Raise FileNotFoundError if working directory does not exist."""
        cmd = Command(
            name="test-cmd",
            prompt="Run tests",
            environment=Path("/tmp/definitely-nonexistent-dir-12345"),
        )
        try:
            execute_command(cmd)
            pytest.fail("Should have raised FileNotFoundError")
        except FileNotFoundError as exc:
            assert "Working directory does not exist" in str(exc)

    @patch("navigator.executor.subprocess.run")
    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    def test_secrets_not_in_args(self, mock_which, mock_run, tmp_path):
        """Secret values must never appear in the subprocess args list."""
        env_file = tmp_path / ".env"
        env_file.write_text("SUPER_SECRET=mysecretvalue99\n")

        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        cmd = self._make_command(tmp_path, secrets_path=env_file, tools=["Read"])
        execute_command(cmd)

        call_args = mock_run.call_args[0][0]
        for arg in call_args:
            assert "mysecretvalue99" not in arg

    @patch("navigator.executor.subprocess.run")
    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    def test_secrets_in_env(self, mock_which, mock_run, tmp_path):
        """Secrets from .env file appear in the subprocess env dict."""
        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY=abc123\n")

        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        cmd = self._make_command(tmp_path, secrets_path=env_file)
        execute_command(cmd)

        env = mock_run.call_args.kwargs["env"]
        assert env["API_KEY"] == "abc123"
