# Phase 12: CLI Reference - Research

**Researched:** 2026-03-25
**Domain:** mkdocs-click CLI auto-generation, Typer help text quality
**Confidence:** HIGH

## Summary

Phase 12 builds on a fully operational documentation infrastructure from Phase 11. The mkdocs-click extension, Typer-to-Click bridge, and CLI reference page already exist and produce working output for all 21 commands (18 top-level + 3 namespace subcommands). The current build passes `mkdocs build --strict` with zero warnings.

The primary work in this phase is quality improvement, not infrastructure. An audit of all CLI help strings reveals that every command docstring and every option/argument help text is populated -- none are empty or placeholder. However, the `--version` option on the root `navigator` command has `help=None`, which renders as "N/A" in the generated reference. Additionally, some help strings are terse and could benefit from more descriptive text (e.g., `"Manage namespaces."` could explain what namespaces are for, `"Skip confirmation"` on `--force` could clarify the consequence).

**Primary recommendation:** Review and enhance all help strings for clarity and completeness, fix the `--version` help=None issue, verify the generated reference page renders all 21 commands with correct structure, and ensure `mkdocs build --strict` continues to pass.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
None -- all implementation choices are at Claude's discretion (infrastructure phase).

### Claude's Discretion
All implementation choices including CLI reference page structure, mkdocs-click directive configuration, and help text improvements are technical decisions guided by the existing mkdocs-click setup from Phase 11.

### Deferred Ideas (OUT OF SCOPE)
None.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DINF-02 | Auto-generated CLI reference from Typer app covering all commands and subcommands | Infrastructure already exists from Phase 11; this phase ensures complete coverage, quality help text, and passing strict build |
</phase_requirements>

## Standard Stack

### Core (Already Installed)
| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| mkdocs | 1.6 | Static site generator | Installed in docs group |
| mkdocs-material | 9.7 | Theme | Installed in docs group |
| mkdocs-click | 0.9 | CLI reference auto-generation | Installed, configured as markdown extension |

No new dependencies are needed for this phase.

## Architecture Patterns

### Existing Infrastructure (from Phase 11)
```
orchestrator/
├── mkdocs.yml                        # MkDocs config (mkdocs-click as markdown_extensions)
├── docs/
│   ├── index.md                      # Landing page
│   └── reference/
│       └── cli.md                    # CLI reference with mkdocs-click directive
├── src/navigator/
│   ├── cli.py                        # All CLI commands (help text source)
│   └── _click_bridge.py              # Typer-to-Click bridge for mkdocs-click
└── pyproject.toml                    # docs dependency group
```

### Pattern 1: mkdocs-click Directive (Already in Place)
The directive in `docs/reference/cli.md` is:
```markdown
::: mkdocs-click
    :module: navigator._click_bridge
    :command: cli
    :prog_name: navigator
    :style: table
    :list_subcommands: true
```

**Available directive options** (verified from source):
| Option | Current Value | Purpose |
|--------|---------------|---------|
| `:module:` | `navigator._click_bridge` | Python module containing the Click group |
| `:command:` | `cli` | Attribute name of the Click group |
| `:prog_name:` | `navigator` | Name shown in usage strings |
| `:style:` | `table` | Output format: `table` or `plain` |
| `:list_subcommands:` | `true` | Show subcommand list on parent |
| `:depth:` | `0` (default) | Heading depth offset |
| `:show_hidden:` | `false` (default) | Include hidden commands |
| `:remove_ascii_art:` | `false` (default) | Strip ASCII art from help |

The current configuration is appropriate. No changes needed to the directive.

### Pattern 2: Help Text Quality Standards
Good Typer help text follows these conventions:
- **Command docstrings**: Start with a verb, describe what the command does, mention key behavior. 1-2 sentences.
- **Option help**: Describe what the option controls, include default behavior when relevant, mention valid values for constrained inputs.
- **Argument help**: Name what the argument represents, include format hints when not obvious.

### Anti-Patterns to Avoid
- **Overly long docstrings in CLI functions**: mkdocs-click renders the full docstring. Keep it concise -- 1-2 sentences max. Longer explanations belong in guide docs (Phase 14), not help text.
- **Changing command names or signatures**: This phase is about documentation quality, not refactoring the CLI API.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI documentation | Manual markdown reference | mkdocs-click auto-generation | Already working from Phase 11 |
| Help text formatting | Post-processing scripts | Typer's built-in help parameter | Typer renders help text correctly; just improve the source strings |

## Common Pitfalls

### Pitfall 1: Breaking the Strict Build
**What goes wrong:** Editing help text or CLI structure causes `mkdocs build --strict` to fail.
**Why it happens:** mkdocs-click introspects the live Click tree at build time. Import errors, circular imports, or removing commands breaks the build.
**How to avoid:** Run `uv run mkdocs build --strict` after every change to cli.py. Do not reorganize imports or module structure in this phase.
**Warning signs:** Build errors mentioning ModuleNotFoundError or Click introspection failures.

