# Phase 11: Docs Foundation - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped)

<domain>
## Phase Boundary

MkDocs project builds cleanly and the auto-generation plugin is validated against Navigator's CLI. This phase sets up the documentation infrastructure: MkDocs with Material theme, CLI auto-generation plugin (mkdocs-click or mkdocs-typer2 — to be resolved by testing), strict build validation, and docs dependency group in pyproject.toml.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — pure infrastructure phase. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

Key decision to resolve during planning:
- **Plugin choice**: mkdocs-click vs mkdocs-typer2 — test both against Navigator's nested subcommand groups and pick the one that works best.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- Navigator CLI built with Typer (src/navigator/cli/) — the target for auto-generation
- pyproject.toml already has dependency groups and hatchling build backend
- .gitignore exists for adding site/ exclusion

### Established Patterns
- uv for package management, dependency groups in pyproject.toml
- Project root is the working directory for all tooling

### Integration Points
- pyproject.toml [project.optional-dependencies] or [dependency-groups] for docs group
- mkdocs.yml at project root
- .gitignore for site/ directory

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — infrastructure phase.

</deferred>
