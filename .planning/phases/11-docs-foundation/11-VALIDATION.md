---
phase: 11
slug: docs-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x (existing) + mkdocs build --strict |
| **Config file** | pyproject.toml (pytest), mkdocs.yml (docs build) |
| **Quick run command** | `uv run mkdocs build --strict` |
| **Full suite command** | `uv run pytest tests/ && uv run mkdocs build --strict` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run mkdocs build --strict`
- **After every plan wave:** Run `uv run pytest tests/ && uv run mkdocs build --strict`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | DINF-01 | build | `uv run mkdocs build --strict` | ❌ W0 | ⬜ pending |
| 11-01-02 | 01 | 1 | DINF-03 | build | `uv run mkdocs build --strict` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `mkdocs.yml` — MkDocs configuration with Material theme
- [ ] `docs/index.md` — Landing page stub
- [ ] `uv sync --group docs` — install docs dependencies

*These are created as part of Phase 11 itself — the phase IS the infrastructure setup.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `mkdocs serve` shows Material theme | DINF-01 | Visual check | Run `uv run mkdocs serve`, open localhost:8000, verify Material theme renders |
| CLI auto-generation plugin output quality | DINF-02 (Phase 12) | Visual check | Run `uv run mkdocs serve`, navigate to CLI reference page, verify commands render |

*Note: DINF-02 is Phase 12's requirement but plugin validation is a Phase 11 success criterion.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
