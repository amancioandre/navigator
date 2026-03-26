---
phase: 14
slug: feature-guides
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 14 — Validation Strategy

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
| 14-01-01 | 01 | 1 | GUIDE-01,02,03 | build + grep | `uv run mkdocs build --strict && test -f site/guides/scheduling/index.html` | ❌ W0 | ⬜ pending |
| 14-02-01 | 02 | 1 | GUIDE-04,05,06 | build + grep | `uv run mkdocs build --strict && test -f site/guides/secrets/index.html` | ❌ W0 | ⬜ pending |
| 14-03-01 | 03 | 2 | GUIDE-07 | build + grep | `uv run mkdocs build --strict && test -f site/guides/configuration/index.html` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `docs/guides/*.md` — 7 guide files
- [ ] `mkdocs.yml` nav update — add Guides section

*These are created as part of Phase 14 itself.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Guide readability and accuracy | ALL | Content quality check | Read each guide, verify examples match actual CLI behavior |
| Cross-links work correctly | ALL | Navigation check | Click all cross-reference links between guides |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
