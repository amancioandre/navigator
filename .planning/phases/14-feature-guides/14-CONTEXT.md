# Phase 14: Feature Guides - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Each major Navigator capability has a task-oriented guide with real examples. Seven guides covering scheduling, file watching, chaining, secrets, namespaces, systemd, and configuration reference. Plus mkdocs.yml nav updates.

</domain>

<decisions>
## Implementation Decisions

### Guide Structure & Format
- Consistent structure across all 7 guides: Overview → Prerequisites → Usage → Examples → Troubleshooting
- Flat file organization: `docs/guides/{feature}.md` — 7 files in one directory
- Real CLI commands with expected output shown inline (consistent with getting started from Phase 13)
- Cross-link related guides (e.g., scheduling → systemd for persistence, secrets → namespaces for isolation)

### Content Depth
- Task-oriented: show how to DO things, not explain internals
- Config reference uses table format per section: option, type, default, description
- Include 2-3 real-world "common patterns" per guide (e.g., cron: "daily at 9am", "weekdays only")

### Tone & Scope
- Direct and concise tone — same as getting started (established in Phase 13)
- Use MkDocs admonitions for important caveats (e.g., "secrets are plaintext .env files")
- Target ~100-150 lines per guide — enough to be useful, short enough to scan

### Claude's Discretion
- Exact content and examples within each guide
- Ordering of guides in nav
- Which features to cross-reference within each guide

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- All CLI commands exist and are functional (verified in prior phases)
- `docs/getting-started/` pages establish the tone and format precedent
- MkDocs Material with admonitions, highlight, superfences extensions
- Auto-generated CLI reference at `docs/reference/cli.md`

### Established Patterns
- Direct/concise writing style (Phase 13)
- Shell commands with expected output inline
- `uv run mkdocs build --strict` for validation
- Material theme features: code copy, content tabs

### Integration Points
- `mkdocs.yml` nav section — add Guides section
- `docs/getting-started/quickstart.md` — update "What's Next" links to point to actual guide pages
- `docs/index.md` — may need links to guides section

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the decisions above.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
