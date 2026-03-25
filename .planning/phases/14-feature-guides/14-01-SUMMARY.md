---
phase: 14-feature-guides
plan: 01
subsystem: docs
tags: [mkdocs, markdown, scheduling, file-watching, chaining, guides]

# Dependency graph
requires:
  - phase: 13-getting-started
    provides: "Established writing patterns, quickstart.md tone reference, mkdocs.yml nav structure"
provides:
  - "Scheduling guide (GUIDE-01) with 5 cron expression examples"
  - "File watching guide (GUIDE-02) with debounce, ignore patterns, active-hours"
  - "Command chaining guide (GUIDE-03) with correlation IDs, cycle detection, depth limits"
  - "Guides section in mkdocs.yml nav with 3 entries"
affects: [14-02, 14-03, 15-readme]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Guide template: Overview-Prerequisites-Usage-Patterns-Troubleshooting-WhatsNext"]

key-files:
  created:
    - docs/guides/scheduling.md
    - docs/guides/file-watching.md
    - docs/guides/chaining.md
  modified:
    - mkdocs.yml

key-decisions:
  - "Cross-links to not-yet-created guides use plain text instead of markdown links to pass strict build"

patterns-established:
  - "Guide structure: H1 title, 1-sentence overview, Prerequisites, primary action, Common Patterns, secondary actions, Troubleshooting, What's Next"
  - "Coming-soon plain text for cross-links to future guides (avoids strict build failures)"

requirements-completed: [GUIDE-01, GUIDE-02, GUIDE-03]

# Metrics
duration: 2min
completed: 2026-03-25
---

# Phase 14 Plan 01: Feature Guides Summary

**Three feature guides (scheduling, file watching, chaining) with consistent structure, real CLI examples, and Guides nav section in mkdocs.yml**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-25T22:43:39Z
- **Completed:** 2026-03-25T22:45:48Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Scheduling guide with 5 cron expression examples (daily, hourly, weekdays, every 15 min, weekly)
- File watching guide covering debounce, ignore patterns, active-hours constraints, and SelfTriggerGuard
- Command chaining guide with correlation IDs, cycle detection, depth limits, and cross-namespace support
- Guides section added to mkdocs.yml nav; strict build passes cleanly

## Task Commits

Each task was committed atomically:

1. **Task 1: Create scheduling and file watching guides** - `1702cff` (feat)
2. **Task 2: Create chaining guide and update mkdocs.yml nav** - `aca6f41` (feat)

## Files Created/Modified
- `docs/guides/scheduling.md` - Cron scheduling guide with 5 expression examples
- `docs/guides/file-watching.md` - File watching guide with debounce, ignores, active-hours
- `docs/guides/chaining.md` - Command chaining guide with correlation IDs and cycle detection
- `mkdocs.yml` - Added Guides nav section with 3 entries

## Decisions Made
- Cross-links to not-yet-created guides (systemd, namespaces, configuration) use plain text with "(coming soon)" instead of markdown links, preventing strict build failures while maintaining discoverability. Plans 02 and 03 will convert these to real links.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed broken cross-links to future guides**
- **Found during:** Task 2 (mkdocs build --strict validation)
- **Issue:** What's Next sections linked to systemd.md, namespaces.md, configuration.md which don't exist yet, causing 6 strict build warnings
- **Fix:** Converted links to plain text with "(coming soon)" suffix
- **Files modified:** docs/guides/scheduling.md, docs/guides/file-watching.md, docs/guides/chaining.md
- **Verification:** `uv run mkdocs build --strict` passes with zero warnings
- **Committed in:** aca6f41 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary fix for strict build compliance. No scope creep. Future plans will convert plain text to real links.

## Issues Encountered
None beyond the cross-link deviation documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Guides directory and nav section established for plans 02 and 03 to add remaining guides
- Plain text cross-links ready to be converted to real links as target guides are created

---
*Phase: 14-feature-guides*
*Completed: 2026-03-25*
