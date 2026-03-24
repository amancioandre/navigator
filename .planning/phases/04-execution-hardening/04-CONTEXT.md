# Phase 4: Execution Hardening - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Harden the execution engine with retry logic, per-execution logging, timeouts with graceful termination, and clean process lifecycle management. After this phase, failed commands retry automatically, every execution is logged to disk, long-running commands are terminated safely, and child processes never become zombies.

</domain>

<decisions>
## Implementation Decisions

### Retry Strategy
- **D-01:** Exponential backoff formula: `2^attempt * 1s` (1s, 2s, 4s, 8s...).
- **D-02:** Default retry count from `config.default_retry_count` (currently 3) — already in NavigatorConfig.
- **D-03:** Failure = non-zero exit code from subprocess. Simple, universal.
- **D-04:** Log each retry attempt with attempt number and delay before sleeping.

### Execution Logging
- **D-05:** Log directory structure: `{config.log_dir}/{command_name}/{ISO_timestamp}.log`.
- **D-06:** Log file content: combined stdout + stderr with metadata header (command name, timestamp, exit code, duration, attempt number).
- **D-07:** `navigator logs <command>` shows last N log entries as Rich table. `--tail` flag shows full content of last log.
- **D-08:** No automatic log cleanup this phase — future enhancement if needed.

### Timeout Behavior
- **D-09:** Default timeout from `config.default_timeout` (currently 300s/5min) — already in NavigatorConfig.
- **D-10:** Termination signal chain: SIGTERM first, wait 5s grace period, then SIGKILL if still alive.
- **D-11:** Timeout produces exit code 124 (matching the `timeout` command convention), logged to execution log.
- **D-12:** `--timeout` optional flag on `navigator exec` — overrides config default for that execution.

### Process Lifecycle
- **D-13:** Process group isolation via `start_new_session=True` in subprocess.run/Popen — isolates entire child process tree.
- **D-14:** Kill entire process group on timeout/cleanup: `os.killpg(pgid, signal)`.
- **D-15:** Log PID at spawn for targeted cleanup and debugging.
- **D-16:** `atexit` handler + signal handlers (SIGTERM, SIGINT) to kill any active child processes on navigator exit.

### Claude's Discretion
- Whether to refactor executor.py or create separate retry.py / logging.py modules
- Popen vs subprocess.run for timeout support (Popen likely needed for process group + timeout)
- Rich table column design for `navigator logs` output
- Test approach for retry timing (mock time.sleep vs real delays)
- Whether to add `--retries` override flag on `navigator exec` alongside `--timeout`

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project
- `.planning/PROJECT.md` — Core value, constraints
- `.planning/REQUIREMENTS.md` — EXEC-04, EXEC-05, EXEC-06, EXEC-09, EXEC-10

### Prior Phases
- `.planning/phases/03-execution-core/03-CONTEXT.md` — Executor architecture, subprocess invocation, env isolation
- `src/navigator/executor.py` — Current execute_command() that needs hardening
- `src/navigator/config.py` — NavigatorConfig with default_retry_count and default_timeout

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/navigator/executor.py` — `execute_command()`, `build_clean_env()`, `build_command_args()` — needs extension for retry/timeout
- `src/navigator/config.py` — `NavigatorConfig` already has `default_retry_count: int = 3` and `default_timeout: int = 300`
- `src/navigator/cli.py` — `exec_command()` stub for logs, existing exec subcommand to extend with --timeout/--retries

### Established Patterns
- Lazy imports inside CLI command functions (from cli.py)
- Rich Console/Table for output (from cli.py)
- Pydantic models for data (from models.py)
- TDD approach (tests written first or alongside)

### Integration Points
- `src/navigator/executor.py` — Main file to extend with retry, timeout, process group, logging
- `src/navigator/cli.py` — Add --timeout/--retries flags to exec, implement logs subcommand
- `src/navigator/config.py` — Already has the config fields needed

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-execution-hardening*
*Context gathered: 2026-03-24*
