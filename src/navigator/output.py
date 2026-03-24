"""Navigator output module -- JSON output infrastructure for CLI scriptability.

Provides a global output_format state and helpers for consistent JSON responses.
When output_format is set to "json", CLI commands emit structured JSON instead
of Rich-formatted tables.
"""

from __future__ import annotations

import json

# Module-level global state for output format (set by --output callback)
output_format: str = "text"


def is_json() -> bool:
    """Check if the current output format is JSON."""
    return output_format == "json"


def json_response(
    status: str,
    data: dict | list | None = None,
    message: str = "",
) -> str:
    """Return a consistent JSON wrapper string.

    Format: {"status": "ok"|"error", "data": ..., "message": "..."}
    """
    return json.dumps(
        {"status": status, "data": data, "message": message},
        indent=2,
        default=str,
    )
