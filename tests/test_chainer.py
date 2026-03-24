"""Tests for Navigator chain execution engine -- cycle detection, depth limits, and sequential execution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from navigator.chainer import ChainResult, detect_cycle, execute_chain, walk_chain
from navigator.config import NavigatorConfig
from navigator.db import get_connection, init_db, insert_command
from navigator.executor import ExecutionResult
from navigator.models import Command


@pytest.fixture()
def chain_db(tmp_path):
    """SQLite connection with schema initialized for chain tests."""
    db_path = tmp_path / "chain_test.db"
    conn = get_connection(db_path)
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture()
def chain_config(tmp_path):
    """NavigatorConfig with test paths."""
    return NavigatorConfig(
        db_path=tmp_path / "chain_test.db",
        log_dir=tmp_path / "logs",
        secrets_base_path=tmp_path / "secrets",
        max_chain_depth=10,
    )


def _make_cmd(name: str, chain_next: str | None = None, on_failure_continue: bool = False) -> Command:
    """Helper to create a Command with chain fields."""
    return Command(
        name=name,
        prompt=f"Run {name}",
        environment=Path("/tmp"),
        chain_next=chain_next,
        on_failure_continue=on_failure_continue,
    )


def _mock_result(name: str, returncode: int = 0) -> ExecutionResult:
    """Helper to create a mock ExecutionResult."""
    return ExecutionResult(
        command_name=name,
        returncode=returncode,
        stdout=f"{name} output",
        stderr="",
        attempts=1,
        duration=0.1,
        timed_out=False,
        log_path=None,
    )


class TestWalkChain:
    """Tests for walk_chain function."""

    def test_single_command_no_chain_next(self, chain_db):
        cmd = _make_cmd("solo")
        insert_command(chain_db, cmd)
        result = walk_chain(chain_db, "solo")
        assert len(result) == 1
        assert result[0].name == "solo"

    def test_follows_abc_chain(self, chain_db):
        insert_command(chain_db, _make_cmd("cmd-a", chain_next="cmd-b"))
        insert_command(chain_db, _make_cmd("cmd-b", chain_next="cmd-c"))
        insert_command(chain_db, _make_cmd("cmd-c"))
        result = walk_chain(chain_db, "cmd-a")
        assert [c.name for c in result] == ["cmd-a", "cmd-b", "cmd-c"]

    def test_raises_on_depth_exceeded(self, chain_db):
        insert_command(chain_db, _make_cmd("d1", chain_next="d2"))
        insert_command(chain_db, _make_cmd("d2", chain_next="d3"))
        insert_command(chain_db, _make_cmd("d3"))
        with pytest.raises(ValueError, match="Chain depth limit exceeded"):
            walk_chain(chain_db, "d1", max_depth=2)


class TestDetectCycle:
    """Tests for detect_cycle function."""

    def test_self_link(self, chain_db):
        insert_command(chain_db, _make_cmd("self"))
        assert detect_cycle(chain_db, "self", "self") is True

    def test_indirect_cycle(self, chain_db):
        insert_command(chain_db, _make_cmd("a", chain_next="b"))
        insert_command(chain_db, _make_cmd("b", chain_next="c"))
        insert_command(chain_db, _make_cmd("c"))
        # Adding c->a would create a cycle
        assert detect_cycle(chain_db, "a", "c") is True

    def test_valid_non_cyclic(self, chain_db):
        insert_command(chain_db, _make_cmd("x", chain_next="y"))
        insert_command(chain_db, _make_cmd("y"))
        insert_command(chain_db, _make_cmd("z"))
        # Adding z->x is fine (z is not reachable from x)
        assert detect_cycle(chain_db, "z", "x") is False


class TestExecuteChain:
    """Tests for execute_chain function."""

    @patch("navigator.chainer.execute_command")
    def test_runs_all_steps_sequentially(self, mock_exec, chain_db, chain_config):
        insert_command(chain_db, _make_cmd("step1", chain_next="step2"))
        insert_command(chain_db, _make_cmd("step2", chain_next="step3"))
        insert_command(chain_db, _make_cmd("step3"))

        call_order = []
        def side_effect(cmd, config, extra_env=None):
            call_order.append(cmd.name)
            return _mock_result(cmd.name)

        mock_exec.side_effect = side_effect

        start_cmd = Command(name="step1", prompt="Run step1", environment=Path("/tmp"), chain_next="step2")
        result = execute_chain(chain_db, start_cmd, chain_config)

        assert call_order == ["step1", "step2", "step3"]
        assert result.success is True
        assert result.steps_run == 3
        assert result.total_steps == 3
        assert len(result.results) == 3

    @patch("navigator.chainer.execute_command")
    def test_stops_on_failure(self, mock_exec, chain_db, chain_config):
        insert_command(chain_db, _make_cmd("ok", chain_next="fail"))
        insert_command(chain_db, _make_cmd("fail", chain_next="skip"))
        insert_command(chain_db, _make_cmd("skip"))

        def side_effect(cmd, config, extra_env=None):
            rc = 1 if cmd.name == "fail" else 0
            return _mock_result(cmd.name, returncode=rc)

        mock_exec.side_effect = side_effect

        start_cmd = Command(name="ok", prompt="Run ok", environment=Path("/tmp"), chain_next="fail")
        result = execute_chain(chain_db, start_cmd, chain_config)

        assert result.success is False
        assert result.steps_run == 2  # ok + fail
        assert result.total_steps == 3

    @patch("navigator.chainer.execute_command")
    def test_continues_on_failure_when_flag_set(self, mock_exec, chain_db, chain_config):
        insert_command(chain_db, _make_cmd("ok", chain_next="fail"))
        insert_command(chain_db, _make_cmd("fail", chain_next="after", on_failure_continue=True))
        insert_command(chain_db, _make_cmd("after"))

        def side_effect(cmd, config, extra_env=None):
            rc = 1 if cmd.name == "fail" else 0
            return _mock_result(cmd.name, returncode=rc)

        mock_exec.side_effect = side_effect

        start_cmd = Command(name="ok", prompt="Run ok", environment=Path("/tmp"), chain_next="fail")
        result = execute_chain(chain_db, start_cmd, chain_config)

        assert result.steps_run == 3
        assert result.success is False  # overall still false since a step failed

    @patch("navigator.chainer.execute_command")
    def test_passes_navigator_chain_id(self, mock_exec, chain_db, chain_config):
        insert_command(chain_db, _make_cmd("single"))

        captured_env = {}
        def side_effect(cmd, config, extra_env=None):
            if extra_env:
                captured_env.update(extra_env)
            return _mock_result(cmd.name)

        mock_exec.side_effect = side_effect

        start_cmd = Command(name="single", prompt="Run single", environment=Path("/tmp"))
        result = execute_chain(chain_db, start_cmd, chain_config)

        assert "NAVIGATOR_CHAIN_ID" in captured_env
        assert result.correlation_id == captured_env["NAVIGATOR_CHAIN_ID"]

    @patch("navigator.chainer.execute_command")
    def test_chain_result_has_correlation_id(self, mock_exec, chain_db, chain_config):
        insert_command(chain_db, _make_cmd("only"))
        mock_exec.return_value = _mock_result("only")

        start_cmd = Command(name="only", prompt="Run only", environment=Path("/tmp"))
        result = execute_chain(chain_db, start_cmd, chain_config)

        assert isinstance(result, ChainResult)
        assert result.correlation_id  # non-empty UUID string
        assert len(result.correlation_id) == 36  # UUID4 format
