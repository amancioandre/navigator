"""Navigator configuration — TOML-based config with XDG-compliant paths.

Provides first-run config creation, loading, and absolute path resolution.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import platformdirs
import tomli_w
from pydantic import BaseModel, Field


def get_config_dir() -> Path:
    """Return the XDG-compliant config directory for Navigator."""
    return Path(platformdirs.user_config_dir("navigator"))


def get_data_dir() -> Path:
    """Return the XDG-compliant data directory for Navigator."""
    return Path(platformdirs.user_data_dir("navigator"))


def get_config_path() -> Path:
    """Return the path to the Navigator config file."""
    return get_config_dir() / "config.toml"


def resolve_path(path: str | Path) -> Path:
    """Expand ~ and resolve a path to absolute.

    Used at registration time to prevent stale crontab references (INFRA-07).
    """
    return Path(path).expanduser().resolve()


class NavigatorConfig(BaseModel):
    """Navigator configuration model with sensible defaults."""

    db_path: Path = Field(default_factory=lambda: get_data_dir() / "registry.db")
    log_dir: Path = Field(default_factory=lambda: get_data_dir() / "logs")
    secrets_base_path: Path = Field(default_factory=lambda: Path.home() / ".secrets" / "navigator")
    default_retry_count: int = 3
    default_timeout: int = 300

    def resolve_paths(self) -> None:
        """Resolve all path fields to absolute paths."""
        self.db_path = resolve_path(self.db_path)
        self.log_dir = resolve_path(self.log_dir)
        self.secrets_base_path = resolve_path(self.secrets_base_path)


def load_config() -> NavigatorConfig:
    """Load config from TOML file, creating defaults on first run.

    - If config file exists: reads it and constructs NavigatorConfig
    - If not: creates NavigatorConfig with defaults, writes to TOML
    - Always resolves all paths to absolute before returning
    """
    config_path = get_config_path()

    if config_path.exists():
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        config = NavigatorConfig(**data)
    else:
        config = NavigatorConfig()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = config.model_dump(mode="json")
        with open(config_path, "wb") as f:
            tomli_w.dump(data, f)

    config.resolve_paths()
    return config
