"""Navigator chain execution engine -- sequential command chaining with cycle detection.

Provides walk_chain for resolving chain links, detect_cycle for safety checks,
and execute_chain for running command chains with correlation IDs and failure semantics.
"""

from __future__ import annotations

import logging
import sqlite3
import uuid
from dataclasses import dataclass, field

from navigator.config import NavigatorConfig
from navigator.db import get_command_by_name
from navigator.executor import ExecutionResult, execute_command
from navigator.models import Command
from navigator.namespace import parse_qualified_name

logger = logging.getLogger(__name__)


@dataclass
class ChainResult:
    """Result of executing a command chain."""

    correlation_id: str
    results: list[ExecutionResult] = field(default_factory=list)
    success: bool = True
    steps_run: int = 0
    total_steps: int = 0


def walk_chain(
    conn: sqlite3.Connection,
    start_name: str,
    max_depth: int = 10,
) -> list[Command]:
    """Walk a chain of commands starting from start_name.

    Follows chain_next links via get_command_by_name, resolving cross-namespace
    names via parse_qualified_name. Raises ValueError if chain exceeds max_depth.
    """
    commands: list[Command] = []
    current_name: str | None = start_name

    while current_name is not None:
        if len(commands) >= max_depth:
            msg = f"Chain depth limit exceeded: {max_depth}"
            raise ValueError(msg)

        # Resolve cross-namespace names
        _ns, bare_name = parse_qualified_name(current_name)
        cmd = get_command_by_name(conn, bare_name)
        if cmd is None:
            msg = f"Command not found in chain: {current_name}"
            raise ValueError(msg)

        commands.append(cmd)
        current_name = cmd.chain_next

    return commands


def detect_cycle(
    conn: sqlite3.Connection,
    from_name: str,
    to_name: str,
) -> bool:
    """Check if adding a link from_name -> to_name would create a cycle.

    Returns True if:
    - from_name == to_name (self-link)
    - Walking from to_name eventually reaches from_name
    """
    if from_name == to_name:
        return True

    # Walk from to_name following chain_next links
    current_name: str | None = to_name
    visited: set[str] = set()

    while current_name is not None:
        if current_name in visited:
            break  # already a cycle in existing data, stop
        visited.add(current_name)

        _ns, bare_name = parse_qualified_name(current_name)
        cmd = get_command_by_name(conn, bare_name)
        if cmd is None:
            break

        next_name = cmd.chain_next
        if next_name is not None:
            _ns, next_bare = parse_qualified_name(next_name)
            if next_bare == from_name:
                return True
        current_name = next_name

    return False


def execute_chain(
    conn: sqlite3.Connection,
    start_cmd: Command,
    config: NavigatorConfig,
) -> ChainResult:
    """Execute a chain of commands sequentially with correlation ID tracking.

    Generates a UUID4 correlation_id passed as NAVIGATOR_CHAIN_ID to each step.
    Stops on first failure unless the failed command has on_failure_continue=True.
    """
    correlation_id = str(uuid.uuid4())
    chain = walk_chain(conn, start_cmd.name, config.max_chain_depth)
    extra_env = {"NAVIGATOR_CHAIN_ID": correlation_id}

    result = ChainResult(
        correlation_id=correlation_id,
        total_steps=len(chain),
    )

    logger.info(
        "Starting chain execution [%s]: %d steps, correlation_id=%s",
        start_cmd.name,
        len(chain),
        correlation_id,
    )

    all_succeeded = True

    for cmd in chain:
        logger.info("Chain [%s] step: %s", correlation_id, cmd.name)

        step_result = execute_command(cmd, config, extra_env=extra_env)
        result.results.append(step_result)
        result.steps_run += 1

        if step_result.returncode != 0:
            all_succeeded = False
            logger.warning(
                "Chain [%s] step '%s' failed with code %d",
                correlation_id,
                cmd.name,
                step_result.returncode,
            )
            if not cmd.on_failure_continue:
                logger.info("Chain [%s] stopping on failure (on_failure_continue=False)", correlation_id)
                break
            logger.info("Chain [%s] continuing past failure (on_failure_continue=True)", correlation_id)

    result.success = all_succeeded

    logger.info(
        "Chain [%s] complete: %d/%d steps, success=%s",
        correlation_id,
        result.steps_run,
        result.total_steps,
        result.success,
    )

    return result
