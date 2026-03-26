# Phase 5: Cron Scheduling - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver cron-based scheduling — users can schedule registered commands to run automatically via the real system crontab. Navigator creates tagged crontab entries that invoke `navigator exec`, supports concurrent access with file locking, and provides CLI operations for scheduling, unscheduling, and listing schedules.

</domain>

<decisions>
## Implementation Decisions

### Crontab Entry Format
- **D-01:** Tag format: `# navigator:<command_name>` as a comment line immediately before the cron entry. Greppable for management.
- **D-02:** Cron command: `navigator exec <command_name>` — uses existing exec subcommand, works without daemon running.
- **D-03:** Use `python-crontab` library for crontab CRUD — no manual parsing of crontab files.
- **D-04:** Validate cron expressions via python-crontab before writing — reject invalid expressions with clear error.

### File Locking
- **D-05:** Lock mechanism: `fcntl.flock` on a dedicated lock file at `{config.data_dir}/crontab.lock`.
- **D-06:** Lock timeout: 10 seconds, error with clear message if lock can't be acquired.
- **D-07:** Lock scope: entire read-modify-write cycle — atomic crontab operations.

### Schedule CLI UX
- **D-08:** Schedule syntax: `navigator schedule <command> --cron "*/5 * * * *"` — cron expression as quoted string option.
- **D-09:** Unschedule: `navigator schedule <command> --remove` — same subcommand, flag-based.
- **D-10:** List schedules: `navigator schedule --list` — shows all scheduled commands with cron expressions as Rich table.
- **D-11:** Verify after write: re-read crontab and confirm the entry exists after writing.

### Claude's Discretion
- Internal module organization (single `scheduler.py` or separate `crontab_manager.py`)
- Whether to store schedule info in the SQLite registry alongside command records
- python-crontab API usage patterns and error handling
- Test strategy for crontab operations (mock vs real crontab in temp environment)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project
- `.planning/PROJECT.md` — Core value, constraints (must use real system crontab)
- `.planning/REQUIREMENTS.md` — SCHED-01 through SCHED-05

### Prior Phases
- `.planning/phases/02-command-registry/02-CONTEXT.md` — Command model, DB layer
- `.planning/phases/04-execution-hardening/04-CONTEXT.md` — Executor with retry/timeout
- `src/navigator/executor.py` — execute_command() that crontab entries will invoke
- `src/navigator/config.py` — NavigatorConfig with data_dir for lock file location

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/navigator/db.py` — get_command_by_name() for validating command exists before scheduling
- `src/navigator/config.py` — NavigatorConfig.data_dir for lock file, load_config()
- `src/navigator/cli.py` — schedule() stub exists, Rich Console/Table patterns established

### Established Patterns
- Lazy imports inside CLI functions
- Rich Console/Table for output
- Pydantic models for data validation
- TDD approach

### Integration Points
- `src/navigator/cli.py:schedule()` — stub exists, needs implementation
- `src/navigator/db.py` — validate command exists before scheduling
- System crontab — real external resource, needs careful testing strategy

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

*Phase: 05-cron-scheduling*
*Context gathered: 2026-03-24*
