"""Navigator watcher event handler -- debounce, guard, time window, and trigger logic.

Provides DebouncedHandler (watchdog PatternMatchingEventHandler with debounce),
SelfTriggerGuard (prevents re-entry during execution), time window utilities,
and make_trigger_callback that wires all guards together with the executor.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from datetime import time as dt_time
from typing import TYPE_CHECKING, Callable

from watchdog.events import PatternMatchingEventHandler

from navigator.db import get_command_by_name, get_connection, init_db
from navigator.executor import execute_command

if TYPE_CHECKING:
    from watchdog.events import FileSystemEvent

    from navigator.config import NavigatorConfig
    from navigator.models import Watcher

logger = logging.getLogger(__name__)


def parse_time_window(window_str: str) -> tuple[dt_time, dt_time]:
    """Parse a time window string 'HH:MM-HH:MM' into (start, end) time objects.

    Raises:
        ValueError: If the format is invalid or times cannot be parsed.
    """
    if "-" not in window_str:
        msg = f"Time window must be in HH:MM-HH:MM format, got '{window_str}'"
        raise ValueError(msg)

    parts = window_str.split("-")
    if len(parts) != 2:
        msg = f"Time window must be in HH:MM-HH:MM format, got '{window_str}'"
        raise ValueError(msg)

    start_str, end_str = parts

    try:
        start_parts = start_str.split(":")
        start = dt_time(int(start_parts[0]), int(start_parts[1]))
    except (ValueError, IndexError) as e:
        msg = f"Invalid start time '{start_str}': {e}"
        raise ValueError(msg) from e

    try:
        end_parts = end_str.split(":")
        end = dt_time(int(end_parts[0]), int(end_parts[1]))
    except (ValueError, IndexError) as e:
        msg = f"Invalid end time '{end_str}': {e}"
        raise ValueError(msg) from e

    return (start, end)


def is_within_window(window_str: str | None) -> bool:
    """Check if the current time is within the given time window.

    Returns True if window_str is None (always active).
    For normal ranges (start <= end): checks start <= now <= end.
    For overnight ranges (start > end): checks now >= start or now <= end.
    """
    if window_str is None:
        return True

    start, end = parse_time_window(window_str)
    now = datetime.now().time()

    if start <= end:
        # Normal day range: 09:00-17:00
        return start <= now <= end
    else:
        # Overnight range: 22:00-06:00
        return now >= start or now <= end


class SelfTriggerGuard:
    """Thread-safe guard to prevent re-triggering during command execution.

    Per D-07: blocks events while command is executing to avoid self-triggering
    when the command itself modifies watched files.
    """

    def __init__(self) -> None:
        self._executing = False
        self._lock = threading.Lock()

    @property
    def is_executing(self) -> bool:
        """Return whether a command is currently executing."""
        with self._lock:
            return self._executing

    def set_executing(self, value: bool) -> None:
        """Set the executing state."""
        with self._lock:
            self._executing = value


class DebouncedHandler(PatternMatchingEventHandler):
    """Watchdog event handler that debounces rapid filesystem events.

    Per D-05, D-06: Collects rapid-fire events and fires the callback once
    after a quiet period (debounce_seconds). Skips directory modified events
    which are noisy on Linux inotify.
    """

    def __init__(
        self,
        callback: Callable[[], None],
        debounce_seconds: float,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._callback = callback
        self._debounce_seconds = debounce_seconds
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def on_any_event(self, event: FileSystemEvent) -> None:
        """Handle any filesystem event with debounce logic.

        Skips directory modified events (noisy on Linux).
        Resets the debounce timer on each new event.
        """
        # Skip noisy directory modified events
        if event.is_directory and event.event_type == "modified":
            return

        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce_seconds, self._fire)
            self._timer.daemon = True
            self._timer.start()

    def _fire(self) -> None:
        """Fire the callback after the debounce quiet period."""
        self._callback()


def make_trigger_callback(
    watcher: Watcher,
    config: NavigatorConfig,
    guard: SelfTriggerGuard,
) -> Callable[[], None]:
    """Create a trigger callback that wires guard, time window, and executor.

    Returns a closure that:
    1. Checks guard.is_executing -- skips if True (D-07)
    2. Checks is_within_window -- skips if False (D-10)
    3. Loads command from DB (fresh connection for thread safety)
    4. Skips if command is None or paused
    5. Sets guard, calls execute_command, unsets guard in finally
    """

    def trigger() -> None:
        # Check guard
        if guard.is_executing:
            logger.debug(
                "Skipping trigger for '%s' -- command already executing",
                watcher.command_name,
            )
            return

        # Check time window
        if not is_within_window(watcher.active_hours):
            logger.debug(
                "Skipping trigger for '%s' -- outside active hours '%s'",
                watcher.command_name,
                watcher.active_hours,
            )
            return

        # Load command from DB (fresh connection for thread safety)
        conn = get_connection(config.db_path)
        try:
            init_db(conn)
            cmd = get_command_by_name(conn, watcher.command_name)
        finally:
            conn.close()

        if cmd is None:
            logger.debug(
                "Skipping trigger -- command '%s' not found",
                watcher.command_name,
            )
            return

        if cmd.status != "active":
            logger.debug(
                "Skipping trigger -- command '%s' is %s",
                watcher.command_name,
                cmd.status,
            )
            return

        # Execute
        guard.set_executing(True)
        try:
            logger.info("Triggering command '%s' from watcher", watcher.command_name)
            execute_command(cmd, config)
        except Exception:
            logger.exception(
                "Error executing command '%s' from watcher", watcher.command_name
            )
        finally:
            guard.set_executing(False)

    return trigger
