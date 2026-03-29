"""Tests for Navigator execution logger."""

from __future__ import annotations

import time
from pathlib import Path

from navigator.execution_logger import (
    LogEntry,
    list_execution_logs,
    read_log_content,
    write_execution_log,
)


class TestWriteExecutionLog:
    """Tests for write_execution_log."""

    def test_write_creates_directory(self, tmp_path: Path) -> None:
        """write_execution_log creates the command subdirectory."""
        log_dir = tmp_path / "logs"
        write_execution_log(log_dir, "my-cmd", 1, 0, 1.23, "out", "err")
        assert (log_dir / "my-cmd").is_dir()

    def test_write_log_content(self, tmp_path: Path) -> None:
        """Log file contains correct header fields and body content."""
        log_path = write_execution_log(
            tmp_path, "test-cmd", 2, 1, 5.67, "hello stdout", "hello stderr"
        )
        text = log_path.read_text()

        assert "command: test-cmd" in text
        assert "attempt: 2" in text
        assert "exit_code: 1" in text
        assert "duration: 5.67s" in text
        assert "timestamp:" in text
        assert "---\n" in text
        assert "hello stdout" in text
        assert "hello stderr" in text

    def test_write_log_filename_format(self, tmp_path: Path) -> None:
        """Log filename matches YYYYMMDDTHHMMSS_{microseconds}Z.log pattern."""
        log_path = write_execution_log(tmp_path, "fmt-cmd", 1, 0, 0.5, "", "")
        name = log_path.name
        # Pattern: 8 digits T 6 digits _ 6 digits Z.log
        assert name.endswith("Z.log")
        assert "T" in name
        assert "_" in name
        parts = name.replace("Z.log", "").split("_")
        assert len(parts) == 2
        assert len(parts[1]) == 6  # microseconds

    def test_list_logs_newest_first(self, tmp_path: Path) -> None:
        """list_execution_logs returns logs in newest-first order."""
        paths = []
        for i in range(3):
            p = write_execution_log(tmp_path, "order-cmd", i, 0, float(i), f"out{i}", "")
            paths.append(p)
            # Small delay to ensure distinct filenames
            time.sleep(0.01)

        entries = list_execution_logs(tmp_path, "order-cmd")
        assert len(entries) == 3
        # Newest (last written) should be first
        assert entries[0].path == paths[-1]
        assert entries[-1].path == paths[0]

    def test_list_logs_respects_count(self, tmp_path: Path) -> None:
        """list_execution_logs returns at most count entries."""
        for i in range(5):
            write_execution_log(tmp_path, "count-cmd", i, 0, 0.1, "", "")
            time.sleep(0.01)

        entries = list_execution_logs(tmp_path, "count-cmd", count=2)
        assert len(entries) == 2

    def test_list_logs_empty_dir(self, tmp_path: Path) -> None:
        """Nonexistent command directory returns empty list."""
        entries = list_execution_logs(tmp_path, "nonexistent-cmd")
        assert entries == []

    def test_read_log_content(self, tmp_path: Path) -> None:
        """read_log_content extracts only the body after the separator."""
        log_path = write_execution_log(
            tmp_path, "read-cmd", 1, 0, 1.0, "body output\n", "body error\n"
        )
        body = read_log_content(log_path)
        assert "body output" in body
        assert "body error" in body
        # Header fields should not be in body
        assert "command:" not in body
        assert "exit_code:" not in body

    def test_rapid_writes_no_collision(self, tmp_path: Path) -> None:
        """Two rapid writes produce two distinct log files."""
        p1 = write_execution_log(tmp_path, "rapid-cmd", 1, 0, 0.1, "a", "")
        p2 = write_execution_log(tmp_path, "rapid-cmd", 2, 0, 0.2, "b", "")
        assert p1 != p2
        assert p1.exists()
        assert p2.exists()
        # Verify content is different
        assert "a" in p1.read_text()
        assert "b" in p2.read_text()


class TestErrorField:
    """Tests for optional error field in execution logs."""

    def test_write_log_with_error_field(self, tmp_path: Path) -> None:
        """write_execution_log with error includes error line in header."""
        log_path = write_execution_log(
            tmp_path, "err-cmd", 1, -1, 0.0, "", "",
            error="FileNotFoundError: /usr/bin/claude",
        )
        text = log_path.read_text()
        header = text.split("---\n", 1)[0]
        assert "error: FileNotFoundError: /usr/bin/claude" in header

    def test_write_log_without_error_field(self, tmp_path: Path) -> None:
        """write_execution_log without error param produces no error line."""
        log_path = write_execution_log(
            tmp_path, "ok-cmd", 1, 0, 1.0, "out", "",
        )
        text = log_path.read_text()
        assert "error:" not in text

    def test_write_log_error_none(self, tmp_path: Path) -> None:
        """write_execution_log with error=None produces no error line."""
        log_path = write_execution_log(
            tmp_path, "ok-cmd", 1, 0, 1.0, "out", "",
            error=None,
        )
        text = log_path.read_text()
        assert "error:" not in text

    def test_list_logs_parses_error_field(self, tmp_path: Path) -> None:
        """list_execution_logs parses error field into LogEntry.error."""
        write_execution_log(
            tmp_path, "parse-cmd", 1, -1, 0.0, "", "",
            error="FileNotFoundError: /usr/bin/claude",
        )
        entries = list_execution_logs(tmp_path, "parse-cmd")
        assert len(entries) == 1
        assert entries[0].error == "FileNotFoundError: /usr/bin/claude"

    def test_list_logs_no_error_field(self, tmp_path: Path) -> None:
        """list_execution_logs returns error=None for logs without error."""
        write_execution_log(tmp_path, "ok-cmd", 1, 0, 1.0, "out", "")
        entries = list_execution_logs(tmp_path, "ok-cmd")
        assert len(entries) == 1
        assert entries[0].error is None
