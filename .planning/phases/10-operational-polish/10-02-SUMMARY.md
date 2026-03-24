---
phase: 10-operational-polish
plan: 02
subsystem: infra
tags: [health-check, diagnostics, cli, auto-fix]

requires:
  - phase: 10-operational-polish-01
    provides: JSON output infrastructure (output.py, is_json, json_response)
provides:
  - "navigator doctor health-check command with 5 checks"
  - "auto-fix for missing directories and stale crontab entries"
  - "JSON output support for doctor command"
  - "DoctorResult/CheckResult dataclasses for structured diagnostics"
affects: []

tech-stack:
  added: []
  patterns: [health-check-pattern, auto-fix-pattern]

key-files:
  created: [src/navigator/doctor.py, tests/test_doctor.py]
  modified: [src/navigator/cli.py, tests/test_cli.py]

key-decisions:
  - "Lazy imports inside check functions for consistent codebase pattern"
  - "Patch at source module level for lazy-import monkeypatch compatibility in tests"

patterns-established:
  - "Health check pattern: individual _check_* functions returning CheckResult, aggregated by run_doctor"
  - "Auto-fix pattern: _apply_fixes iterates fixable checks, applies safe-only remediations"

requirements-completed: [INFRA-03, INFRA-04]

duration: 4min
completed: 2026-03-24
---

# Phase 10 Plan 02: Doctor Health-Check Command Summary

**Self-diagnosable Navigator with 5 health checks (DB, binary, paths, crontab, service), --fix auto-remediation, and JSON output**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-24T22:09:05Z
- **Completed:** 2026-03-24T22:14:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Doctor module with 5 health checks: database connectivity, navigator binary on PATH, registered command paths, crontab sync, systemd service status
- Auto-fix capability: recreates missing log/data directories, removes stale crontab entries
- Full CLI integration with Rich color-coded output (PASS/FAIL/WARN) and JSON output via --output json
- Exit code 1 when any check fails, 0 otherwise -- scriptable by Claude Code agents
- 21 tests covering all check functions, fix behavior, and CLI integration

## Task Commits

Each task was committed atomically:

1. **Task 1: Create doctor module with health checks** - `63c5c4b` (feat)
2. **Task 2: Wire doctor command in CLI with --fix and JSON output** - `e4eeb72` (feat)

## Files Created/Modified
- `src/navigator/doctor.py` - Health check module with CheckResult/DoctorResult dataclasses and 5 check functions
- `tests/test_doctor.py` - 17 unit tests for doctor module
- `src/navigator/cli.py` - Replaced doctor stub with full implementation including --fix flag and JSON output
- `tests/test_cli.py` - 4 CLI integration tests for doctor command

## Decisions Made
- Lazy imports inside each check function following established codebase pattern (Phase 02 decision)
- Patch at source module level (navigator.scheduler.CrontabManager, navigator.service.get_service_path) for lazy-import monkeypatch compatibility in tests
- DoctorResult.summary as @property for computed aggregation without stale state

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed mock patch paths for lazy imports**
- **Found during:** Task 1 (test implementation)
- **Issue:** Tests patched `navigator.doctor.CrontabManager` but CrontabManager is lazy-imported inside functions, not a module-level attribute
- **Fix:** Changed patch targets to source modules (navigator.scheduler.CrontabManager, navigator.service.get_service_path)
- **Files modified:** tests/test_doctor.py
- **Verification:** All 17 tests pass
- **Committed in:** 63c5c4b (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Necessary for test correctness. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 10 complete: both operational polish plans (JSON output + doctor) delivered
- Navigator is fully self-diagnosable via `navigator doctor`
- All 127 tests pass across doctor and CLI test suites

---
*Phase: 10-operational-polish*
*Completed: 2026-03-24*
