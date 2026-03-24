---
phase: 2
slug: command-registry
status: draft
nyquist_compliant: false
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
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | REG-10 | unit | `uv run pytest tests/test_db.py -v` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | REG-01 | unit | `uv run pytest tests/test_models.py -v` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | REG-01 | integration | `uv run pytest tests/test_cli_register.py -v` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | REG-02, REG-08 | integration | `uv run pytest tests/test_cli_list.py -v` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 1 | REG-03 | integration | `uv run pytest tests/test_cli_show.py -v` | ❌ W0 | ⬜ pending |
| 02-02-04 | 02 | 1 | REG-04 | integration | `uv run pytest tests/test_cli_update.py -v` | ❌ W0 | ⬜ pending |
| 02-02-05 | 02 | 1 | REG-05 | integration | `uv run pytest tests/test_cli_delete.py -v` | ❌ W0 | ⬜ pending |
| 02-02-06 | 02 | 1 | REG-06, REG-07 | integration | `uv run pytest tests/test_cli_pause_resume.py -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_db.py` — stubs for REG-10 (SQLite CRUD, atomic writes)
- [ ] `tests/test_models.py` — stubs for Command model validation
- [ ] `tests/test_cli_register.py` — stubs for REG-01 register command
- [ ] `tests/test_cli_list.py` — stubs for REG-02, REG-08 list + sort
- [ ] `tests/test_cli_show.py` — stubs for REG-03 show command
- [ ] `tests/test_cli_update.py` — stubs for REG-04 update command
- [ ] `tests/test_cli_delete.py` — stubs for REG-05 delete command
- [ ] `tests/test_cli_pause_resume.py` — stubs for REG-06, REG-07 pause/resume
- [ ] `tests/conftest.py` — shared fixtures (tmp db, sample commands)

*Existing infrastructure covers pytest framework from Phase 1.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
