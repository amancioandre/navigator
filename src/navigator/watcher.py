"""Navigator watcher manager -- CRUD and daemon orchestration for file watchers.

Provides WatcherManager with high-level operations for registering, removing,
and listing file watchers. Each method opens its own DB connection for thread safety.
"""

from __future__ import annotations

import logging
from pathlib import Path

from navigator.config import NavigatorConfig
from navigator.db import (
    delete_watcher,
    delete_watchers_for_command,
    get_active_watchers,
    get_command_by_name,
    get_connection,
    get_watchers_for_command,
    init_db,
    insert_watcher,
)
from navigator.models import Watcher

logger = logging.getLogger(__name__)


def run_daemon(config: NavigatorConfig) -> None:
    """Start the watcher daemon -- monitors all active watchers for file changes.

    Creates a single watchdog Observer, schedules a DebouncedHandler per active
    watcher, and blocks until Ctrl+C. This is a foreground process; systemd
    integration comes in Phase 9.
    """
    from watchdog.observers import Observer

    from navigator.watcher_handler import (
        DebouncedHandler,
        SelfTriggerGuard,
        make_trigger_callback,
    )

    manager = WatcherManager(config)
    watchers = manager.get_active_watchers()

    if not watchers:
        logger.info("No active watchers found. Nothing to monitor.")
        return

    observer = Observer()

    for watcher in watchers:
        guard = SelfTriggerGuard()
        callback = make_trigger_callback(watcher, config, guard)
        handler = DebouncedHandler(
            callback=callback,
            debounce_seconds=watcher.debounce_ms / 1000.0,
            patterns=watcher.patterns,
            ignore_patterns=watcher.ignore_patterns,
        )
        observer.schedule(handler, str(watcher.watch_path), recursive=watcher.recursive)
        logger.info(
            "Watching %s for command '%s'", watcher.watch_path, watcher.command_name
        )

    observer.start()
    logger.info(
        "Watcher daemon started. Monitoring %d watcher(s). Press Ctrl+C to stop.",
        len(watchers),
    )

    try:
        while observer.is_alive():
            observer.join(timeout=1)
    except KeyboardInterrupt:
        logger.info("Shutting down watcher daemon...")
        observer.stop()

    observer.join()


class WatcherManager:
    """Manages watcher CRUD operations against the SQLite database.

    Each method opens a fresh connection for thread safety (per research Pitfall 5).
    """

    def __init__(self, config: NavigatorConfig) -> None:
        self._config = config

    def _get_conn(self):
        """Open a fresh connection with initialized schema."""
        conn = get_connection(self._config.db_path)
        init_db(conn)
        return conn

    def register_watcher(
        self,
        command_name: str,
        watch_path: Path,
        patterns: list[str] | None = None,
        ignore_patterns: list[str] | None = None,
        debounce_ms: int = 500,
        active_hours: str | None = None,
        recursive: bool = True,
    ) -> Watcher:
        """Register a new watcher for an existing active command.

        Raises:
            ValueError: If command does not exist or is not active.
        """
        conn = self._get_conn()
        try:
            cmd = get_command_by_name(conn, command_name)
            if cmd is None:
                msg = f"Command '{command_name}' not found"
                raise ValueError(msg)
            if cmd.status != "active":
                msg = f"Command '{command_name}' is not active (status: {cmd.status})"
                raise ValueError(msg)

            kwargs: dict = {
                "command_name": command_name,
                "watch_path": watch_path,
                "debounce_ms": debounce_ms,
                "active_hours": active_hours,
                "recursive": recursive,
            }
            if patterns is not None:
                kwargs["patterns"] = patterns
            if ignore_patterns is not None:
                kwargs["ignore_patterns"] = ignore_patterns

            watcher = Watcher(**kwargs)
            insert_watcher(conn, watcher)
            return watcher
        finally:
            conn.close()

    def remove_watcher(self, watcher_id: str) -> bool:
        """Remove a watcher by id. Returns True if found and deleted."""
        conn = self._get_conn()
        try:
            return delete_watcher(conn, watcher_id) > 0
        finally:
            conn.close()

    def remove_watchers_for_command(self, command_name: str) -> int:
        """Remove all watchers for a command. Returns count of deleted watchers."""
        conn = self._get_conn()
        try:
            return delete_watchers_for_command(conn, command_name)
        finally:
            conn.close()

    def list_watchers(self, command_name: str | None = None) -> list[Watcher]:
        """List watchers, optionally filtered by command name."""
        conn = self._get_conn()
        try:
            if command_name is not None:
                return get_watchers_for_command(conn, command_name)
            return get_active_watchers(conn)
        finally:
            conn.close()

    def get_active_watchers(self) -> list[Watcher]:
        """Return only active watchers."""
        conn = self._get_conn()
        try:
            return get_active_watchers(conn)
        finally:
            conn.close()
