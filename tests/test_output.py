"""Tests for navigator.output module -- JSON output infrastructure."""

from __future__ import annotations

import json


def test_json_response_ok():
    """json_response with ok status returns correct wrapper."""
    from navigator.output import json_response

    result = json.loads(json_response("ok", {"commands": []}))
    assert result["status"] == "ok"
    assert result["data"] == {"commands": []}
    assert result["message"] == ""


def test_json_response_error():
    """json_response with error status and message returns correct wrapper."""
    from navigator.output import json_response

    result = json.loads(json_response("error", message="not found"))
    assert result["status"] == "error"
    assert result["data"] is None
    assert result["message"] == "not found"


def test_json_response_with_list_data():
    """json_response accepts list as data."""
    from navigator.output import json_response

    result = json.loads(json_response("ok", [1, 2, 3]))
    assert result["data"] == [1, 2, 3]


def test_output_format_defaults_to_text():
    """output_format defaults to 'text'."""
    from navigator.output import output_format

    assert output_format == "text"


def test_is_json_false_by_default():
    """is_json() returns False when output_format is 'text'."""
    import navigator.output as nav_output

    nav_output.output_format = "text"
    assert nav_output.is_json() is False


def test_is_json_true_when_json():
    """is_json() returns True when output_format is 'json'."""
    import navigator.output as nav_output

    nav_output.output_format = "json"
    assert nav_output.is_json() is True
    # Reset
    nav_output.output_format = "text"


# === CLI integration tests for --output json ===


def test_json_list_empty(cli_runner, app, tmp_config_dir):
    """--output json list with no commands returns JSON with empty commands array."""
    result = cli_runner.invoke(app, ["--output", "json", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "ok"
    assert data["data"]["commands"] == []


def test_json_list_with_commands(cli_runner, app, tmp_config_dir):
    """--output json list with registered commands returns JSON array."""
    cli_runner.invoke(app, ["register", "my-cmd", "--prompt", "do stuff"])
    result = cli_runner.invoke(app, ["--output", "json", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "ok"
    assert len(data["data"]["commands"]) == 1
    assert data["data"]["commands"][0]["name"] == "my-cmd"


def test_json_show_existing(cli_runner, app, tmp_config_dir):
    """--output json show returns command details as JSON."""
    cli_runner.invoke(app, ["register", "my-cmd", "--prompt", "do stuff"])
    result = cli_runner.invoke(app, ["--output", "json", "show", "my-cmd"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "ok"
    assert data["data"]["name"] == "my-cmd"
    assert data["data"]["prompt"] == "do stuff"


def test_json_show_not_found(cli_runner, app, tmp_config_dir):
    """--output json show nonexistent returns error JSON."""
    result = cli_runner.invoke(app, ["--output", "json", "show", "ghost"])
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["status"] == "error"
    assert "not found" in data["message"]


def test_json_logs_no_entries(cli_runner, app, tmp_config_dir):
    """--output json logs with no log files returns empty logs array."""
    result = cli_runner.invoke(app, ["--output", "json", "logs", "nonexistent"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "ok"
    assert data["data"]["logs"] == []


def test_json_logs_with_entries(cli_runner, app, tmp_config_dir):
    """--output json logs with log files returns logs array."""
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

    result = cli_runner.invoke(app, ["--output", "json", "logs", "test-cmd"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "ok"
    assert len(data["data"]["logs"]) == 1
    assert "timestamp" in data["data"]["logs"][0]


def test_json_schedule_list_empty(cli_runner, app, tmp_config_dir, tmp_path, monkeypatch):
    """--output json schedule --list with no schedules returns empty array."""
    tab_file = tmp_path / "crontab"
    tab_file.write_text("")
    monkeypatch.setattr(
        "navigator.scheduler.CronTab",
        lambda **kw: __import__("crontab").CronTab(tabfile=str(tab_file)),
    )
    result = cli_runner.invoke(app, ["--output", "json", "schedule", "--list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "ok"
    assert data["data"]["schedules"] == []


def test_json_watch_list_empty(cli_runner, app, tmp_config_dir):
    """--output json watch --list with no watchers returns empty array."""
    result = cli_runner.invoke(app, ["--output", "json", "watch", "--list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "ok"
    assert data["data"]["watchers"] == []


def test_json_namespace_list(cli_runner, app, tmp_config_dir):
    """--output json namespace list returns namespaces array."""
    cli_runner.invoke(app, ["namespace", "create", "myproject"])
    result = cli_runner.invoke(app, ["--output", "json", "namespace", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "ok"
    assert len(data["data"]["namespaces"]) >= 1
    names = [ns["name"] for ns in data["data"]["namespaces"]]
    assert "default" in names
