"""Tests for Navigator execution engine."""

from __future__ import annotations

import os
import signal
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from navigator.config import NavigatorConfig
from navigator.executor import (
    ENV_WHITELIST,
    ExecutionResult,
    _active_processes,
    build_clean_env,
    build_command_args,
    execute_command,
)
from navigator.models import Command


def _make_config(tmp_path: Path) -> NavigatorConfig:
    """Create a NavigatorConfig with tmp_path for logs and no retries by default."""
    return NavigatorConfig(
        db_path=tmp_path / "registry.db",
        log_dir=tmp_path / "logs",
        secrets_base_path=tmp_path / "secrets",
        default_retry_count=0,
        default_timeout=300,
    )


def _make_mock_popen(returncode: int = 0, stdout: str = "", stderr: str = ""):
    """Create a mock Popen instance with communicate returning given values."""
    mock_proc = MagicMock()
    mock_proc.pid = 12345
    mock_proc.returncode = returncode
    mock_proc.communicate.return_value = (stdout, stderr)
    mock_proc.stdout = MagicMock()
    mock_proc.stdout.read.return_value = stdout
    mock_proc.stderr = MagicMock()
    mock_proc.stderr.read.return_value = stderr
    mock_proc.wait.return_value = returncode
    return mock_proc


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

    @patch("navigator.executor.write_execution_log")
    @patch("navigator.executor.subprocess.Popen")
    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    @patch("navigator.executor.os.getpgid", return_value=12345)
    def test_passes_env_and_cwd(self, mock_getpgid, mock_which, mock_popen, mock_log, tmp_path, monkeypatch):
        """execute_command passes clean env and correct cwd to Popen."""
        monkeypatch.setattr(os, "environ", {"PATH": "/usr/bin", "HOME": "/home/test"})
        mock_proc = _make_mock_popen()
        mock_popen.return_value = mock_proc
        mock_log.return_value = tmp_path / "test.log"

        config = _make_config(tmp_path)
        cmd = self._make_command(tmp_path)
        execute_command(cmd, config)

        mock_popen.assert_called_once()
        call_kwargs = mock_popen.call_args
        assert call_kwargs.kwargs["cwd"] == str(tmp_path)
        assert call_kwargs.kwargs["text"] is True
        assert call_kwargs.kwargs["start_new_session"] is True
        env = call_kwargs.kwargs["env"]
        for key in env:
            assert key in ENV_WHITELIST

    @patch("navigator.executor.shutil.which", return_value=None)
    def test_claude_not_found(self, mock_which, tmp_path):
        """Raise FileNotFoundError if claude CLI is not on PATH."""
        config = _make_config(tmp_path)
        cmd = self._make_command(tmp_path)
        with pytest.raises(FileNotFoundError, match="claude CLI not found"):
            execute_command(cmd, config)

    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    def test_cwd_not_exist(self, mock_which, tmp_path):
        """Raise FileNotFoundError if working directory does not exist."""
        config = _make_config(tmp_path)
        cmd = Command(
            name="test-cmd",
            prompt="Run tests",
            environment=Path("/tmp/definitely-nonexistent-dir-12345"),
        )
        with pytest.raises(FileNotFoundError, match="Working directory does not exist"):
            execute_command(cmd, config)

    @patch("navigator.executor.write_execution_log")
    @patch("navigator.executor.subprocess.Popen")
    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    @patch("navigator.executor.os.getpgid", return_value=12345)
    def test_secrets_not_in_args(self, mock_getpgid, mock_which, mock_popen, mock_log, tmp_path):
        """Secret values must never appear in the subprocess args list."""
        env_file = tmp_path / ".env"
        env_file.write_text("SUPER_SECRET=mysecretvalue99\n")

        mock_proc = _make_mock_popen()
        mock_popen.return_value = mock_proc
        mock_log.return_value = tmp_path / "test.log"

        config = _make_config(tmp_path)
        cmd = self._make_command(tmp_path, secrets_path=env_file, tools=["Read"])
        execute_command(cmd, config)

        call_args = mock_popen.call_args[0][0]
        for arg in call_args:
            assert "mysecretvalue99" not in arg

    @patch("navigator.executor.write_execution_log")
    @patch("navigator.executor.subprocess.Popen")
    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    @patch("navigator.executor.os.getpgid", return_value=12345)
    def test_secrets_in_env(self, mock_getpgid, mock_which, mock_popen, mock_log, tmp_path):
        """Secrets from .env file appear in the subprocess env dict."""
        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY=abc123\n")

        mock_proc = _make_mock_popen()
        mock_popen.return_value = mock_proc
        mock_log.return_value = tmp_path / "test.log"

        config = _make_config(tmp_path)
        cmd = self._make_command(tmp_path, secrets_path=env_file)
        execute_command(cmd, config)

        env = mock_popen.call_args.kwargs["env"]
        assert env["API_KEY"] == "abc123"


