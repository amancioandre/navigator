"""CLI invocation tests for INFRA-01."""

from __future__ import annotations

import pytest


SUBCOMMANDS = ["register", "list", "exec", "schedule", "watch", "chain", "logs", "doctor"]


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
