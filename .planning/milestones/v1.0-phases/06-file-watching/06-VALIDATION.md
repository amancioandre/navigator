---
phase: 6
slug: file-watching
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 6 — Validation Strategy

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
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q && uv run ruff check src/navigator/`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | WATCH-01 | unit | `uv run pytest tests/test_watcher.py -v && uv run ruff check src/navigator/watcher.py` | TDD | pending |
| 06-01-02 | 01 | 1 | WATCH-02..05 | unit | `uv run pytest tests/test_watcher.py -v && uv run ruff check src/navigator/watcher.py` | TDD | pending |
| 06-02-01 | 02 | 2 | WATCH-01..05 | integration | `uv run pytest tests/test_cli.py -v -k "watch or Watch" && uv run ruff check src/navigator/cli.py` | TDD | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_watcher.py` — stubs for watcher DB, debounce, self-trigger, time windows, ignore patterns
- [ ] `tests/test_cli.py` — updated stubs for watch command

*Existing infrastructure covers pytest framework from Phase 1.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real filesystem watcher triggers | WATCH-01 | Requires real watchdog observer + file system events | Start watcher daemon, touch a file, verify command triggers |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] Ruff linting included in all verify commands
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