class TestRetry:
    """Tests for retry with exponential backoff."""

    def _make_command(self, tmp_path):
        return Command(
            name="retry-cmd",
            prompt="Run tests",
            environment=tmp_path,
        )

    @patch("navigator.executor.write_execution_log")
    @patch("navigator.executor.time.sleep")
    @patch("navigator.executor.subprocess.Popen")
    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    @patch("navigator.executor.os.getpgid", return_value=12345)
    def test_retries_on_failure(self, mock_getpgid, mock_which, mock_popen, mock_sleep, mock_log, tmp_path):
        """Retries on failure and succeeds on third attempt."""
        procs = [
            _make_mock_popen(returncode=1),
            _make_mock_popen(returncode=1),
            _make_mock_popen(returncode=0),
        ]
        mock_popen.side_effect = procs
        mock_log.return_value = tmp_path / "test.log"

        config = _make_config(tmp_path)
        cmd = self._make_command(tmp_path)
        result = execute_command(cmd, config, retries_override=2)

        assert result.returncode == 0
        assert result.attempts == 3
        assert mock_popen.call_count == 3

    @patch("navigator.executor.write_execution_log")
    @patch("navigator.executor.subprocess.Popen")
    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    @patch("navigator.executor.os.getpgid", return_value=12345)
    def test_no_retry_on_success(self, mock_getpgid, mock_which, mock_popen, mock_log, tmp_path):
        """Does not retry when first attempt succeeds."""
        mock_popen.return_value = _make_mock_popen(returncode=0)
        mock_log.return_value = tmp_path / "test.log"

        config = _make_config(tmp_path)
        cmd = self._make_command(tmp_path)
        result = execute_command(cmd, config, retries_override=3)

        assert result.returncode == 0
        assert result.attempts == 1
        assert mock_popen.call_count == 1

    @patch("navigator.executor.write_execution_log")
    @patch("navigator.executor.time.sleep")
    @patch("navigator.executor.subprocess.Popen")
    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    @patch("navigator.executor.os.getpgid", return_value=12345)
    def test_max_retries_exhausted(self, mock_getpgid, mock_which, mock_popen, mock_sleep, mock_log, tmp_path):
        """Returns failure after all retries exhausted."""
        mock_popen.return_value = _make_mock_popen(returncode=1)
        mock_log.return_value = tmp_path / "test.log"

        config = _make_config(tmp_path)
        cmd = self._make_command(tmp_path)
        result = execute_command(cmd, config, retries_override=2)

        assert result.returncode == 1
        assert result.attempts == 3  # 1 initial + 2 retries
        assert mock_popen.call_count == 3

    @patch("navigator.executor.write_execution_log")
    @patch("navigator.executor.time.sleep")
    @patch("navigator.executor.subprocess.Popen")
    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    @patch("navigator.executor.os.getpgid", return_value=12345)
    def test_exponential_backoff_delays(self, mock_getpgid, mock_which, mock_popen, mock_sleep, mock_log, tmp_path):
        """Retry delays follow 2^attempt pattern."""
        mock_popen.return_value = _make_mock_popen(returncode=1)
        mock_log.return_value = tmp_path / "test.log"

        config = _make_config(tmp_path)
        cmd = self._make_command(tmp_path)
        execute_command(cmd, config, retries_override=2)

        # attempt 1 (index 1): delay = 2^1 = 2
        # attempt 2 (index 2): delay = 2^2 = 4
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0][0][0] == 2
        assert mock_sleep.call_args_list[1][0][0] == 4

    @patch("navigator.executor.write_execution_log")
    @patch("navigator.executor.time.sleep")
    @patch("navigator.executor.subprocess.Popen")
    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    @patch("navigator.executor.os.getpgid", return_value=12345)
    def test_retries_override(self, mock_getpgid, mock_which, mock_popen, mock_sleep, mock_log, tmp_path):
        """retries_override=1 allows max 2 attempts."""
        mock_popen.return_value = _make_mock_popen(returncode=1)
        mock_log.return_value = tmp_path / "test.log"

        config = _make_config(tmp_path)
        cmd = self._make_command(tmp_path)
        result = execute_command(cmd, config, retries_override=1)

        assert result.attempts == 2
        assert mock_popen.call_count == 2


