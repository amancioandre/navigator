"""CLI invocation tests for INFRA-01 and registry subcommand integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest

SUBCOMMANDS = ["register", "list", "exec", "schedule", "watch", "chain", "logs", "daemon", "install-service", "uninstall-service", "service", "doctor", "namespace"]


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


# === Phase 5 tests — schedule subcommand ===


class TestSchedule:
    """Tests for navigator schedule command."""

    @pytest.fixture()
    def schedule_env(self, tmp_config_dir, tmp_path, monkeypatch):
        """Set up environment for schedule CLI tests.

        Patches CronTab to use a tabfile and shutil.which to find navigator.
        Registers a test command in the DB for scheduling operations.
        """
        tab_file = tmp_path / "crontab"
        tab_file.write_text("")

        monkeypatch.setattr(
            "navigator.scheduler.CronTab",
            lambda **kw: __import__("crontab").CronTab(tabfile=str(tab_file)),
        )
        monkeypatch.setattr(
            "navigator.scheduler.shutil",
            type(
                "shutil",
                (),
                {"which": staticmethod(lambda cmd: "/usr/local/bin/navigator")},
            ),
        )

        # Register a test command via CLI so DB is properly initialized
        from typer.testing import CliRunner

        from navigator.cli import app as nav_app

        runner = CliRunner()
        runner.invoke(nav_app, [
            "register", "test-cmd",
            "--prompt", "Run tests",
            "--environment", "/tmp",
        ])

        return {"tab_file": tab_file}

    @pytest.fixture()
    def schedule_env_with_paused(self, schedule_env, cli_runner, app):
        """Schedule env with an additional paused command."""
        cli_runner.invoke(app, [
            "register", "paused-cmd",
            "--prompt", "Paused command",
            "--environment", "/tmp",
        ])
        cli_runner.invoke(app, ["pause", "paused-cmd"])
        return schedule_env

    def test_schedule_command_with_cron(self, cli_runner, app, schedule_env):
        """navigator schedule test-cmd --cron '*/5 * * * *' exits 0 with success."""
        result = cli_runner.invoke(
            app, ["schedule", "test-cmd", "--cron", "*/5 * * * *"]
        )
        assert result.exit_code == 0
        assert "Scheduled" in result.output
        assert "test-cmd" in result.output

    def test_schedule_command_list(self, cli_runner, app, schedule_env):
        """navigator schedule --list shows scheduled commands in table."""
        # First schedule a command
        cli_runner.invoke(
            app, ["schedule", "test-cmd", "--cron", "*/5 * * * *"]
        )
        result = cli_runner.invoke(app, ["schedule", "--list"])
        assert result.exit_code == 0
        assert "test-cmd" in result.output
        assert "Scheduled Commands" in result.output

    def test_schedule_command_list_empty(self, cli_runner, app, schedule_env):
        """navigator schedule --list with no schedules shows empty message."""
        result = cli_runner.invoke(app, ["schedule", "--list"])
        assert result.exit_code == 0
        assert "No scheduled commands" in result.output

    def test_schedule_command_remove(self, cli_runner, app, schedule_env):
        """navigator schedule test-cmd --remove exits 0 with success."""
        # First schedule, then remove
        cli_runner.invoke(
            app, ["schedule", "test-cmd", "--cron", "*/5 * * * *"]
        )
        result = cli_runner.invoke(
            app, ["schedule", "test-cmd", "--remove"]
        )
        assert result.exit_code == 0
        assert "Removed schedule" in result.output

    def test_schedule_command_remove_not_scheduled(
        self, cli_runner, app, schedule_env
    ):
        """navigator schedule test-cmd --remove when not scheduled shows warning."""
        result = cli_runner.invoke(
            app, ["schedule", "test-cmd", "--remove"]
        )
        assert result.exit_code == 0
        assert "was not scheduled" in result.output

    def test_schedule_nonexistent_command(
        self, cli_runner, app, schedule_env
    ):
        """Scheduling unknown command shows error and exit 1."""
        result = cli_runner.invoke(
            app, ["schedule", "ghost-cmd", "--cron", "*/5 * * * *"]
        )
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_schedule_paused_command(
        self, cli_runner, app, schedule_env_with_paused
    ):
        """Scheduling paused command shows error suggesting resume."""
        result = cli_runner.invoke(
            app, ["schedule", "paused-cmd", "--cron", "*/5 * * * *"]
        )
        assert result.exit_code == 1
        assert "paused" in result.output
        assert "navigator resume" in result.output

    def test_schedule_invalid_cron(self, cli_runner, app, schedule_env):
        """Invalid cron expression shows error and exit 1."""
        result = cli_runner.invoke(
            app, ["schedule", "test-cmd", "--cron", "invalid-cron"]
        )
        assert result.exit_code == 1
        assert "Invalid cron" in result.output or "invalid" in result.output.lower()

    def test_schedule_no_args(self, cli_runner, app, schedule_env):
        """navigator schedule with no arguments shows error."""
        result = cli_runner.invoke(app, ["schedule"])
        assert result.exit_code == 1
        assert "Command name required" in result.output or "Use --cron" in result.output

    def test_schedule_cron_and_remove_conflict(
        self, cli_runner, app, schedule_env
    ):
        """Using both --cron and --remove shows error."""
        result = cli_runner.invoke(
            app, ["schedule", "test-cmd", "--cron", "*/5 * * * *", "--remove"]
        )
        assert result.exit_code == 1
        assert "Cannot use --cron and --remove together" in result.output


# === Phase 6 tests — watch subcommand ===


class TestWatch:
    """Tests for navigator watch command."""

    def test_watch_list_empty(self, cli_runner, app, tmp_config_dir):
        """navigator watch --list shows 'No watchers' when none registered."""
        result = cli_runner.invoke(app, ["watch", "--list"])
        assert result.exit_code == 0
        assert "No watchers registered" in result.output

    def test_watch_register(self, cli_runner, app, tmp_config_dir):
        """Register a watcher for existing command succeeds."""
        cli_runner.invoke(app, [
            "register", "test-cmd", "--prompt", "Run tests",
            "--environment", "/tmp",
        ])
        result = cli_runner.invoke(app, [
            "watch", "test-cmd", "--path", "/tmp", "--pattern", "*.md",
        ])
        assert result.exit_code == 0
        assert "Registered watcher" in result.output

    def test_watch_register_missing_command(self, cli_runner, app, tmp_config_dir):
        """Registering watcher for nonexistent command exits 1."""
        result = cli_runner.invoke(app, [
            "watch", "nonexistent", "--path", "/tmp",
        ])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_watch_list_after_register(self, cli_runner, app, tmp_config_dir):
        """After registering a watcher, --list shows it in a table."""
        cli_runner.invoke(app, [
            "register", "test-cmd", "--prompt", "Run tests",
            "--environment", "/tmp",
        ])
        cli_runner.invoke(app, [
            "watch", "test-cmd", "--path", "/tmp", "--pattern", "*.md",
        ])
        result = cli_runner.invoke(app, ["watch", "--list"])
        assert result.exit_code == 0
        assert "test-cmd" in result.output
        assert "Registered Watchers" in result.output

    def test_watch_remove(self, cli_runner, app, tmp_config_dir):
        """Removing watchers for a command succeeds."""
        cli_runner.invoke(app, [
            "register", "test-cmd", "--prompt", "Run tests",
            "--environment", "/tmp",
        ])
        cli_runner.invoke(app, [
            "watch", "test-cmd", "--path", "/tmp",
        ])
        result = cli_runner.invoke(app, ["watch", "test-cmd", "--remove"])
        assert result.exit_code == 0
        assert "Removed" in result.output

    def test_watch_remove_nonexistent(self, cli_runner, app, tmp_config_dir):
        """Removing watchers for command with none shows appropriate message."""
        result = cli_runner.invoke(app, ["watch", "nonexistent", "--remove"])
        assert result.exit_code == 0
        assert "No watchers found" in result.output

    def test_watch_no_args(self, cli_runner, app, tmp_config_dir):
        """Watch with command but no --path or --remove shows usage hint."""
        cli_runner.invoke(app, [
            "register", "test-cmd", "--prompt", "Run tests",
            "--environment", "/tmp",
        ])
        result = cli_runner.invoke(app, ["watch", "test-cmd"])
        assert result.exit_code == 1
        assert "Use --path" in result.output


# === Phase 7 tests — namespace subcommand ===


def test_namespace_create(cli_runner, app, tmp_config_dir):
    """Create a namespace exits 0 and prints confirmation."""
    result = cli_runner.invoke(app, ["namespace", "create", "myproject"])
    assert result.exit_code == 0
    assert "Created namespace" in result.output


def test_namespace_create_duplicate(cli_runner, app, tmp_config_dir):
    """Creating duplicate namespace exits 1."""
    cli_runner.invoke(app, ["namespace", "create", "myproject"])
    result = cli_runner.invoke(app, ["namespace", "create", "myproject"])
    assert result.exit_code == 1
    assert "already exists" in result.output


def test_namespace_create_invalid_name(cli_runner, app, tmp_config_dir):
    """Creating namespace with uppercase name exits 1."""
    result = cli_runner.invoke(app, ["namespace", "create", "INVALID"])
    assert result.exit_code == 1


def test_namespace_list(cli_runner, app, tmp_config_dir):
    """List namespaces shows at least 'default'."""
    # Trigger DB init by creating a namespace (default is auto-created by init_db)
    cli_runner.invoke(app, ["namespace", "create", "myproject"])
    result = cli_runner.invoke(app, ["namespace", "list"])
    assert result.exit_code == 0
    assert "default" in result.output


def test_namespace_delete_empty(cli_runner, app, tmp_config_dir):
    """Create then delete empty namespace exits 0."""
    cli_runner.invoke(app, ["namespace", "create", "myproject"])
    result = cli_runner.invoke(app, ["namespace", "delete", "myproject"])
    assert result.exit_code == 0
    assert "Deleted namespace" in result.output


def test_namespace_delete_default_rejected(cli_runner, app, tmp_config_dir):
    """Deleting 'default' namespace exits 1."""
    result = cli_runner.invoke(app, ["namespace", "delete", "default"])
    assert result.exit_code == 1
    assert "Cannot delete" in result.output


# === Phase 7 tests — qualified names and --namespace on register ===


def test_register_with_namespace(cli_runner, app, tmp_config_dir):
    """Register command with --namespace puts it in that namespace."""
    cli_runner.invoke(app, ["namespace", "create", "myns"])
    result = cli_runner.invoke(app, [
        "register", "my-cmd", "--prompt", "do stuff", "--namespace", "myns",
    ])
    assert result.exit_code == 0
    assert "Registered command" in result.output

    # Verify it appears in namespace-filtered list
    result = cli_runner.invoke(app, ["list", "--namespace", "myns"])
    assert "my-cmd" in result.output


def test_register_nonexistent_namespace(cli_runner, app, tmp_config_dir):
    """Register with --namespace that doesn't exist exits 1."""
    result = cli_runner.invoke(app, [
        "register", "my-cmd", "--prompt", "do stuff", "--namespace", "nonexistent",
    ])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_exec_qualified_name(cli_runner, app, tmp_config_dir, monkeypatch):
    """Exec with qualified name myns:cmd-name resolves correctly."""
    from navigator.executor import ExecutionResult

    cli_runner.invoke(app, ["namespace", "create", "myns"])
    cli_runner.invoke(app, [
        "register", "my-cmd", "--prompt", "do stuff",
        "--environment", "/tmp", "--namespace", "myns",
    ])

    mock_result = ExecutionResult(
        command_name="my-cmd",
        returncode=0,
        stdout="Qualified exec output",
        stderr="",
        attempts=1,
        duration=1.0,
        timed_out=False,
        log_path=None,
    )
    monkeypatch.setattr(
        "navigator.executor.execute_command", lambda *a, **kw: mock_result
    )

    result = cli_runner.invoke(app, ["exec", "myns:my-cmd"])
    assert result.exit_code == 0
    assert "Qualified exec output" in result.output


