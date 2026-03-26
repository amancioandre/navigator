# Phase 16: Docs Maintenance - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped)

<domain>
## Phase Boundary

Documentation stays current as Navigator evolves beyond this milestone. Final validation of the complete docs site, orphan page check, and documenting the convention for keeping docs current in future milestones.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — pure infrastructure phase. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- Complete MkDocs docs site with 12+ pages
- `mkdocs.yml` with Material theme, strict build config
- `uv run mkdocs build --strict` for validation
- CLAUDE.md already has a Conventions section (currently empty)

### Established Patterns
- `uv run mkdocs build --strict` catches orphaned pages and broken links
- mkdocs-click auto-generates CLI reference from Typer app

### Integration Points
- CLAUDE.md Conventions section — where docs maintenance convention should be documented
- mkdocs.yml nav — source of truth for page reachability

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
