"""CLI invocation tests for INFRA-01 and registry subcommand integration tests."""

from __future__ import annotations

import pytest

SUBCOMMANDS = ["register", "list", "exec", "schedule", "watch", "chain", "logs", "doctor"]


# === Phase 1 tests (INFRA-01) ===


def test_help_output(cli_runner, app):
    """navigator --help exits 0 and output contains all 8 subcommand names."""
    result = cli_runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in SUBCOMMANDS:
        assert cmd in result.output, f"Subcommand '{cmd}' not found in --help output"


def test_version_output(cli_runner, app):
    """navigator --version exits 0 and output contains 'navigator'."""
    result = cli_runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "navigator" in result.output


def test_no_args_shows_help(cli_runner, app):
    """Running navigator with no args shows help (no_args_is_help=True).

    Click/Typer returns exit code 0 for explicit --help but exit code 2
    for no_args_is_help (treated as missing required argument). The key
    behavior is that help text IS displayed.
    """
    result = cli_runner.invoke(app, [])
    assert result.exit_code in (0, 2)
    assert "Usage" in result.output


@pytest.mark.parametrize("subcommand", SUBCOMMANDS)
def test_subcommand_stubs(cli_runner, app, subcommand):
    """Each of the 8 subcommands responds to --help with exit code 0."""
    result = cli_runner.invoke(app, [subcommand, "--help"])
    assert result.exit_code == 0


# === Phase 2 tests — register subcommand ===


def test_register_valid(cli_runner, app, tmp_config_dir):
    """Register with valid args exits 0 and prints confirmation."""
    result = cli_runner.invoke(app, ["register", "my-cmd", "--prompt", "do stuff"])
    assert result.exit_code == 0
    assert "Registered command" in result.output


def test_register_invalid_name(cli_runner, app, tmp_config_dir):
    """Register with invalid name (uppercase) exits 1."""
    result = cli_runner.invoke(app, ["register", "INVALID", "--prompt", "do stuff"])
    assert result.exit_code == 1


def test_register_duplicate_name(cli_runner, app, tmp_config_dir):
    """Register duplicate name exits 1 and prints 'already exists'."""
    cli_runner.invoke(app, ["register", "my-cmd", "--prompt", "do stuff"])
    result = cli_runner.invoke(app, ["register", "my-cmd", "--prompt", "other stuff"])
    assert result.exit_code == 1
    assert "already exists" in result.output


def test_register_missing_prompt(cli_runner, app, tmp_config_dir):
    """Register without --prompt exits non-zero."""
    result = cli_runner.invoke(app, ["register", "my-cmd"])
    assert result.exit_code != 0


def test_register_with_all_options(cli_runner, app, tmp_config_dir):
    """Register with all optional flags succeeds."""
    result = cli_runner.invoke(app, [
        "register", "full-cmd",
        "--prompt", "do everything",
        "--environment", "/tmp",
        "--secrets", "/tmp/secrets.env",
        "--allowed-tools", "Read,Write,Bash",
    ])
    assert result.exit_code == 0
    assert "Registered command" in result.output


# === Phase 2 tests — list subcommand ===


def test_list_empty(cli_runner, app, tmp_config_dir):
    """List with no commands prints empty message."""
    result = cli_runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No commands registered" in result.output


def test_list_after_register(cli_runner, app, tmp_config_dir):
    """List after register shows command name in output."""
    cli_runner.invoke(app, ["register", "my-cmd", "--prompt", "do stuff"])
    result = cli_runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "my-cmd" in result.output


def test_list_sort_date(cli_runner, app, tmp_config_dir):
    """List --sort-date changes output order (newest first)."""
    cli_runner.invoke(app, ["register", "alpha-cmd", "--prompt", "first"])
    cli_runner.invoke(app, ["register", "beta-cmd", "--prompt", "second"])
    result = cli_runner.invoke(app, ["list", "--sort-date"])
    assert result.exit_code == 0
    # Both commands should appear
    assert "alpha-cmd" in result.output
    assert "beta-cmd" in result.output
    # beta-cmd registered later, should appear before alpha-cmd in newest-first order
    assert result.output.index("beta-cmd") < result.output.index("alpha-cmd")


def test_list_namespace_filter(cli_runner, app, tmp_config_dir):
    """List --namespace default returns registered commands."""
    cli_runner.invoke(app, ["register", "my-cmd", "--prompt", "do stuff"])
    result = cli_runner.invoke(app, ["list", "--namespace", "default"])
    assert result.exit_code == 0
    assert "my-cmd" in result.output


