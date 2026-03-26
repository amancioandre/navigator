# Phase 10: Operational Polish - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver operational introspection — dry-run mode for safe command preview, `navigator doctor` for health verification, and `--output json` for machine-readable output enabling Claude Code agent integration. After this phase, Navigator is fully self-diagnosable and scriptable.

</domain>

<decisions>
## Implementation Decisions

### Dry Run
- **D-01:** `navigator exec <command> --dry-run` flag on existing exec subcommand.
- **D-02:** Shows: command args, environment variable keys (not values), working directory, allowed tools, chain info. Everything except actually running.
- **D-03:** Rich formatted panel in human mode, JSON object in `--output json` mode.

### Doctor Command
- **D-04:** Checks: database integrity (tables exist, queryable), crontab sync (tagged entries match registered scheduled commands), registered paths exist, systemd service status, navigator binary on PATH.
- **D-05:** Output: checklist with pass/fail/warn per check, summary at end. Rich table with green/red/yellow color coding.
- **D-06:** Auto-fix: `navigator doctor --fix` for safe fixes — recreate missing directories, re-sync stale crontab entries. Does not delete data.

### JSON Output
- **D-07:** `--output json` as a global option on the Typer app callback — applies to all subcommands.
- **D-08:** Consistent JSON wrapper: `{"status": "ok"|"error", "data": {...}, "message": "..."}`.
- **D-09:** Supported commands: list, show, logs, schedule --list, watch --list, namespace list, doctor, exec --dry-run.

### Claude's Discretion
- Whether to use a context variable or global state for the output format flag
- How to structure the doctor checks (list of callables, class-based, or simple function)
- Whether `--output json` suppresses Rich output or generates both
- Test approach for JSON output validation (schema check or key presence)
- Whether to add `--output yaml` as a future option

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project
- `.planning/PROJECT.md` — Core value, constraints
- `.planning/REQUIREMENTS.md` — REG-09, INFRA-03, INFRA-04

### Prior Phases
- `src/navigator/cli.py` — All existing CLI commands that need JSON support
- `src/navigator/executor.py` — execute_command() for dry-run preview
- `src/navigator/scheduler.py` — CrontabManager for doctor crontab check
- `src/navigator/service.py` — service_control for doctor service check
- `src/navigator/db.py` — DB functions for doctor integrity check

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/navigator/executor.py` — build_command_args(), build_clean_env() for dry-run display
- `src/navigator/scheduler.py` — CrontabManager.list_schedules() for doctor crontab check
- `src/navigator/service.py` — service_control("status") for doctor service check
- `src/navigator/db.py` — get_all_commands(), get_connection() for doctor DB check
- `src/navigator/config.py` — NavigatorConfig for path verification

### Established Patterns
- Rich Console/Table for human output
- Typer app callback for global options (--version already exists)
- Lazy imports in CLI functions
- Pydantic model serialization (.model_dump())

### Integration Points
- `src/navigator/cli.py:main()` callback — add --output option
- `src/navigator/cli.py:doctor()` — stub exists, needs implementation
- `src/navigator/cli.py:exec_command()` — add --dry-run flag
- All list/show commands — add JSON output path

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

*Phase: 10-operational-polish*
*Context gathered: 2026-03-24*