### Pitfall 2: Help Text That Reads Well in --help but Poorly in Docs
**What goes wrong:** Help text optimized for terminal width (80 chars) looks truncated or oddly formatted in the HTML table layout.
**Why it happens:** mkdocs-click renders help text into markdown tables. Very long single-line help strings may not wrap well.
**How to avoid:** Keep help strings under 60 characters where possible. For complex options, use a short description rather than a full explanation.
**Warning signs:** Check the rendered output with `uv run mkdocs serve` -- not just `--help` in terminal.

### Pitfall 3: --version Help Text Showing as N/A
**What goes wrong:** The `--version` option in the generated reference shows "N/A" for its description.
**Why it happens:** The `--version` option is created via `typer.Option("--version", callback=version_callback, is_eager=True)` without a `help=` parameter. Typer does not auto-generate help text for callback-only options.
**How to avoid:** Add `help="Show version and exit."` to the `--version` Option definition.
**Warning signs:** Already visible in the current generated output.

## Code Examples

### Fix: --version Help Text
```python
# In src/navigator/cli.py, update the version option:
version: Annotated[
    bool | None,
    typer.Option(
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
] = None,
```

### Help Text Improvement Pattern
Before (terse):
```python
"""Manage namespaces."""
```
After (descriptive):
```python
"""Manage namespaces for organizing commands into groups."""
```

The improvements should be meaningful but not verbose. Every docstring and help parameter already has content -- this is polish, not gap-filling.

## Current Help Text Audit

### Commands (21 total) -- All Have Docstrings
Every command has a non-empty docstring. Quality assessment:

| Command | Current Help Text | Quality |
|---------|-------------------|---------|
| register | Register a new command. | Good |
| list | List all registered commands. | Good |
| show | Show full details of a registered command. | Good |
| update | Update fields of a registered command. | Good |
| delete | Delete a registered command. | Good |
| pause | Pause a registered command. | Good |
| resume | Resume a paused command. | Good |
| exec | Execute a registered command. | Good |
| schedule | Schedule a command with a cron expression. | Good |
| watch | Register a file watcher for a command. | Good |
| chain | Chain commands together. | Could be clearer |
| logs | View execution logs. | Could be clearer |
| daemon | Run the watcher daemon in foreground (for systemd). | Good |
| install-service | Generate and install the systemd user service. | Good |
| uninstall-service | Remove the systemd user service. | Good |
| service | Manage the Navigator systemd service. | Could be clearer |
| doctor | Verify system health. | Could be clearer |
| namespace | Manage namespaces. | Could be clearer |
| namespace create | Create a new namespace. | Good |
| namespace list | List all namespaces with command counts. | Good |
| namespace delete | Delete a namespace. | Good |

### Options/Arguments -- All Have Help Text
Every option and argument has help text. One issue found:

| Issue | Location | Fix |
|-------|----------|-----|
| `--version` has `help=None` | `cli.py` line 43 | Add `help="Show version and exit."` |

### Rendered Output Verification
The current `mkdocs build --strict` succeeds with zero warnings. The generated HTML includes:
- Root `navigator` command with options table
- Subcommand list with descriptions
- Individual sections for all 18 top-level commands
- Nested `namespace` subgroup with its 3 subcommands
- All options rendered in table format with name, type, description, default

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0+ |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run mkdocs build --strict` |
| Full suite command | `uv run mkdocs build --strict && uv run pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DINF-02 | CLI reference page exists at docs/reference/cli.md | smoke | `test -f docs/reference/cli.md` | Yes |
| DINF-02 | Reference is auto-generated (not hand-written) | smoke | `grep -q 'mkdocs-click' docs/reference/cli.md` | Yes |
| DINF-02 | All 21 commands appear in generated output | smoke | `uv run mkdocs build --strict && grep -c '<h2' site/reference/cli/index.html` | N/A (build check) |
| DINF-02 | No empty help text in CLI commands | smoke | `uv run python -c "from navigator._click_bridge import cli; ..."` (audit script) | N/A (script check) |
| DINF-02 | Strict build passes | smoke | `uv run mkdocs build --strict` | N/A (build check) |

### Sampling Rate
- **Per task commit:** `uv run mkdocs build --strict`
- **Per wave merge:** `uv run mkdocs build --strict && uv run pytest tests/ -x`
- **Phase gate:** Full suite green + strict build passes + visual inspection of rendered reference

### Wave 0 Gaps
None -- validation is via `mkdocs build --strict` and help text audit script. No new test files needed.

## Open Questions

None -- this phase is straightforward. The infrastructure is proven, the audit is complete, and the work scope is clear.

## Sources

### Primary (HIGH confidence)
- Local codebase: `src/navigator/cli.py` -- all help strings audited via Click introspection
- Local codebase: `docs/reference/cli.md` -- directive verified working
- Local codebase: `mkdocs.yml` -- configuration verified
- Local build: `uv run mkdocs build --strict` -- passes with zero warnings
- mkdocs-click source: `_extension.py` -- directive options verified from installed package

### Secondary (MEDIUM confidence)
- Phase 11 research and summary -- mkdocs-click patterns and decisions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all infrastructure proven in Phase 11, no new dependencies
- Architecture: HIGH -- existing patterns, no structural changes needed
- Pitfalls: HIGH -- verified against actual build output and help text audit
- Help text quality: HIGH -- complete audit performed, all issues catalogued

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable ecosystem, no moving parts)
