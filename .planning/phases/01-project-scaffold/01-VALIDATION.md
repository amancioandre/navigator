---
phase: 1
slug: project-scaffold
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
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
| 01-01-01 | 01 | 1 | INFRA-01 | integration | `uv run pip install . && navigator --help` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | INFRA-05 | unit | `uv run pytest tests/test_config.py -v` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | INFRA-07 | unit | `uv run pytest tests/test_paths.py -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_cli.py` — stubs for INFRA-01 (CLI entry point, `--help`)
- [ ] `tests/test_config.py` — stubs for INFRA-05 (config creation, defaults)
- [ ] `tests/test_paths.py` — stubs for INFRA-07 (absolute path resolution)
- [ ] `tests/conftest.py` — shared fixtures (tmp config dir, isolated filesystem)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `uv tool install .` puts `navigator` on PATH | INFRA-01 | Requires global install side effect | Run `uv tool install .` in clean environment, verify `which navigator` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
