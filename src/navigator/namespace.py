"""Navigator namespace utilities — qualified name parsing and secrets path resolution."""

from __future__ import annotations

from pathlib import Path


def parse_qualified_name(qualified: str) -> tuple[str, str]:
    """Parse a qualified name into (namespace, command) tuple.

    - "namespace:command" -> ("namespace", "command")
    - "command" -> ("default", "command")
    - Multiple colons or empty parts raise ValueError.
    """
    parts = qualified.split(":")
    if len(parts) == 1:
        return ("default", qualified)
    if len(parts) == 2:
        namespace, command = parts
        if not namespace:
            msg = "Invalid qualified name: empty namespace"
            raise ValueError(msg)
        if not command:
            msg = "Invalid qualified name: empty command"
            raise ValueError(msg)
        return (namespace, command)
    msg = "Invalid qualified name: multiple colons"
    raise ValueError(msg)


def namespace_secrets_path(namespace: str) -> Path:
    """Return the secrets directory path for a namespace.

    Secrets live at ~/.secrets/<namespace>/.
    """
    return Path.home() / ".secrets" / namespace
