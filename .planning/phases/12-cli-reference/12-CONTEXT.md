# Phase 12: CLI Reference - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped)

<domain>
## Phase Boundary

Every Navigator command and subcommand is documented automatically from the live Typer app. This phase builds on Phase 11's mkdocs-click plugin to produce a comprehensive, auto-generated CLI reference page. Includes reviewing and improving all --help strings in cli.py.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — pure infrastructure phase. The CLI reference page structure, mkdocs-click directive configuration, and help text improvements are all technical decisions guided by the existing mkdocs-click setup from Phase 11.

Key considerations:
- Phase 11 already created `docs/reference/cli.md` with the mkdocs-click directive and `src/navigator/_click_bridge.py` bridge module
- This phase focuses on ensuring complete coverage and quality help text
- mkdocs-click was validated to work with Navigator's nested subcommand groups

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `docs/reference/cli.md` — already has mkdocs-click directive from Phase 11
- `src/navigator/_click_bridge.py` — Typer-to-Click bridge module
- `mkdocs.yml` — configured with mkdocs-click as markdown extension
- `src/navigator/cli.py` — main Typer app with all CLI commands

### Established Patterns
- mkdocs-click as markdown extension (not plugin) — validated in Phase 11
- Material theme for MkDocs
- uv for package management, `uv run mkdocs build --strict` for validation

### Integration Points
- `docs/reference/cli.md` ← mkdocs-click directive references bridge module
- `src/navigator/cli.py` ← help text source for all commands
- `mkdocs.yml` ← nav structure for reference section

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — infrastructure phase.

</deferred>
