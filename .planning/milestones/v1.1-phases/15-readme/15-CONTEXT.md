# Phase 15: README - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning
**Mode:** Auto-generated (fully specified by success criteria)

<domain>
## Phase Boundary

The project README serves as a concise entry point that links to the docs site for depth. Hard-capped at 150 lines.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — the success criteria fully define the README's content requirements:
- Installation instructions matching the docs site installation guide
- Quick start section with 4-5 commands showing the core workflow
- Feature overview listing all major capabilities with one-line descriptions
- Under 150 lines, links to docs site for depth

Prior decisions:
- Direct and concise tone (established in Phases 13-14)
- README links to docs site, not the other way around (ROADMAP decision)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `docs/getting-started/installation.md` — source for installation instructions
- `docs/getting-started/quickstart.md` — source for quick start commands
- All feature guide files in `docs/guides/` — source for feature descriptions
- `docs/reference/cli.md` — CLI reference to link to

### Established Patterns
- Direct/concise writing style
- Shell commands with expected output inline

### Integration Points
- `README.md` at project root (new file)
- Links to docs site pages for depth

</code_context>

<specifics>
## Specific Ideas

No specific requirements — fully specified by success criteria.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
