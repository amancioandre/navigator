"""Config creation/loading test stubs for Plan 02."""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Implemented in Plan 02")
def test_first_run_creates_config():
    """First invocation creates config.toml with defaults."""


@pytest.mark.skip(reason="Implemented in Plan 02")
def test_load_existing_config():
    """Existing config.toml is loaded correctly."""


@pytest.mark.skip(reason="Implemented in Plan 02")
def test_paths_are_absolute():
    """All path fields in config are resolved to absolute paths."""


@pytest.mark.skip(reason="Implemented in Plan 02")
def test_resolve_path():
    """resolve_path handles ~, relative, and absolute input."""
