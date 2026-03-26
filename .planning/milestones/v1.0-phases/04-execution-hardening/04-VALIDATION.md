---
phase: 4
slug: execution-hardening
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 4 — Validation Strategy

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
| **Estimated runtime** | ~8 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q && uv run ruff check src/navigator/`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 8 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | EXEC-05 | unit | `uv run pytest tests/test_execution_logger.py -v && uv run ruff check src/navigator/execution_logger.py` | TDD | pending |
| 04-01-02 | 01 | 1 | EXEC-04, EXEC-09, EXEC-10 | unit | `uv run pytest tests/test_executor.py -v && uv run ruff check src/navigator/executor.py` | TDD | pending |
| 04-02-01 | 02 | 2 | EXEC-04, EXEC-06, EXEC-10 | integration | `uv run pytest tests/test_cli.py -v && uv run ruff check src/navigator/cli.py` | TDD | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_execution_logger.py` — stubs for log writing, log listing, log reading
- [ ] `tests/test_executor.py` — updated stubs for retry, timeout, process group tests
- [ ] `tests/test_cli.py` — updated stubs for exec --timeout/--retries, logs subcommand

*Existing infrastructure covers pytest framework from Phase 1.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| No zombie processes after timeout | EXEC-09 | Requires long-running process + ps inspection | Start a long command, timeout, check `ps` for orphans |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 8s
- [ ] Ruff linting included in all verify commands
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