def test_exec_wrong_namespace(cli_runner, app, tmp_config_dir, monkeypatch):
    """Exec with wrong namespace in qualified name exits 1."""
    from navigator.executor import ExecutionResult

    cli_runner.invoke(app, ["namespace", "create", "myns"])
    cli_runner.invoke(app, [
        "register", "my-cmd", "--prompt", "do stuff",
        "--environment", "/tmp", "--namespace", "myns",
    ])

    monkeypatch.setattr(
        "navigator.executor.execute_command",
        lambda *a, **kw: ExecutionResult(
            command_name="my-cmd", returncode=0, stdout="", stderr="",
            attempts=1, duration=1.0, timed_out=False, log_path=None,
        ),
    )

    result = cli_runner.invoke(app, ["exec", "other:my-cmd"])
    assert result.exit_code == 1
    assert "not 'other'" in result.output


def test_show_qualified_name(cli_runner, app, tmp_config_dir):
    """Show with qualified name myns:cmd-name works."""
    cli_runner.invoke(app, ["namespace", "create", "myns"])
    cli_runner.invoke(app, [
        "register", "my-cmd", "--prompt", "do stuff",
        "--environment", "/tmp", "--namespace", "myns",
    ])
    result = cli_runner.invoke(app, ["show", "myns:my-cmd"])
    assert result.exit_code == 0
    assert "my-cmd" in result.output
    assert "do stuff" in result.output


