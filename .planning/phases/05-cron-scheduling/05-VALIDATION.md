---
phase: 5
slug: cron-scheduling
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 5 — Validation Strategy

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
| 05-01-01 | 01 | 1 | SCHED-01..05 | unit | `uv run pytest tests/test_scheduler.py -v && uv run ruff check src/navigator/scheduler.py` | TDD | pending |
| 05-02-01 | 02 | 2 | SCHED-01..03 | integration | `uv run pytest tests/test_cli.py -v && uv run ruff check src/navigator/cli.py` | TDD | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_scheduler.py` — stubs for crontab CRUD, locking, validation
- [ ] `tests/test_cli.py` — updated stubs for schedule command

*Existing infrastructure covers pytest framework from Phase 1.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real crontab entry appears | SCHED-02 | Requires system crontab inspection | Run `navigator schedule test --cron "0 * * * *"`, check `crontab -l` |

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