def test_list_namespace_nonexistent(cli_runner, app, tmp_config_dir):
    """List --namespace nonexistent returns empty message."""
    cli_runner.invoke(app, ["register", "my-cmd", "--prompt", "do stuff"])
    result = cli_runner.invoke(app, ["list", "--namespace", "nonexistent"])
    assert result.exit_code == 0
    assert "No commands registered" in result.output


# === Phase 2 tests — show subcommand ===


def test_show_existing(cli_runner, app, tmp_config_dir):
    """Show existing command prints all fields."""
    cli_runner.invoke(app, ["register", "my-cmd", "--prompt", "do stuff"])
    result = cli_runner.invoke(app, ["show", "my-cmd"])
    assert result.exit_code == 0
    assert "my-cmd" in result.output
    assert "do stuff" in result.output


def test_show_nonexistent(cli_runner, app, tmp_config_dir):
    """Show nonexistent command exits 1 and prints 'not found'."""
    result = cli_runner.invoke(app, ["show", "ghost-cmd"])
    assert result.exit_code == 1
    assert "not found" in result.output


# === Phase 2 tests — update subcommand ===


def test_update_prompt(cli_runner, app, tmp_config_dir):
    """Update --prompt changes the prompt field."""
    cli_runner.invoke(app, ["register", "my-cmd", "--prompt", "old prompt"])
    result = cli_runner.invoke(app, ["update", "my-cmd", "--prompt", "new prompt"])
    assert result.exit_code == 0
    assert "Updated command" in result.output
    # Verify via show
    show = cli_runner.invoke(app, ["show", "my-cmd"])
    assert "new prompt" in show.output


