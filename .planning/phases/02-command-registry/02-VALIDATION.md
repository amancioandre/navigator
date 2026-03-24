---
phase: 2
slug: command-registry
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-23
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Lint command** | `uv run ruff check src/navigator/` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q && uv run ruff check src/navigator/`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | REG-01 | unit | `uv run pytest tests/test_models.py -v && uv run ruff check src/navigator/models.py` | TDD | pending |
| 02-01-02 | 01 | 1 | REG-10 | unit | `uv run pytest tests/test_db.py -v && uv run ruff check src/navigator/db.py` | TDD | pending |
| 02-02-01 | 02 | 2 | REG-01..08 | integration | `uv run ruff check tests/test_cli.py` (RED -- tests written, stubs not yet implemented) | TDD | pending |
| 02-02-02 | 02 | 2 | REG-01,02,03,08 | integration | `uv run pytest tests/test_cli.py -v -k "register or list or show" && uv run ruff check src/navigator/cli.py` | yes (Task 1) | pending |
| 02-02-03 | 02 | 2 | REG-04,05,06,07 | integration | `uv run pytest tests/test_cli.py -v && uv run ruff check src/navigator/cli.py` | yes (Task 1) | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_models.py` — stubs for Command model validation (Plan 01 Task 1, TDD)
- [ ] `tests/test_db.py` — stubs for REG-10 (SQLite CRUD, atomic writes) (Plan 01 Task 2, TDD)
- [ ] `tests/test_cli.py` — integration tests for all 7 subcommands (Plan 02 Task 1, TDD RED phase)
- [ ] `tests/conftest.py` — shared fixtures (tmp db, sample commands)

*Existing infrastructure covers pytest framework from Phase 1.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] Ruff linting included in all verify commands
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
