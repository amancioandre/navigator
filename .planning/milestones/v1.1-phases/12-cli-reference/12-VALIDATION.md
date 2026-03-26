---
phase: 12
slug: cli-reference
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 12 — Validation Strategy

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
| 12-01-01 | 01 | 1 | DINF-02 | build + grep | `uv run mkdocs build --strict && grep -c '<h[23]' site/reference/cli/index.html` | ✅ | ⬜ pending |
| 12-01-02 | 01 | 1 | DINF-02 | grep | `grep -E 'help=None\|"N/A"' src/navigator/cli.py` (should find 0 matches) | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements — Phase 11 installed mkdocs-click and validated the build.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CLI reference page readability | DINF-02 | Visual quality check | Run `uv run mkdocs serve`, navigate to CLI Reference, verify all commands render with clear descriptions |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