# === Phase 8 tests — chain subcommand ===


class TestChain:
    """Tests for navigator chain command."""

    def _register_two(self, cli_runner, app):
        """Helper: register two commands for chaining."""
        cli_runner.invoke(app, [
            "register", "cmd-a", "--prompt", "do A", "--environment", "/tmp",
        ])
        cli_runner.invoke(app, [
            "register", "cmd-b", "--prompt", "do B", "--environment", "/tmp",
        ])

    def test_chain_link_commands(self, cli_runner, app, tmp_config_dir):
        """Chain two commands with --next succeeds."""
        self._register_two(cli_runner, app)
        result = cli_runner.invoke(app, ["chain", "cmd-a", "--next", "cmd-b"])
        assert result.exit_code == 0
        assert "Chained" in result.output
        assert "cmd-a" in result.output
        assert "cmd-b" in result.output

    def test_chain_show(self, cli_runner, app, tmp_config_dir):
        """Chain --show displays arrow diagram."""
        self._register_two(cli_runner, app)
        cli_runner.invoke(app, ["chain", "cmd-a", "--next", "cmd-b"])
        result = cli_runner.invoke(app, ["chain", "cmd-a", "--show"])
        assert result.exit_code == 0
        assert "->" in result.output
        assert "cmd-a" in result.output
        assert "cmd-b" in result.output

    def test_chain_remove(self, cli_runner, app, tmp_config_dir):
        """Chain --remove unlinks commands."""
        self._register_two(cli_runner, app)
        cli_runner.invoke(app, ["chain", "cmd-a", "--next", "cmd-b"])
        result = cli_runner.invoke(app, ["chain", "cmd-a", "--remove"])
        assert result.exit_code == 0
        assert "Removed chain link" in result.output

    def test_chain_cycle_rejected(self, cli_runner, app, tmp_config_dir):
        """Cycle detection rejects A->B->A."""
        self._register_two(cli_runner, app)
        cli_runner.invoke(app, ["chain", "cmd-a", "--next", "cmd-b"])
        result = cli_runner.invoke(app, ["chain", "cmd-b", "--next", "cmd-a"])
        assert result.exit_code == 1
        assert "Cycle detected" in result.output

    def test_chain_nonexistent_command(self, cli_runner, app, tmp_config_dir):
        """Chain to nonexistent command exits 1."""
        cli_runner.invoke(app, [
            "register", "cmd-a", "--prompt", "do A", "--environment", "/tmp",
        ])
        result = cli_runner.invoke(app, ["chain", "cmd-a", "--next", "ghost"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_chain_on_failure_continue(self, cli_runner, app, tmp_config_dir):
        """Chain with --on-failure continue stores correctly."""
        self._register_two(cli_runner, app)
        result = cli_runner.invoke(app, [
            "chain", "cmd-a", "--next", "cmd-b", "--on-failure", "continue",
        ])
        assert result.exit_code == 0
        assert "Chained" in result.output

        # Verify via --show that continue annotation appears
        result = cli_runner.invoke(app, ["chain", "cmd-a", "--show"])
        assert "continue on failure" in result.output

    def test_chain_no_flags(self, cli_runner, app, tmp_config_dir):
        """Chain without --next/--show/--remove shows usage hint."""
        cli_runner.invoke(app, [
            "register", "cmd-a", "--prompt", "do A", "--environment", "/tmp",
        ])
        result = cli_runner.invoke(app, ["chain", "cmd-a"])
        assert result.exit_code == 1
        assert "--next" in result.output or "--show" in result.output

    def test_chain_remove_no_link(self, cli_runner, app, tmp_config_dir):
        """Remove on command with no chain link shows warning."""
        cli_runner.invoke(app, [
            "register", "cmd-a", "--prompt", "do A", "--environment", "/tmp",
        ])
        result = cli_runner.invoke(app, ["chain", "cmd-a", "--remove"])
        assert result.exit_code == 0
        assert "has no chain link" in result.output

    def test_chain_self_link_rejected(self, cli_runner, app, tmp_config_dir):
        """Self-link A->A is rejected as cycle."""
        cli_runner.invoke(app, [
            "register", "cmd-a", "--prompt", "do A", "--environment", "/tmp",
        ])
        result = cli_runner.invoke(app, ["chain", "cmd-a", "--next", "cmd-a"])
        assert result.exit_code == 1
        assert "Cycle detected" in result.output

    def test_exec_follows_chain(self, cli_runner, app, tmp_config_dir, monkeypatch):
        """Exec with chained commands calls execute_chain and shows Chain ID."""
        from navigator.chainer import ChainResult
        from navigator.executor import ExecutionResult

        self._register_two(cli_runner, app)
        cli_runner.invoke(app, ["chain", "cmd-a", "--next", "cmd-b"])

        mock_chain_result = ChainResult(
            correlation_id="test-corr-id-1234",
            results=[
                ExecutionResult(
                    command_name="cmd-a", returncode=0, stdout="A out",
                    stderr="", attempts=1, duration=1.0, timed_out=False, log_path=None,
                ),
                ExecutionResult(
                    command_name="cmd-b", returncode=0, stdout="B out",
                    stderr="", attempts=1, duration=1.0, timed_out=False, log_path=None,
                ),
            ],
            success=True,
            steps_run=2,
            total_steps=2,
        )
        monkeypatch.setattr(
            "navigator.chainer.execute_chain",
            lambda conn, cmd, config: mock_chain_result,
        )

        result = cli_runner.invoke(app, ["exec", "cmd-a"])
        assert result.exit_code == 0
        assert "Chain ID" in result.output
        assert "test-corr-id-1234" in result.output
        assert "2/2" in result.output


# === Phase 9 tests — daemon and service CLI commands ===


class TestDaemon:
    """Tests for the daemon CLI command."""

    def test_daemon_calls_run_daemon(self, cli_runner, app, monkeypatch):
        """daemon command calls run_daemon with loaded config."""
        from unittest.mock import MagicMock

        mock_config = MagicMock()
        mock_run_daemon = MagicMock()
        monkeypatch.setattr("navigator.config.load_config", lambda: mock_config)
        monkeypatch.setattr("navigator.watcher.run_daemon", mock_run_daemon)

        result = cli_runner.invoke(app, ["daemon"])
        assert result.exit_code == 0
        mock_run_daemon.assert_called_once_with(mock_config)

    def test_daemon_help(self, cli_runner, app):
        """daemon --help exits 0 and mentions foreground."""
        result = cli_runner.invoke(app, ["daemon", "--help"])
        assert result.exit_code == 0
        assert "foreground" in result.output


class TestServiceCLI:
    """Tests for install-service, uninstall-service, and service CLI commands."""

    def test_install_service_success(self, cli_runner, app, monkeypatch):
        """install-service prints path on success."""
        monkeypatch.setattr(
            "navigator.service.install_service",
            lambda enable_linger: Path("/tmp/test.service"),
        )
        result = cli_runner.invoke(app, ["install-service"])
        assert result.exit_code == 0
        assert "installed" in result.output.lower()

    def test_install_service_not_found(self, cli_runner, app, monkeypatch):
        """install-service exits 1 when navigator binary not found."""
        def _raise(enable_linger):
            raise FileNotFoundError("navigator binary not found")

        monkeypatch.setattr("navigator.service.install_service", _raise)
        result = cli_runner.invoke(app, ["install-service"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_install_service_no_linger(self, cli_runner, app, monkeypatch):
        """install-service --no-linger passes enable_linger=False."""
        captured = {}

        def _capture(enable_linger):
            captured["enable_linger"] = enable_linger
            return Path("/tmp/test.service")

        monkeypatch.setattr("navigator.service.install_service", _capture)
        result = cli_runner.invoke(app, ["install-service", "--no-linger"])
        assert result.exit_code == 0
        assert captured["enable_linger"] is False

    def test_uninstall_service_existed(self, cli_runner, app, monkeypatch):
        """uninstall-service shows 'uninstalled' when service existed."""
        monkeypatch.setattr(
            "navigator.service.uninstall_service", lambda: True
        )
        result = cli_runner.invoke(app, ["uninstall-service"])
        assert result.exit_code == 0
        assert "uninstalled" in result.output.lower()

    def test_uninstall_service_not_installed(self, cli_runner, app, monkeypatch):
        """uninstall-service shows 'not installed' when service did not exist."""
        monkeypatch.setattr(
            "navigator.service.uninstall_service", lambda: False
        )
        result = cli_runner.invoke(app, ["uninstall-service"])
        assert result.exit_code == 0
        assert "not installed" in result.output.lower()

    def test_service_status(self, cli_runner, app, monkeypatch):
        """service status prints stdout on success."""
        from subprocess import CompletedProcess

        monkeypatch.setattr(
            "navigator.service.service_control",
            lambda action: CompletedProcess(
                args=[], returncode=0, stdout="active (running)\n", stderr=""
            ),
        )
        result = cli_runner.invoke(app, ["service", "status"])
        assert result.exit_code == 0
        assert "active" in result.output

    def test_service_invalid_action(self, cli_runner, app, monkeypatch):
        """service with invalid action exits 1."""
        def _raise(action):
            raise ValueError("Invalid action")

        monkeypatch.setattr("navigator.service.service_control", _raise)
        result = cli_runner.invoke(app, ["service", "bogus"])
        assert result.exit_code == 1

    def test_service_failed_exit_code(self, cli_runner, app, monkeypatch):
        """service propagates non-zero exit code from systemctl."""
        from subprocess import CompletedProcess

        monkeypatch.setattr(
            "navigator.service.service_control",
            lambda action: CompletedProcess(
                args=[], returncode=3, stdout="", stderr="inactive"
            ),
        )
        result = cli_runner.invoke(app, ["service", "status"])
        assert result.exit_code == 3


# === Phase 10 tests — --dry-run on exec ===


class TestDryRun:
    """Tests for navigator exec --dry-run flag."""

    def test_dry_run_text_output(self, cli_runner, app, tmp_config_dir, monkeypatch):
        """Exec --dry-run shows Rich panel with command preview."""
        cli_runner.invoke(app, [
            "register", "test-cmd", "--prompt", "do stuff",
            "--environment", "/tmp",
            "--allowed-tools", "Read,Write",
        ])

        # Mock build functions so we don't need real claude binary
        monkeypatch.setattr(
            "navigator.executor.build_command_args",
            lambda prompt, tools: ["claude", "-p", prompt, "--print"],
        )
        monkeypatch.setattr(
            "navigator.executor.build_clean_env",
            lambda secrets=None, extra_env=None: {"PATH": "/usr/bin", "HOME": "/home/test"},
        )
        monkeypatch.setattr(
            "navigator.secrets.load_secrets",
            lambda path: {},
        )

        result = cli_runner.invoke(app, ["exec", "test-cmd", "--dry-run"])
        assert result.exit_code == 0
        assert "Dry Run" in result.output
        assert "test-cmd" in result.output
        assert "/tmp" in result.output

    def test_dry_run_does_not_execute(self, cli_runner, app, tmp_config_dir, monkeypatch):
        """Exec --dry-run never calls execute_command."""
        cli_runner.invoke(app, [
            "register", "test-cmd", "--prompt", "do stuff",
            "--environment", "/tmp",
        ])

        execute_called = {"called": False}

        def mock_execute(*a, **kw):
            execute_called["called"] = True

        monkeypatch.setattr("navigator.executor.execute_command", mock_execute)
        monkeypatch.setattr(
            "navigator.executor.build_command_args",
            lambda prompt, tools: ["claude", "-p", prompt, "--print"],
        )
        monkeypatch.setattr(
            "navigator.executor.build_clean_env",
            lambda secrets=None, extra_env=None: {"PATH": "/usr/bin"},
        )
        monkeypatch.setattr(
            "navigator.secrets.load_secrets",
            lambda path: {},
        )

        result = cli_runner.invoke(app, ["exec", "test-cmd", "--dry-run"])
        assert result.exit_code == 0
        assert not execute_called["called"]

    def test_dry_run_shows_env_keys_not_values(self, cli_runner, app, tmp_config_dir, monkeypatch):
        """Exec --dry-run shows env key names but never secret values."""
        cli_runner.invoke(app, [
            "register", "test-cmd", "--prompt", "do stuff",
            "--environment", "/tmp",
        ])

        monkeypatch.setattr(
            "navigator.executor.build_command_args",
            lambda prompt, tools: ["claude", "-p", prompt, "--print"],
        )
        monkeypatch.setattr(
            "navigator.executor.build_clean_env",
            lambda secrets=None, extra_env=None: {
                "PATH": "/usr/bin",
                "MY_SECRET": "super-secret-value-12345",
            },
        )
        monkeypatch.setattr(
            "navigator.secrets.load_secrets",
            lambda path: {"MY_SECRET": "super-secret-value-12345"},
        )

        result = cli_runner.invoke(app, ["exec", "test-cmd", "--dry-run"])
        assert result.exit_code == 0
        assert "MY_SECRET" in result.output
        assert "super-secret-value-12345" not in result.output

    def test_dry_run_json_output(self, cli_runner, app, tmp_config_dir, monkeypatch):
        """Exec --output json --dry-run returns JSON with dry run data."""
        import json

        cli_runner.invoke(app, [
            "register", "test-cmd", "--prompt", "do stuff",
            "--environment", "/tmp",
            "--allowed-tools", "Read,Write",
        ])

        monkeypatch.setattr(
            "navigator.executor.build_command_args",
            lambda prompt, tools: ["claude", "-p", prompt, "--print"],
        )
        monkeypatch.setattr(
            "navigator.executor.build_clean_env",
            lambda secrets=None, extra_env=None: {"PATH": "/usr/bin", "HOME": "/home/test"},
        )
        monkeypatch.setattr(
            "navigator.secrets.load_secrets",
            lambda path: {},
        )

        result = cli_runner.invoke(app, ["--output", "json", "exec", "test-cmd", "--dry-run"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ok"
        assert data["data"]["command_name"] == "test-cmd"
        assert "command_args" in data["data"]
        assert "env_keys" in data["data"]
        assert "working_directory" in data["data"]
        assert data["data"]["working_directory"] == "/tmp"

    def test_dry_run_nonexistent_command(self, cli_runner, app, tmp_config_dir):
        """Exec nonexistent --dry-run exits 1 with error."""
        result = cli_runner.invoke(app, ["exec", "nonexistent", "--dry-run"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_dry_run_paused_command(self, cli_runner, app, tmp_config_dir):
        """Exec paused-cmd --dry-run exits 1 (paused check still applies)."""
        cli_runner.invoke(app, ["register", "paused-cmd", "--prompt", "do stuff"])
        cli_runner.invoke(app, ["pause", "paused-cmd"])
        result = cli_runner.invoke(app, ["exec", "paused-cmd", "--dry-run"])
        assert result.exit_code == 1
        assert "paused" in result.output


# === Phase 10 tests — doctor command ===


class TestDoctor:
    def test_doctor_healthy_system(self, cli_runner, app, tmp_config_dir, monkeypatch):
        """navigator doctor with healthy system exits 0 and shows PASS."""
        from unittest.mock import MagicMock

        from navigator.doctor import CheckResult, DoctorResult

        mock_result = DoctorResult(
            checks=[
                CheckResult(name="Database", status="pass", message="Database OK (3 commands)"),
                CheckResult(name="Navigator binary", status="pass", message="Found at /usr/bin/navigator"),
                CheckResult(name="Registered paths", status="pass", message="All paths exist"),
            ]
        )

        monkeypatch.setattr("navigator.doctor.run_doctor", lambda config, fix=False: mock_result)
        result = cli_runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_doctor_with_failures(self, cli_runner, app, tmp_config_dir, monkeypatch):
        """navigator doctor with failures exits 1."""
        from navigator.doctor import CheckResult, DoctorResult

        mock_result = DoctorResult(
            checks=[
                CheckResult(name="Database", status="fail", message="Database error"),
                CheckResult(name="Binary", status="pass", message="OK"),
            ]
        )

        monkeypatch.setattr("navigator.doctor.run_doctor", lambda config, fix=False: mock_result)
        result = cli_runner.invoke(app, ["doctor"])
        assert result.exit_code == 1
        assert "FAIL" in result.output

    def test_doctor_fix_flag(self, cli_runner, app, tmp_config_dir, monkeypatch):
        """navigator doctor --fix passes fix=True to run_doctor."""
        from navigator.doctor import CheckResult, DoctorResult

        called_with_fix = {}

        def mock_run_doctor(config, fix=False):
            called_with_fix["fix"] = fix
            return DoctorResult(
                checks=[
                    CheckResult(name="Log dir", status="warn", message="Missing", fixable=True, fixed=True),
                ]
            )

        monkeypatch.setattr("navigator.doctor.run_doctor", mock_run_doctor)
        result = cli_runner.invoke(app, ["doctor", "--fix"])
        assert result.exit_code == 0
        assert called_with_fix["fix"] is True
        assert "fixed" in result.output.lower()

    def test_doctor_json_output(self, cli_runner, app, tmp_config_dir, monkeypatch):
        """navigator --output json doctor returns valid JSON with checks and summary."""
        import json

        from navigator.doctor import CheckResult, DoctorResult

        mock_result = DoctorResult(
            checks=[
                CheckResult(name="Database", status="pass", message="OK"),
                CheckResult(name="Binary", status="pass", message="Found"),
            ]
        )

        monkeypatch.setattr("navigator.doctor.run_doctor", lambda config, fix=False: mock_result)
        result = cli_runner.invoke(app, ["--output", "json", "doctor"])
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert data["status"] == "ok"
        assert "checks" in data["data"]
        assert "summary" in data["data"]
        assert len(data["data"]["checks"]) == 2
        assert data["data"]["summary"]["total"] == 2
        assert data["data"]["summary"]["passed"] == 2
