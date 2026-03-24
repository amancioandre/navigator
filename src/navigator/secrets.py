"""Navigator secret loading -- reads .env files for subprocess injection."""

from __future__ import annotations

import logging
import stat
from pathlib import Path

logger = logging.getLogger(__name__)


def load_secrets(secrets_path: Path | None) -> dict[str, str]:
    """Load secrets from a .env file.

    Returns a dict of key-value pairs. If the path is None or missing,
    returns an empty dict. Secret values are never logged -- only key names.
    """
    if secrets_path is None:
        return {}

    if not secrets_path.exists():
        logger.warning(
            "Secrets file not found: %s (continuing without secrets)", secrets_path
        )
        return {}

    if not secrets_path.is_file():
        logger.warning(
            "Secrets path is not a file: %s (continuing without secrets)", secrets_path
        )
        return {}

    # Warn if file is readable by group or others
    file_mode = secrets_path.stat().st_mode
    if file_mode & (stat.S_IRGRP | stat.S_IROTH):
        logger.warning(
            "Secrets file %s is readable by group/others. Consider: chmod 600 %s",
            secrets_path,
            secrets_path,
        )

    from dotenv import dotenv_values

    raw = dotenv_values(secrets_path)
    secrets = {k: v for k, v in raw.items() if v is not None}

    logger.info(
        "Loaded %d secret(s) from %s: %s",
        len(secrets),
        secrets_path,
        list(secrets.keys()),
    )

    return secrets
