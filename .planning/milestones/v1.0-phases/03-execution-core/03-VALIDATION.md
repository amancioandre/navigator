---
phase: 3
slug: execution-core
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 3 — Validation Strategy

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
| 03-01-01 | 01 | 1 | EXEC-01, EXEC-07 | unit | `uv run pytest tests/test_executor.py -v && uv run ruff check src/navigator/executor.py` | TDD | pending |
| 03-01-02 | 01 | 1 | EXEC-02, EXEC-03 | unit | `uv run pytest tests/test_secrets.py -v && uv run ruff check src/navigator/secrets.py` | TDD | pending |
| 03-02-01 | 02 | 2 | EXEC-01..03, EXEC-07, EXEC-08 | integration | `uv run pytest tests/test_cli_exec.py -v && uv run ruff check src/navigator/cli.py` | TDD | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_executor.py` — stubs for subprocess execution, env isolation
- [ ] `tests/test_secrets.py` — stubs for .env loading, secret filtering
- [ ] `tests/test_cli_exec.py` — stubs for exec CLI integration
- [ ] `tests/conftest.py` — updated with executor fixtures (tmp secrets files, mock subprocess)

*Existing infrastructure covers pytest framework from Phase 1.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Secrets not in `ps` output | EXEC-03 | Requires running process inspection | Run `navigator exec test-cmd`, check `ps aux` does not show secret values |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] Ruff linting included in all verify commands
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