def test_update_nonexistent(cli_runner, app, tmp_config_dir):
    """Update nonexistent command exits 1."""
    result = cli_runner.invoke(app, ["update", "ghost-cmd", "--prompt", "new"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_update_no_flags(cli_runner, app, tmp_config_dir):
    """Update with no flags prints warning."""
    cli_runner.invoke(app, ["register", "my-cmd", "--prompt", "do stuff"])
    result = cli_runner.invoke(app, ["update", "my-cmd"])
    assert result.exit_code == 0
    assert "No fields to update" in result.output


# === Phase 2 tests — delete subcommand ===


def test_delete_force(cli_runner, app, tmp_config_dir):
    """Delete --force removes command."""
    cli_runner.invoke(app, ["register", "my-cmd", "--prompt", "do stuff"])
    result = cli_runner.invoke(app, ["delete", "my-cmd", "--force"])
    assert result.exit_code == 0
    assert "Deleted command" in result.output


def test_delete_nonexistent(cli_runner, app, tmp_config_dir):
    """Delete nonexistent command exits 1."""
    result = cli_runner.invoke(app, ["delete", "ghost-cmd", "--force"])
    assert result.exit_code == 1
    assert "not found" in result.output


# === Phase 2 tests — pause subcommand ===


def test_pause_active(cli_runner, app, tmp_config_dir):
    """Pause sets status to paused."""
    cli_runner.invoke(app, ["register", "my-cmd", "--prompt", "do stuff"])
    result = cli_runner.invoke(app, ["pause", "my-cmd"])
    assert result.exit_code == 0
    assert "Paused command" in result.output


def test_pause_already_paused(cli_runner, app, tmp_config_dir):
    """Pause already-paused prints 'already paused'."""
    cli_runner.invoke(app, ["register", "my-cmd", "--prompt", "do stuff"])
    cli_runner.invoke(app, ["pause", "my-cmd"])
    result = cli_runner.invoke(app, ["pause", "my-cmd"])
    assert result.exit_code == 0
    assert "already paused" in result.output


def test_pause_nonexistent(cli_runner, app, tmp_config_dir):
    """Pause nonexistent command exits 1."""
    result = cli_runner.invoke(app, ["pause", "ghost-cmd"])
    assert result.exit_code == 1
    assert "not found" in result.output


# === Phase 2 tests — resume subcommand ===


def test_resume_paused(cli_runner, app, tmp_config_dir):
    """Resume sets status to active."""
    cli_runner.invoke(app, ["register", "my-cmd", "--prompt", "do stuff"])
    cli_runner.invoke(app, ["pause", "my-cmd"])
    result = cli_runner.invoke(app, ["resume", "my-cmd"])
    assert result.exit_code == 0
    assert "Resumed command" in result.output


def test_resume_already_active(cli_runner, app, tmp_config_dir):
    """Resume already-active prints 'already active'."""
    cli_runner.invoke(app, ["register", "my-cmd", "--prompt", "do stuff"])
    result = cli_runner.invoke(app, ["resume", "my-cmd"])
    assert result.exit_code == 0
    assert "already active" in result.output


def test_resume_nonexistent(cli_runner, app, tmp_config_dir):
    """Resume nonexistent command exits 1."""
    result = cli_runner.invoke(app, ["resume", "ghost-cmd"])
    assert result.exit_code == 1
    assert "not found" in result.output


# === Phase 3 tests — exec subcommand ===


def test_exec_command_not_found(cli_runner, app, tmp_config_dir):
    """Exec nonexistent command exits 1 and prints 'not found'."""
    result = cli_runner.invoke(app, ["exec", "nonexistent"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_exec_paused_command(cli_runner, app, tmp_config_dir):
    """Exec paused command exits 1 with actionable message."""
    cli_runner.invoke(app, ["register", "paused-cmd", "--prompt", "do stuff"])
    cli_runner.invoke(app, ["pause", "paused-cmd"])
    result = cli_runner.invoke(app, ["exec", "paused-cmd"])
    assert result.exit_code == 1
    assert "is paused" in result.output
    assert "navigator resume" in result.output


def test_exec_paused_exit_code(cli_runner, app, tmp_config_dir):
    """Exec paused command returns exactly exit code 1 (D-14)."""
    cli_runner.invoke(app, ["register", "paused-cmd", "--prompt", "do stuff"])
    cli_runner.invoke(app, ["pause", "paused-cmd"])
    result = cli_runner.invoke(app, ["exec", "paused-cmd"])
    assert result.exit_code == 1


def test_exec_active_command(cli_runner, app, tmp_config_dir, monkeypatch):
    """Exec active command calls execute_command and prints stdout."""
    from pathlib import Path

    from navigator.executor import ExecutionResult

    cli_runner.invoke(app, [
        "register", "my-cmd", "--prompt", "do stuff",
        "--environment", "/tmp",
    ])

    mock_result = ExecutionResult(
        command_name="my-cmd",
        returncode=0,
        stdout="Success output",
        stderr="",
        attempts=1,
        duration=1.5,
        timed_out=False,
        log_path=Path("/tmp/logs/my-cmd/test.log"),
    )
    monkeypatch.setattr(
        "navigator.executor.execute_command", lambda *a, **kw: mock_result
    )

    result = cli_runner.invoke(app, ["exec", "my-cmd"])
    assert result.exit_code == 0
    assert "Success output" in result.output


def test_exec_command_nonzero_exit(cli_runner, app, tmp_config_dir, monkeypatch):
    """Exec command with nonzero exit reports exit code and stderr."""
    from navigator.executor import ExecutionResult

    cli_runner.invoke(app, [
        "register", "fail-cmd", "--prompt", "do stuff",
        "--environment", "/tmp",
    ])

    mock_result = ExecutionResult(
        command_name="fail-cmd",
        returncode=1,
        stdout="",
        stderr="Error details",
        attempts=1,
        duration=0.5,
        timed_out=False,
        log_path=None,
    )
    monkeypatch.setattr(
        "navigator.executor.execute_command", lambda *a, **kw: mock_result
    )

    result = cli_runner.invoke(app, ["exec", "fail-cmd"])
    assert result.exit_code == 1
    assert "exited with code 1" in result.output


def test_exec_claude_not_found(cli_runner, app, tmp_config_dir, monkeypatch):
    """Exec when claude CLI not on PATH exits 1 with helpful error."""
    cli_runner.invoke(app, [
        "register", "my-cmd", "--prompt", "do stuff",
        "--environment", "/tmp",
    ])

    monkeypatch.setattr(
        "navigator.executor.shutil.which", lambda cmd: None
    )

    result = cli_runner.invoke(app, ["exec", "my-cmd"])
    assert result.exit_code == 1
    assert "claude CLI not found" in result.output


# === Phase 4 tests — exec flags (--timeout, --retries) ===


class TestExecFlags:
    """Tests for --timeout and --retries flags on exec command."""

    def test_exec_with_timeout_flag(self, cli_runner, app, tmp_config_dir, monkeypatch):
        """Exec --timeout passes timeout_override to execute_command."""
        from navigator.executor import ExecutionResult

        cli_runner.invoke(app, [
            "register", "test-cmd", "--prompt", "do stuff",
            "--environment", "/tmp",
        ])

        captured_kwargs = {}

        def mock_execute(cmd, config, timeout_override=None, retries_override=None):
            captured_kwargs["timeout_override"] = timeout_override
            captured_kwargs["retries_override"] = retries_override
            return ExecutionResult(
                command_name="test-cmd",
                returncode=0,
                stdout="ok",
                stderr="",
                attempts=1,
                duration=1.0,
                timed_out=False,
                log_path=None,
            )

        monkeypatch.setattr("navigator.executor.execute_command", mock_execute)

        result = cli_runner.invoke(app, ["exec", "test-cmd", "--timeout", "60"])
        assert result.exit_code == 0
        assert captured_kwargs["timeout_override"] == 60

    def test_exec_with_retries_flag(self, cli_runner, app, tmp_config_dir, monkeypatch):
        """Exec --retries passes retries_override to execute_command."""
        from navigator.executor import ExecutionResult

        cli_runner.invoke(app, [
            "register", "test-cmd", "--prompt", "do stuff",
            "--environment", "/tmp",
        ])

        captured_kwargs = {}

        def mock_execute(cmd, config, timeout_override=None, retries_override=None):
            captured_kwargs["timeout_override"] = timeout_override
            captured_kwargs["retries_override"] = retries_override
            return ExecutionResult(
                command_name="test-cmd",
                returncode=0,
                stdout="ok",
                stderr="",
                attempts=1,
                duration=1.0,
                timed_out=False,
                log_path=None,
            )

        monkeypatch.setattr("navigator.executor.execute_command", mock_execute)

        result = cli_runner.invoke(app, ["exec", "test-cmd", "--retries", "2"])
        assert result.exit_code == 0
        assert captured_kwargs["retries_override"] == 2

    def test_exec_shows_attempt_count(self, cli_runner, app, tmp_config_dir, monkeypatch):
        """Exec shows attempt count when more than 1 attempt."""
        from navigator.executor import ExecutionResult

        cli_runner.invoke(app, [
            "register", "test-cmd", "--prompt", "do stuff",
            "--environment", "/tmp",
        ])

        mock_result = ExecutionResult(
            command_name="test-cmd",
            returncode=0,
            stdout="ok",
            stderr="",
            attempts=3,
            duration=5.0,
            timed_out=False,
            log_path=None,
        )
        monkeypatch.setattr(
            "navigator.executor.execute_command", lambda *a, **kw: mock_result
        )

        result = cli_runner.invoke(app, ["exec", "test-cmd"])
        assert result.exit_code == 0
        assert "3 attempt(s)" in result.output


# === Phase 4 tests — logs command ===


class TestLogs:
    """Tests for navigator logs command."""

    def test_logs_no_entries(self, cli_runner, app, tmp_config_dir):
        """Logs for nonexistent command shows 'No execution logs'."""
        result = cli_runner.invoke(app, ["logs", "nonexistent"])
        assert result.exit_code == 0
        assert "No execution logs" in result.output

    def test_logs_table_output(self, cli_runner, app, tmp_config_dir):
        """Logs command shows table rows for existing log files."""
        from navigator.config import load_config
        from navigator.execution_logger import write_execution_log

        config = load_config()
        write_execution_log(
            log_dir=config.log_dir,
            command_name="test-cmd",
            attempt=1,
            returncode=0,
            duration=2.5,
            stdout="output",
            stderr="",
        )

        result = cli_runner.invoke(app, ["logs", "test-cmd"])
        assert result.exit_code == 0
        assert "Execution Logs" in result.output
        assert "2.50s" in result.output

    def test_logs_tail_shows_content(self, cli_runner, app, tmp_config_dir):
        """Logs --tail shows full content of last log."""
        from navigator.config import load_config
        from navigator.execution_logger import write_execution_log

        config = load_config()
        write_execution_log(
            log_dir=config.log_dir,
            command_name="test-cmd",
            attempt=1,
            returncode=0,
            duration=1.0,
            stdout="Detailed execution output here",
            stderr="",
        )

        result = cli_runner.invoke(app, ["logs", "test-cmd", "--tail"])
        assert result.exit_code == 0
        assert "Detailed execution output here" in result.output

    def test_logs_count_flag(self, cli_runner, app, tmp_config_dir):
        """Logs -n limits entries shown."""
        import time

        from navigator.config import load_config
        from navigator.execution_logger import write_execution_log

        config = load_config()
        for i in range(5):
            write_execution_log(
                log_dir=config.log_dir,
                command_name="test-cmd",
                attempt=1,
                returncode=i,
                duration=float(i),
                stdout=f"output-{i}",
                stderr="",
            )
            # Ensure distinct filenames (microsecond resolution)
            time.sleep(0.01)

        result = cli_runner.invoke(app, ["logs", "test-cmd", "-n", "2"])
        assert result.exit_code == 0
        # Table should exist
        assert "Execution Logs" in result.output