class TestTimeout:
    """Tests for timeout enforcement with SIGTERM/SIGKILL escalation."""

    def _make_command(self, tmp_path):
        return Command(
            name="timeout-cmd",
            prompt="Run tests",
            environment=tmp_path,
        )

    @patch("navigator.executor.write_execution_log")
    @patch("navigator.executor.subprocess.Popen")
    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    @patch("navigator.executor.os.getpgid", return_value=12345)
    def test_timeout_returns_124(self, mock_getpgid, mock_which, mock_popen, mock_log, tmp_path):
        """Timeout produces exit code 124."""
        mock_proc = _make_mock_popen()
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=10)
        mock_proc.wait.return_value = None
        mock_popen.return_value = mock_proc
        mock_log.return_value = tmp_path / "test.log"

        config = _make_config(tmp_path)
        cmd = self._make_command(tmp_path)

        with patch("navigator.executor.os.killpg"):
            result = execute_command(cmd, config, timeout_override=10)

        assert result.returncode == 124
        assert result.timed_out is True

    @patch("navigator.executor.write_execution_log")
    @patch("navigator.executor.os.killpg")
    @patch("navigator.executor.subprocess.Popen")
    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    @patch("navigator.executor.os.getpgid", return_value=99999)
    def test_timeout_kills_process_group(self, mock_getpgid, mock_which, mock_popen, mock_killpg, mock_log, tmp_path):
        """Timeout sends SIGTERM then SIGKILL to process group."""
        mock_proc = _make_mock_popen()
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=10)
        # First wait (5s grace) times out, forcing SIGKILL
        mock_proc.wait.side_effect = [subprocess.TimeoutExpired(cmd="test", timeout=5), None]
        mock_popen.return_value = mock_proc
        mock_log.return_value = tmp_path / "test.log"

        config = _make_config(tmp_path)
        cmd = self._make_command(tmp_path)
        execute_command(cmd, config, timeout_override=10)

        # Should have called killpg with SIGTERM first, then SIGKILL
        killpg_calls = mock_killpg.call_args_list
        assert len(killpg_calls) == 2
        assert killpg_calls[0][0] == (99999, signal.SIGTERM)
        assert killpg_calls[1][0] == (99999, signal.SIGKILL)

    @patch("navigator.executor.write_execution_log")
    @patch("navigator.executor.subprocess.Popen")
    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    @patch("navigator.executor.os.getpgid", return_value=12345)
    def test_timeout_override(self, mock_getpgid, mock_which, mock_popen, mock_log, tmp_path):
        """timeout_override is passed to communicate."""
        mock_proc = _make_mock_popen(returncode=0)
        mock_popen.return_value = mock_proc
        mock_log.return_value = tmp_path / "test.log"

        config = _make_config(tmp_path)
        cmd = self._make_command(tmp_path)
        execute_command(cmd, config, timeout_override=60)

        mock_proc.communicate.assert_called_once_with(timeout=60)


class TestProcessGroups:
    """Tests for process group isolation."""

    def _make_command(self, tmp_path):
        return Command(
            name="pg-cmd",
            prompt="Run tests",
            environment=tmp_path,
        )

    @patch("navigator.executor.write_execution_log")
    @patch("navigator.executor.subprocess.Popen")
    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    @patch("navigator.executor.os.getpgid", return_value=12345)
    def test_start_new_session(self, mock_getpgid, mock_which, mock_popen, mock_log, tmp_path):
        """Popen is called with start_new_session=True."""
        mock_popen.return_value = _make_mock_popen(returncode=0)
        mock_log.return_value = tmp_path / "test.log"

        config = _make_config(tmp_path)
        cmd = self._make_command(tmp_path)
        execute_command(cmd, config)

        assert mock_popen.call_args.kwargs["start_new_session"] is True

    @patch("navigator.executor.write_execution_log")
    @patch("navigator.executor.subprocess.Popen")
    @patch("navigator.executor.shutil.which", return_value="/usr/bin/claude")
    @patch("navigator.executor.os.getpgid", return_value=12345)
    def test_pid_tracked(self, mock_getpgid, mock_which, mock_popen, mock_log, tmp_path):
        """PID is added to _active_processes during execution and removed after."""
        mock_proc = _make_mock_popen(returncode=0)
        mock_proc.pid = 54321
        mock_popen.return_value = mock_proc
        mock_log.return_value = tmp_path / "test.log"

        config = _make_config(tmp_path)
        cmd = self._make_command(tmp_path)
        execute_command(cmd, config)

        # PID should be removed after execution completes
        assert 54321 not in _active_processes
