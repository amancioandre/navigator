"""Unit tests for Navigator scheduler (CrontabManager)."""

from __future__ import annotations

import fcntl
import threading
import time
from pathlib import Path

import pytest
from crontab import CronTab

from navigator.scheduler import COMMENT_PREFIX, CrontabManager


@pytest.fixture()
def crontab_env(tmp_path, monkeypatch):
    """Set up mock crontab environment for scheduler tests."""
    tab_file = tmp_path / "crontab"
    tab_file.write_text("")
    lock_path = tmp_path / "crontab.lock"

    # Monkeypatch CronTab in scheduler module to use tabfile
    monkeypatch.setattr(
        "navigator.scheduler.CronTab",
        lambda **kw: CronTab(tabfile=str(tab_file)),
    )
    monkeypatch.setattr(
        "navigator.scheduler.shutil",
        type("shutil", (), {"which": staticmethod(lambda cmd: "/usr/local/bin/navigator")}),
    )

    manager = CrontabManager(lock_path=lock_path)
    return {"manager": manager, "tab_file": tab_file, "lock_path": lock_path, "tmp_path": tmp_path}


def _read_tab(tab_file: Path) -> CronTab:
    """Read back the crontab from the test tab file."""
    return CronTab(tabfile=str(tab_file))


class TestSchedule:
    """Tests for CrontabManager.schedule()."""

    def test_schedule_creates_tagged_entry(self, crontab_env):
        """schedule() creates a crontab entry with navigator:cmd_name comment."""
        mgr = crontab_env["manager"]
        mgr.schedule("test-cmd", "*/5 * * * *")

        cron = _read_tab(crontab_env["tab_file"])
        jobs = list(cron.find_comment(f"{COMMENT_PREFIX}:test-cmd"))
        assert len(jobs) == 1
        assert str(jobs[0].slices) == "*/5 * * * *"

    def test_schedule_uses_absolute_navigator_path(self, crontab_env):
        """Entry command starts with absolute path from shutil.which."""
        mgr = crontab_env["manager"]
        mgr.schedule("path-cmd", "0 * * * *")

        cron = _read_tab(crontab_env["tab_file"])
        jobs = list(cron.find_comment(f"{COMMENT_PREFIX}:path-cmd"))
        assert len(jobs) == 1
        assert str(jobs[0].command).startswith("/usr/local/bin/navigator")

    def test_schedule_idempotent_update(self, crontab_env):
        """Scheduling same command twice replaces rather than duplicates."""
        mgr = crontab_env["manager"]
        mgr.schedule("idempotent-cmd", "0 * * * *")
        mgr.schedule("idempotent-cmd", "*/10 * * * *")

        cron = _read_tab(crontab_env["tab_file"])
        jobs = list(cron.find_comment(f"{COMMENT_PREFIX}:idempotent-cmd"))
        assert len(jobs) == 1
        assert str(jobs[0].slices) == "*/10 * * * *"

    def test_schedule_invalid_cron_raises(self, crontab_env):
        """Invalid cron expression raises ValueError with descriptive message."""
        mgr = crontab_env["manager"]
        with pytest.raises(ValueError, match="Invalid cron expression"):
            mgr.schedule("bad-cmd", "not a cron expression")


class TestUnschedule:
    """Tests for CrontabManager.unschedule()."""

    def test_unschedule_removes_entry(self, crontab_env):
        """unschedule() removes the tagged entry, returns True."""
        mgr = crontab_env["manager"]
        mgr.schedule("remove-cmd", "0 * * * *")

        result = mgr.unschedule("remove-cmd")
        assert result is True

        cron = _read_tab(crontab_env["tab_file"])
        jobs = list(cron.find_comment(f"{COMMENT_PREFIX}:remove-cmd"))
        assert len(jobs) == 0

    def test_unschedule_nonexistent_returns_false(self, crontab_env):
        """unschedule() for unknown command returns False."""
        mgr = crontab_env["manager"]
        result = mgr.unschedule("nonexistent-cmd")
        assert result is False


class TestListSchedules:
    """Tests for CrontabManager.list_schedules()."""

    def test_list_schedules_returns_all_navigator_entries(self, crontab_env):
        """list_schedules() returns only navigator-prefixed entries."""
        mgr = crontab_env["manager"]
        mgr.schedule("cmd-a", "0 * * * *")
        mgr.schedule("cmd-b", "*/5 * * * *")

        schedules = mgr.list_schedules()
        names = {s["command"] for s in schedules}
        assert names == {"cmd-a", "cmd-b"}
        assert all(s["enabled"] == "True" for s in schedules)

    def test_list_schedules_empty(self, crontab_env):
        """list_schedules() returns empty list when no entries."""
        mgr = crontab_env["manager"]
        assert mgr.list_schedules() == []


class TestVerifyAfterWrite:
    """Tests for post-write verification (D-11)."""

    def test_verify_after_write(self, crontab_env):
        """schedule() verifies entry exists after writing."""
        mgr = crontab_env["manager"]
        # If verification passes, schedule completes without error
        mgr.schedule("verify-cmd", "0 * * * *")
        # Entry must exist
        cron = _read_tab(crontab_env["tab_file"])
        assert len(list(cron.find_comment(f"{COMMENT_PREFIX}:verify-cmd"))) == 1


class TestLocking:
    """Tests for file locking behavior."""

    def test_lock_timeout_raises(self, crontab_env, monkeypatch):
        """When lock is held, second attempt raises TimeoutError."""
        lock_path = crontab_env["lock_path"]
        mgr = crontab_env["manager"]

        # Hold the lock externally
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_fd = open(lock_path, "w")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

        # Monkeypatch the timeout to 1 second to avoid slow test
        original_lock = CrontabManager._lock

        from contextlib import contextmanager

        @contextmanager
        def fast_lock(self):
            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            fd = open(self.lock_path, "w")  # noqa: SIM115
            deadline = time.monotonic() + 1  # 1s instead of 10s
            acquired = False
            try:
                while True:
                    try:
                        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        acquired = True
                        break
                    except BlockingIOError:
                        if time.monotonic() >= deadline:
                            msg = (
                                "Could not acquire crontab lock within 10 seconds. "
                                "Another navigator process may be modifying the crontab."
                            )
                            raise TimeoutError(msg) from None
                        time.sleep(0.05)
                yield
            finally:
                if acquired:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                fd.close()

        monkeypatch.setattr(CrontabManager, "_lock", fast_lock)

        try:
            with pytest.raises(TimeoutError, match="Could not acquire crontab lock"):
                mgr.schedule("locked-cmd", "0 * * * *")
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()


class TestNavigatorPath:
    """Tests for navigator binary resolution."""

    def test_navigator_not_on_path_raises(self, tmp_path, monkeypatch):
        """When shutil.which returns None, schedule raises FileNotFoundError."""
        monkeypatch.setattr(
            "navigator.scheduler.shutil",
            type("shutil", (), {"which": staticmethod(lambda cmd: None)}),
        )
        monkeypatch.setattr(
            "navigator.scheduler.CronTab",
            lambda **kw: CronTab(tab=""),
        )

        mgr = CrontabManager(lock_path=tmp_path / "crontab.lock")
        with pytest.raises(FileNotFoundError, match="navigator CLI not found on PATH"):
            mgr.schedule("no-nav-cmd", "0 * * * *")
