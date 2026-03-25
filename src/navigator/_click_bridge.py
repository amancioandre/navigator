"""Expose Navigator's Typer CLI as a Click group for mkdocs-click."""

import typer.main

from navigator.cli import app

# mkdocs-click needs a Click Group object, not a Typer app.
# typer.main.get_command() returns the underlying Click Group.
cli = typer.main.get_command(app)
