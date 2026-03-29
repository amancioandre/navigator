# Roadmap: Navigator

## Milestones

- v1.0 MVP - Phases 1-10 (shipped 2026-03-25)
- v1.1 Documentation - Phases 11-16 (shipped 2026-03-26)
- v1.2 CI/CD Docs Publishing - Phases 17-18 (shipped 2026-03-26)
- v1.2.1 Cron Scheduling Fixes - Phases 19-20 (in progress)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

<details>
<summary>v1.0 MVP (Phases 1-10) - SHIPPED 2026-03-25</summary>

See MILESTONES.md for details.

</details>

<details>
<summary>v1.1 Documentation (Phases 11-16) - SHIPPED 2026-03-26</summary>

See MILESTONES.md for details.

</details>

<details>
<summary>v1.2 CI/CD Docs Publishing (Phases 17-18) - SHIPPED 2026-03-26</summary>

See MILESTONES.md for details.

</details>

### v1.2.1 Cron Scheduling Fixes (In Progress)

**Milestone Goal:** Fix cron scheduling bugs that break real-world command execution -- namespace-aware scheduling, PATH resolution, and failure diagnostics.

- [x] **Phase 19: Namespace-Aware Scheduling** - Fix schedule/unschedule to work with qualified namespace names (completed 2026-03-28)
- [x] **Phase 20: Cron Execution & Diagnostics** - Resolve claude binary path for cron and log execution failures (completed 2026-03-29)

## Phase Details

### Phase 19: Namespace-Aware Scheduling
**Goal**: Users can schedule and unschedule namespaced commands using qualified names
**Depends on**: Nothing (independent bug fix)
**Requirements**: SCHED-01, SCHED-02, SCHED-03
**Success Criteria** (what must be TRUE):
  1. User can run `navigator schedule ns:cmd --cron "..."` and it succeeds without error
  2. The resulting crontab entry contains `navigator exec ns:cmd` (qualified name preserved)
  3. User can run `navigator schedule ns:cmd --remove` and the crontab entry is removed
  4. Existing non-namespaced scheduling continues to work unchanged
**Plans:** 1/1 plans complete
Plans:
- [x] 19-01-PLAN.md -- Fix schedule/unschedule to parse qualified namespace names (tests + CLI fix)

### Phase 20: Cron Execution & Diagnostics
**Goal**: Cron-triggered commands find the claude binary and failed executions produce diagnostic logs
**Depends on**: Nothing (independent of Phase 19)
**Requirements**: CRON-01, CRON-02, DIAG-01, DIAG-02
**Success Criteria** (what must be TRUE):
  1. A command scheduled via cron executes successfully even with cron's minimal PATH (`/usr/bin:/bin`)
  2. Navigator resolves `claude` to its absolute path at execution time (not registration time)
  3. When a child process fails to start (binary not found, permission denied), an execution log entry is written with the error details
  4. User can view failed execution details via `navigator logs <command>` including the failure reason
**Plans:** 2/2 plans complete
Plans:
- [x] 20-01-PLAN.md -- Resolve claude binary to absolute path in build_command_args (CRON-01, CRON-02)
- [x] 20-02-PLAN.md -- Add OSError handling and error field to execution logs (DIAG-01, DIAG-02)

## Progress

**Execution Order:**
Phases execute in numeric order: 19 -> 20

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 19. Namespace-Aware Scheduling | v1.2.1 | 1/1 | Complete    | 2026-03-28 |
| 20. Cron Execution & Diagnostics | v1.2.1 | 2/2 | Complete   | 2026-03-29 |
