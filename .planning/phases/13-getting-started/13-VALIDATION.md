---
phase: 13
slug: getting-started
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 13 — Validation Strategy

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
| 13-01-01 | 01 | 1 | START-01 | build + grep | `uv run mkdocs build --strict && grep -q 'uv tool install' site/getting-started/installation/index.html` | ❌ W0 | ⬜ pending |
| 13-01-02 | 01 | 1 | START-02 | build + grep | `uv run mkdocs build --strict && grep -q 'navigator register' site/getting-started/quickstart/index.html` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `docs/getting-started/installation.md` — installation guide page
- [ ] `docs/getting-started/quickstart.md` — quick start tutorial page
- [ ] `mkdocs.yml` nav update — add Getting Started section

*These are created as part of Phase 13 itself.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Tutorial is self-contained and completable | START-02 | Requires following steps end-to-end | Follow quickstart.md from scratch: register, exec, verify output, delete |
| Installation guide covers all methods | START-01 | Visual completeness check | Read installation.md, verify pip/uv/global methods all present |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
