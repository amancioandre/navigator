---
phase: 01-project-scaffold
plan: 02
subsystem: infra
tags: [pydantic, toml, platformdirs, config, xdg]

# Dependency graph
requires:
  - phase: 01-project-scaffold-01
    provides: "Project structure, pyproject.toml with dependencies, CLI skeleton"
provides:
  - "NavigatorConfig Pydantic model with typed defaults"
  - "load_config() with first-run creation and TOML persistence"
  - "resolve_path() for absolute path resolution (INFRA-07)"
  - "get_config_dir() / get_data_dir() via platformdirs (INFRA-05)"
  - "tmp_config_dir fixture for isolated config testing"
affects: [registry, executor, scheduling, secrets]

# Tech tracking
tech-stack:
  added: [platformdirs, pydantic, tomli-w, tomllib]
  patterns: [pydantic-basemodel-config, xdg-compliant-paths, toml-persistence, monkeypatch-fixture-isolation]

key-files:
  created:
    - src/navigator/config.py
  modified:
    - tests/test_config.py
    - tests/conftest.py

key-decisions:
  - "Path fields use Pydantic Field(default_factory) to defer platformdirs calls"
  - "Config stored in XDG config dir, DB/logs in XDG data dir (mutable vs settings)"
  - "model_dump(mode='json') for TOML serialization — Pydantic v2 converts Path to str"

patterns-established:
  - "Config isolation: tmp_config_dir fixture monkeypatches get_config_dir/get_data_dir"
  - "Path resolution: resolve_path() as canonical utility for all path normalization"

requirements-completed: [INFRA-05, INFRA-07]

# Metrics
duration: 2min
completed: 2026-03-24
---

# Phase 01 Plan 02: Config System Summary

**TOML-based config with Pydantic validation, XDG-compliant paths via platformdirs, and resolve_path() for absolute path normalization**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-24T03:40:14Z
- **Completed:** 2026-03-24T03:41:50Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- NavigatorConfig Pydantic model with db_path, log_dir, secrets_base_path, default_retry_count, default_timeout
- load_config() creates config.toml with defaults on first run, loads existing on subsequent runs
- resolve_path() expands ~ and resolves relative paths to absolute (INFRA-07)
- 8 config tests covering creation, loading, path resolution, defaults, and directory creation
- Full test suite green: 19 tests (11 CLI + 8 config)

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement config module with Pydantic model and TOML persistence** - `d7ae472` (feat)
2. **Task 2: Implement config and path resolution tests** - `15831d6` (test)

## Files Created/Modified
- `src/navigator/config.py` - NavigatorConfig model, load_config(), resolve_path(), get_config_dir/get_data_dir
- `tests/test_config.py` - 8 tests for config creation, loading, path resolution, defaults
- `tests/conftest.py` - Updated tmp_config_dir fixture with proper monkeypatching

## Decisions Made
- Path fields use `Field(default_factory=lambda: ...)` to defer platformdirs calls until instantiation
- Config goes in XDG config dir, DB and logs go in XDG data dir (mutable data vs settings convention)
- `model_dump(mode="json")` for TOML serialization since Pydantic v2 auto-converts Path to str in json mode

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Known Stubs
None - all functionality is fully wired.

## Next Phase Readiness
- Config system complete, ready for registry module to use NavigatorConfig for db_path
- resolve_path() available for command registration path normalization
- tmp_config_dir fixture ready for any test that needs isolated config

## Self-Check: PASSED

All files exist, all commits verified.

---
*Phase: 01-project-scaffold*
*Completed: 2026-03-24*
