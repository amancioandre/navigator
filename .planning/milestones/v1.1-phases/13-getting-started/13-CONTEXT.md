# Phase 13: Getting Started - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

A new user can go from zero to a running scheduled command by following the docs. This phase creates two doc pages: an installation guide and a quick start tutorial.

</domain>

<decisions>
## Implementation Decisions

### Installation Guide Structure
- Lead with uv as the primary install method (project's preferred toolchain), with pip as alternative
- Minimal prerequisites section: Python >=3.12, pip or uv
- Single `uv tool install .` command for global install with note about pip alternative
- Verification step using `navigator doctor` with expected output shown

### Quick Start Tutorial Design
- Tutorial example: register a simple echo command, execute it, check output — simplest possible scenario
- Three-step flow: Register → Execute → Verify output
- Include cleanup at end (delete the test command) for a clean ending
- Do not show JSON output mode — keep tutorial minimal, mention `--output json` exists in passing

### Content Tone & Depth
- Direct and concise tone — match the CLI tool personality, no hand-holding
- Include "what's next" links at the end pointing to Feature Guides and CLI Reference
- Code blocks show shell commands with expected output inline

### Claude's Discretion
- Exact file paths and nav structure in mkdocs.yml
- Specific wording and formatting of guide content
- Whether to split installation and quick start into one or two pages

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `navigator doctor` command exists for verification
- `navigator register`, `navigator exec`, `navigator list`, `navigator delete` for tutorial flow
- `docs/index.md` exists as landing page
- `docs/reference/cli.md` exists with auto-generated CLI reference
- `mkdocs.yml` with Material theme and nav structure

### Established Patterns
- MkDocs with Material theme
- Direct, concise CLI help text style (established in Phase 12)
- `uv run mkdocs build --strict` for validation

### Integration Points
- `mkdocs.yml` nav section — add getting started pages
- `docs/index.md` — may need links to new pages
- Feature Guides (Phase 14) — "what's next" links will point here

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the decisions above.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
