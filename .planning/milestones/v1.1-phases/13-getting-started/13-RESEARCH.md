# Phase 13: Getting Started - Research

**Researched:** 2026-03-25
**Domain:** Documentation -- installation guide and quick start tutorial
**Confidence:** HIGH

## Summary

Phase 13 creates two documentation pages (or one combined page) for Navigator: an installation guide and a quick start tutorial. The domain is straightforward -- this is Markdown content authored in MkDocs Material, following patterns already established in Phases 11-12. The existing docs infrastructure (mkdocs.yml, Material theme, admonition/superfences extensions) is fully operational and validated with `mkdocs build --strict`.

The main challenge is content accuracy: every shell command and its expected output must reflect the real CLI behavior. Research captured actual CLI output from `navigator doctor`, `navigator register`, `navigator list`, `navigator exec --dry-run`, and `navigator delete` to provide verified examples the planner can reference.

**Primary recommendation:** Write the docs pages using verified CLI output captured during research. Validate with `uv run mkdocs build --strict` and manual `mkdocs serve` review.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Lead with uv as the primary install method (project's preferred toolchain), with pip as alternative
- Minimal prerequisites section: Python >=3.12, pip or uv
- Single `uv tool install .` command for global install with note about pip alternative
- Verification step using `navigator doctor` with expected output shown
- Tutorial example: register a simple echo command, execute it, check output -- simplest possible scenario
- Three-step flow: Register -> Execute -> Verify output
- Include cleanup at end (delete the test command) for a clean ending
- Do not show JSON output mode -- keep tutorial minimal, mention `--output json` exists in passing
- Direct and concise tone -- match the CLI tool personality, no hand-holding
- Include "what's next" links at the end pointing to Feature Guides and CLI Reference
- Code blocks show shell commands with expected output inline

### Claude's Discretion
- Exact file paths and nav structure in mkdocs.yml
- Specific wording and formatting of guide content
- Whether to split installation and quick start into one or two pages

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| START-01 | Installation guide covering pip, uv, and global install methods | Verified pyproject.toml entry points, captured `navigator doctor` output for verification step |
| START-02 | Quick start tutorial walking through registering and executing a first command | Verified full CLI flow: register, list, exec --dry-run, delete with actual output captured |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python >=3.12 runtime requirement
- uv is the preferred toolchain (referenced throughout CLAUDE.md)
- hatchling is the build backend
- Project entry point: `navigator = "navigator.cli:app"` in pyproject.toml
- MkDocs with Material theme for documentation (established in Phase 11-12)
- `uv run mkdocs build --strict` for build validation

## Architecture Patterns

### Current Docs Structure
```
docs/
  index.md          # Landing page with quick links
  reference/
    cli.md          # Auto-generated CLI reference (mkdocs-click)
mkdocs.yml          # Nav: Home, Reference > CLI
```

### Recommended Addition
```
docs/
  index.md          # Update quick links to include getting started
  getting-started/
    installation.md # Installation guide (START-01)
    quickstart.md   # Quick start tutorial (START-02)
  reference/
    cli.md
```

**Rationale for two pages:** The CONTEXT.md locked decisions describe two distinct doc artifacts (installation guide, quick start tutorial) with different purposes. Splitting them keeps each page focused and short. The planner has discretion here per CONTEXT.md but two pages is the cleaner structure.

### mkdocs.yml Nav Update
```yaml
nav:
  - Home: index.md
  - Getting Started:
    - Installation: getting-started/installation.md
    - Quick Start: getting-started/quickstart.md
  - Reference:
    - CLI: reference/cli.md
```

### MkDocs Material Features Available
The following markdown extensions are already configured and available:
- `admonition` -- for tip/warning/note boxes
- `pymdownx.highlight` -- syntax highlighting in code blocks
- `pymdownx.superfences` -- fenced code blocks with language tags
- `content.code.copy` -- copy button on code blocks (theme feature)

## Verified CLI Output

All output captured from the actual CLI on 2026-03-25. Use these as the source of truth for documentation examples.

### navigator doctor (healthy system)
```
$ navigator doctor
  PASS  Database: Database OK (0 commands)
  PASS  Navigator binary: Found at /home/user/.local/bin/navigator
  PASS  Registered paths: No commands registered
  PASS  Crontab sync: No crontab entries
  PASS  Service: Service not installed (optional)

5 checks: 5 passed, 0 failed, 0 warned
```

Note: The binary path in actual output was `.venv/bin/navigator` (dev environment). For the docs, use a representative path like `/home/user/.local/bin/navigator` since users will have it globally installed.

### navigator register
```
$ navigator register hello-world --prompt "echo hello from navigator" --environment /tmp
Registered command 'hello-world'
```

### navigator list
```
$ navigator list
                              Registered Commands
┏━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Name        ┃ Status ┃ Namespace ┃ Environment ┃ Created             ┃
┡━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ hello-world │ active │ default   │ /tmp        │ 2026-03-25T20:18:…  │
└─────────────┴────────┴───────────┴─────────────┴─────────────────────┘
```

### navigator exec --dry-run
```
$ navigator exec hello-world --dry-run
╭────────────────────────────── Dry Run ──────────────────────────────╮
│ Command:    hello-world                                             │
│ Namespace:  default                                                 │
│ Directory:  /tmp                                                    │
│ Args:       claude -p echo hello from navigator --print             │
│ Env keys:   HOME, LANG, PATH, SHELL, TERM                          │
│ Tools:      (none)                                                  │
╰─────────────────────────────────────────────────────────────────────╯
```

### navigator delete
```
$ navigator delete hello-world --force
Deleted command 'hello-world'
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Code block formatting | Raw HTML/CSS | MkDocs Material `pymdownx.highlight` + `content.code.copy` | Already configured, handles syntax highlighting and copy buttons |
| Callout boxes | Custom styled divs | `admonition` extension (`!!! tip`, `!!! warning`) | Standard MkDocs Material pattern, consistent with rest of docs |
| Navigation structure | Manual HTML links | `mkdocs.yml` nav section | MkDocs handles nav generation, breadcrumbs, and prev/next links |

## Common Pitfalls

### Pitfall 1: Stale CLI Output in Docs
**What goes wrong:** Documentation shows output that doesn't match the actual CLI, confusing users.
**Why it happens:** CLI output changes as features evolve; docs are not auto-tested.
**How to avoid:** Use the verified output from this research. The planner should include a verification step that runs the actual commands and compares output.
**Warning signs:** `mkdocs build --strict` won't catch this -- it only validates markdown structure, not content accuracy.

### Pitfall 2: Broken Internal Links
**What goes wrong:** "What's next" links point to pages that don't exist yet (Phase 14 Feature Guides).
**Why it happens:** Phase 13 runs before Phase 14 creates the guide pages.
**How to avoid:** Link to the CLI Reference (exists) and mention Feature Guides as "coming soon", or use relative links that will resolve once Phase 14 completes. Alternatively, use placeholder text like "See Feature Guides (coming in a future update)" without a link.
**Warning signs:** `mkdocs build --strict` will fail on broken links.

### Pitfall 3: Installation Instructions Assume Dev Setup
**What goes wrong:** Docs show `uv run navigator` (dev mode) instead of just `navigator` (global install).
**Why it happens:** Developers write docs from their dev environment where `uv run` is the norm.
**How to avoid:** All tutorial commands should use bare `navigator` since the installation section establishes a global install via `uv tool install` or `pip install`.

### Pitfall 4: Rich Table Output in Docs
**What goes wrong:** Rich tables use Unicode box-drawing characters that may render inconsistently in markdown code blocks depending on font.
**Why it happens:** Navigator uses Rich for terminal output; docs reproduce this verbatim.
**How to avoid:** Show the table output in a plain code block (no language tag or use `text`). Most monospace fonts handle box-drawing characters fine, but test with `mkdocs serve`.

## Code Examples

### MkDocs Admonition Pattern
```markdown
!!! tip
    You can verify your installation at any time by running `navigator doctor`.
```

### Shell Command with Output Pattern
```markdown
```bash
navigator doctor
```

Expected output:

```text
  PASS  Database: Database OK (0 commands)
  ...
```
```

### "What's Next" Section Pattern
```markdown
## What's Next

- [CLI Reference](../reference/cli.md) -- full command documentation
- Feature Guides -- scheduling, file watching, chaining, and more (coming soon)
```

Note: Use a plain text mention for Feature Guides since those pages don't exist yet. This avoids `--strict` build failures from broken links.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_cli.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| START-01 | Installation guide renders without errors | build validation | `uv run mkdocs build --strict` | N/A (build command, not test file) |
| START-02 | Quick start tutorial renders without errors | build validation | `uv run mkdocs build --strict` | N/A (build command, not test file) |

### Sampling Rate
- **Per task commit:** `uv run mkdocs build --strict`
- **Per wave merge:** `uv run mkdocs build --strict && uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
None -- existing build infrastructure (`uv run mkdocs build --strict`) covers validation for documentation phases. No new test files needed.

## Sources

### Primary (HIGH confidence)
- Direct CLI execution -- all command outputs verified on 2026-03-25 against the actual Navigator codebase
- pyproject.toml -- entry points, dependencies, build system verified
- mkdocs.yml -- current nav structure, extensions, theme features verified
- Existing docs (index.md, reference/cli.md) -- current content verified

### Secondary (MEDIUM confidence)
- MkDocs Material documentation patterns -- based on training data for established features (admonitions, code blocks, nav structure)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new libraries, pure documentation using existing MkDocs setup
- Architecture: HIGH - docs structure follows MkDocs conventions, nav pattern verified
- Pitfalls: HIGH - based on direct observation of CLI output and mkdocs strict mode behavior

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable -- documentation tooling, not fast-moving)
