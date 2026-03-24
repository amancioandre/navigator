"""Tests for Navigator watcher handler -- debounce, guard, time window, ignore patterns."""

from __future__ import annotations

import threading
from datetime import time as dt_time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from navigator.models import Command, CommandStatus, Watcher, WatcherStatus
from navigator.watcher_handler import (
    DebouncedHandler,
    SelfTriggerGuard,
    is_within_window,
    make_trigger_callback,
    parse_time_window,
)


class TestParseTimeWindow:
    """Tests for parse_time_window function."""

    def test_normal_range(self):
        start, end = parse_time_window("09:00-17:00")
        assert start == dt_time(9, 0)
        assert end == dt_time(17, 0)

    def test_overnight_range(self):
        start, end = parse_time_window("22:00-06:00")
        assert start == dt_time(22, 0)
        assert end == dt_time(6, 0)

    def test_invalid_input_raises(self):
        with pytest.raises(ValueError):
            parse_time_window("invalid")

    def test_bad_time_values_raise(self):
        with pytest.raises(ValueError):
            parse_time_window("25:00-17:00")


class TestIsWithinWindow:
    """Tests for is_within_window function."""

    def test_none_returns_true(self):
        assert is_within_window(None) is True

    def test_within_normal_range(self):
        """12:00 is within 09:00-17:00."""
        from datetime import datetime

        fake_now = datetime(2026, 1, 1, 12, 0, 0)
        with patch("navigator.watcher_handler.datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert is_within_window("09:00-17:00") is True

    def test_outside_normal_range(self):
        """20:00 is outside 09:00-17:00."""
        from datetime import datetime

        fake_now = datetime(2026, 1, 1, 20, 0, 0)
        with patch("navigator.watcher_handler.datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert is_within_window("09:00-17:00") is False

    def test_overnight_late_night(self):
        """23:00 is within 22:00-06:00."""
        from datetime import datetime

        fake_now = datetime(2026, 1, 1, 23, 0, 0)
        with patch("navigator.watcher_handler.datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert is_within_window("22:00-06:00") is True

    def test_overnight_early_morning(self):
        """03:00 is within 22:00-06:00."""
        from datetime import datetime

        fake_now = datetime(2026, 1, 1, 3, 0, 0)
        with patch("navigator.watcher_handler.datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert is_within_window("22:00-06:00") is True


class TestSelfTriggerGuard:
    """Tests for SelfTriggerGuard."""

    def test_starts_false(self):
        guard = SelfTriggerGuard()
        assert guard.is_executing is False

    def test_set_executing_true(self):
        guard = SelfTriggerGuard()
        guard.set_executing(True)
        assert guard.is_executing is True

    def test_set_executing_false(self):
        guard = SelfTriggerGuard()
        guard.set_executing(True)
        guard.set_executing(False)
        assert guard.is_executing is False


class TestDebouncedHandler:
    """Tests for DebouncedHandler."""

    def test_fires_callback_once_after_debounce(self):
        """Multiple rapid events should result in a single callback."""
        fired = threading.Event()
        call_count = {"n": 0}

        def callback():
            call_count["n"] += 1
            fired.set()

        handler = DebouncedHandler(
            callback=callback,
            debounce_seconds=0.1,
            patterns=["*"],
            ignore_patterns=[],
        )

        # Simulate multiple file events
        event = MagicMock()
        event.is_directory = False
        event.event_type = "modified"

        handler.on_any_event(event)
        handler.on_any_event(event)
        handler.on_any_event(event)

        fired.wait(timeout=2)
        assert call_count["n"] == 1

    def test_resets_timer_on_new_event(self):
        """New events should restart the debounce period."""
        fired = threading.Event()
        call_count = {"n": 0}

        def callback():
            call_count["n"] += 1
            fired.set()

        handler = DebouncedHandler(
            callback=callback,
            debounce_seconds=0.2,
            patterns=["*"],
            ignore_patterns=[],
        )

        event = MagicMock()
        event.is_directory = False
        event.event_type = "modified"

        import time

        handler.on_any_event(event)
        time.sleep(0.1)
        handler.on_any_event(event)  # Reset timer

        # After 0.1s from second event, should not have fired yet
        assert call_count["n"] == 0

        fired.wait(timeout=2)
        assert call_count["n"] == 1

    def test_skips_directory_modified_events(self):
        """Directory modified events should be ignored (noisy on Linux)."""
        fired = threading.Event()

        def callback():
            fired.set()

        handler = DebouncedHandler(
            callback=callback,
            debounce_seconds=0.05,
            patterns=["*"],
            ignore_patterns=[],
        )

        event = MagicMock()
        event.is_directory = True
        event.event_type = "modified"

        handler.on_any_event(event)

        # Should not fire
        assert not fired.wait(timeout=0.2)


class TestMakeTriggerCallback:
    """Tests for make_trigger_callback."""

    def _make_watcher(self, **kwargs):
        defaults = {
            "command_name": "test-cmd",
            "watch_path": Path("/tmp/watched"),
        }
        defaults.update(kwargs)
        return Watcher(**defaults)

    def _make_config(self):
        from navigator.config import NavigatorConfig

        return NavigatorConfig(
            db_path=Path("/tmp/test.db"),
            log_dir=Path("/tmp/logs"),
            secrets_base_path=Path("/tmp/secrets"),
        )

    def test_skips_when_guard_is_executing(self):
        watcher = self._make_watcher()
        config = self._make_config()
        guard = SelfTriggerGuard()
        guard.set_executing(True)

        cb = make_trigger_callback(watcher, config, guard)
        # Should return without calling execute_command
        with patch("navigator.watcher_handler.execute_command") as mock_exec:
            cb()
            mock_exec.assert_not_called()

    def test_skips_when_outside_time_window(self):
        watcher = self._make_watcher(active_hours="09:00-17:00")
        config = self._make_config()
        guard = SelfTriggerGuard()

        cb = make_trigger_callback(watcher, config, guard)
        with (
            patch("navigator.watcher_handler.is_within_window", return_value=False),
            patch("navigator.watcher_handler.execute_command") as mock_exec,
        ):
            cb()
            mock_exec.assert_not_called()

    def test_skips_when_command_is_paused(self):
        watcher = self._make_watcher()
        config = self._make_config()
        guard = SelfTriggerGuard()

        paused_cmd = Command(
            name="test-cmd",
            prompt="test",
            environment=Path("/tmp"),
            status=CommandStatus.PAUSED,
        )

        cb = make_trigger_callback(watcher, config, guard)
        with (
            patch("navigator.watcher_handler.is_within_window", return_value=True),
            patch("navigator.watcher_handler.get_connection") as mock_conn,
            patch("navigator.watcher_handler.init_db"),
            patch("navigator.watcher_handler.get_command_by_name", return_value=paused_cmd),
            patch("navigator.watcher_handler.execute_command") as mock_exec,
        ):
            cb()
            mock_exec.assert_not_called()

    def test_calls_execute_when_all_guards_pass(self):
        watcher = self._make_watcher()
        config = self._make_config()
        guard = SelfTriggerGuard()

        active_cmd = Command(
            name="test-cmd",
            prompt="test",
            environment=Path("/tmp"),
            status=CommandStatus.ACTIVE,
        )

        mock_result = MagicMock()

        cb = make_trigger_callback(watcher, config, guard)
        with (
            patch("navigator.watcher_handler.is_within_window", return_value=True),
            patch("navigator.watcher_handler.get_connection") as mock_conn,
            patch("navigator.watcher_handler.init_db"),
            patch("navigator.watcher_handler.get_command_by_name", return_value=active_cmd),
            patch("navigator.watcher_handler.execute_command", return_value=mock_result) as mock_exec,
        ):
            cb()
            mock_exec.assert_called_once_with(active_cmd, config)
            # Guard should be False after execution
            assert guard.is_executing is False
