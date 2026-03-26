# Roadmap: Navigator

## Milestones

- ✅ **v1.0 Navigator Core** — Phases 1-10 (shipped 2026-03-25)
- ✅ **v1.1 Documentation** — Phases 11-16 (shipped 2026-03-26)
- 🚧 **v1.2 CI/CD Docs Publishing** — Phases 17-18 (in progress)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

<details>
<summary>v1.0 Navigator Core (Phases 1-10) - SHIPPED 2026-03-25</summary>

- [x] **Phase 1: Project Scaffold** - Installable Python package with CLI entry point and configuration
- [x] **Phase 2: Command Registry** - Full CRUD for registered commands backed by SQLite
- [x] **Phase 3: Execution Core** - Run registered commands as Claude Code subprocesses with secrets and clean environments
- [x] **Phase 4: Execution Hardening** - Retry, timeouts, logging, and process lifecycle management
- [x] **Phase 5: Cron Scheduling** - Schedule commands via real system crontab with lock-safe writes
- [x] **Phase 6: File Watching** - Trigger commands on filesystem changes with debounce and guards
- [x] **Phase 7: Namespacing** - Multi-project command isolation with per-namespace secrets
- [x] **Phase 8: Command Chaining** - Sequential command triggers with depth limits and cycle detection
- [x] **Phase 9: Daemon and systemd** - Persistent watcher daemon and systemd service installation
- [x] **Phase 10: Operational Polish** - Health checks, JSON output, and dry-run for Claude Code agents

</details>

<details>
<summary>v1.1 Documentation (Phases 11-16) - SHIPPED 2026-03-26</summary>

- [x] **Phase 11: Docs Foundation** - MkDocs scaffold with Material theme, dependency group, and strict build validation (completed 2026-03-25)
- [x] **Phase 12: CLI Reference** - Auto-generated CLI reference covering all commands and subcommands (completed 2026-03-25)
- [x] **Phase 13: Getting Started** - Installation guide and quick start tutorial (completed 2026-03-25)
- [x] **Phase 14: Feature Guides** - Seven task-oriented guides for each major Navigator capability (completed 2026-03-26)
- [x] **Phase 15: README** - Comprehensive README.md with install, quick start, and links to docs site (completed 2026-03-26)
- [x] **Phase 16: Docs Maintenance** - Strict build enforcement and maintenance conventions for future milestones (completed 2026-03-26)

</details>

### v1.2 CI/CD Docs Publishing (In Progress)

- [ ] **Phase 17: Docs Deployment Pipeline** - GitHub Actions workflow deploys MkDocs site to gh-pages with dependency caching
- [ ] **Phase 18: PR Validation Gate** - Pull request docs build check with branch protection enforcement

## Phase Details

### Phase 17: Docs Deployment Pipeline
**Goal**: Pushing to master automatically publishes the docs site to GitHub Pages
**Depends on**: Phase 16 (docs site must exist and build cleanly)
**Requirements**: DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-04
**Success Criteria** (what must be TRUE):
  1. Pushing a commit to master triggers a GitHub Actions workflow that builds and deploys the MkDocs site to gh-pages
  2. The docs site is accessible at the GitHub Pages URL after a successful deployment
  3. Subsequent workflow runs use cached uv/pip dependencies (visible as cache hit in Actions logs)
  4. The deploy workflow result appears as a commit status check on the master branch
**Plans:** 1 plan
Plans:
- [ ] 17-01-PLAN.md — Create docs deployment workflow and configure GitHub Pages

### Phase 18: PR Validation Gate
**Goal**: Pull requests cannot merge with broken docs, enforced by CI and branch protection
**Depends on**: Phase 17
**Requirements**: VALID-01, VALID-02
**Success Criteria** (what must be TRUE):
  1. Opening or updating a PR triggers a docs build with `--strict` that fails if any MkDocs warnings exist
  2. A PR with broken docs (missing links, bad config) shows a failing check and cannot be merged
  3. Branch protection rule on master requires the docs build check to pass before merge is allowed
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 17 → 18

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 17. Docs Deployment Pipeline | 0/1 | Planned | - |
| 18. PR Validation Gate | 0/0 | Not started | - |
