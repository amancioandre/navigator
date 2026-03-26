# Phase 11: Docs Foundation - Research

**Researched:** 2026-03-25
**Domain:** MkDocs documentation infrastructure with CLI auto-generation
**Confidence:** HIGH

## Summary

This phase sets up MkDocs with the Material theme and validates a CLI auto-generation plugin against Navigator's Typer-based CLI. The documentation stack is well-established: MkDocs 1.6.1 + Material 9.7.6 is the standard for Python project documentation. The dependency group mechanism in `pyproject.toml` via `[dependency-groups]` is already used in this project (the `dev` group exists), so adding a `docs` group is straightforward.

The key decision is the CLI auto-generation plugin. Two candidates exist: **mkdocs-click** (0.9.0) and **mkdocs-typer2** (0.2.0). mkdocs-click is the more mature, actively maintained option under the official mkdocs GitHub organization. It works with Typer because Typer's `TyperGroup` is a subclass of Click's `Group` -- the bridge is `typer.main.get_command(app)` which returns a standard Click object. mkdocs-typer2 is purpose-built for Typer but is a smaller, single-maintainer project. Both should be tested, but mkdocs-click is the safer default.

**Primary recommendation:** Use mkdocs-click with a thin bridge module that exposes the Typer app as a Click group. Test mkdocs-typer2 as the alternative. Pick whichever produces better output for Navigator's nested subcommand groups.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
None -- all implementation choices are at Claude's discretion (infrastructure phase).

### Claude's Discretion
- All implementation choices including plugin selection
- Key decision to resolve: mkdocs-click vs mkdocs-typer2 -- test both against Navigator's nested subcommand groups and pick the one that works best

### Deferred Ideas (OUT OF SCOPE)
None.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DINF-01 | MkDocs site scaffold with Material theme, mkdocs.yml config, and dependency group in pyproject.toml | Standard Stack section covers exact packages and versions; Architecture Patterns section covers mkdocs.yml structure and pyproject.toml dependency group pattern |
| DINF-03 | Strict build validation (`mkdocs build --strict`) integrated into dev workflow | Common Pitfalls section covers strict mode requirements; Validation Architecture section covers test commands |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mkdocs | 1.6.1 | Static site generator | The standard Python documentation tool. Markdown-based, simple config, extensible via plugins. |
| mkdocs-material | 9.7.6 | Theme | De facto standard MkDocs theme. Beautiful defaults, search, dark mode, responsive. Used by most Python OSS projects. |
| mkdocs-click | 0.9.0 | CLI reference auto-generation | Official mkdocs org plugin. Works with Click-based CLIs (Typer included via bridge). Mature, well-maintained. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| mkdocs-typer2 | 0.2.0 | Alternative CLI auto-generation | If mkdocs-click produces poor output for Typer's TyperGroup. Purpose-built for Typer, uses Typer's native `utils docs` or Click walking. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| mkdocs-click | mkdocs-typer2 | mkdocs-typer2 is Typer-native (no bridge module needed) but smaller community, single maintainer (syn54x), newer (v0.2.0 Jan 2026). mkdocs-click is under the mkdocs org, more battle-tested. |
| mkdocs-click | mkdocs-typer (original) | Unmaintained (no updates in 1+ year). mkdocs-typer2 was created to replace it. Do not use. |

**Installation (docs dependency group):**
```bash
uv sync --group docs
```

## Architecture Patterns

### Recommended Project Structure
```
orchestrator/
├── mkdocs.yml              # MkDocs configuration (project root)
├── docs/
│   ├── index.md            # Landing page
│   └── reference/
│       └── cli.md          # CLI reference (auto-generated via plugin directive)
├── docs/_cli.py            # Bridge module exposing Typer app as Click group (if using mkdocs-click)
├── site/                   # Built output (gitignored)
└── pyproject.toml          # docs dependency group
```

### Pattern 1: Typer-to-Click Bridge Module
**What:** A small Python module that imports the Typer app and converts it to a Click group for mkdocs-click consumption.
**When to use:** When using mkdocs-click with a Typer CLI.
**Example:**
```python
# docs/_cli.py
"""Bridge module: exposes Navigator's Typer app as a Click group for mkdocs-click."""
import typer.main
from navigator.cli import app

# mkdocs-click needs a Click Group object, not a Typer app.
# typer.main.get_command() returns the underlying Click Group.
cli = typer.main.get_command(app)
```

Then in `docs/reference/cli.md`:
```markdown
# CLI Reference

::: mkdocs-click
    :module: docs._cli
    :command: cli
    :prog_name: navigator
    :style: table
    :list_subcommands: true
```

### Pattern 2: mkdocs-typer2 Directive (Alternative)
**What:** Direct Typer module reference without a bridge.
**When to use:** If mkdocs-typer2 is chosen over mkdocs-click.
**Example:**

In `docs/reference/cli.md`:
```markdown
# CLI Reference

::: mkdocs-typer2
    :module: navigator.cli
    :name: navigator
    :pretty: true
```

mkdocs.yml config for typer2:
```yaml
plugins:
  - mkdocs-typer2:
      pretty: true
      engine: native
```

### Pattern 3: Dependency Group in pyproject.toml
**What:** Isolate docs dependencies from runtime and dev dependencies.
**When to use:** Always -- docs tools should never be runtime dependencies.
**Example:**
```toml
[dependency-groups]
dev = [
    "pytest>=9.0",
    "ruff>=0.15",
]
docs = [
    "mkdocs>=1.6",
    "mkdocs-material>=9.7",
    "mkdocs-click>=0.9",  # or mkdocs-typer2>=0.2
]
```

### Pattern 4: Minimal mkdocs.yml
**What:** Minimal configuration that satisfies `--strict` mode.
**Example:**
```yaml
site_name: Navigator
site_description: Autonomous task orchestrator for Claude Code sessions
site_url: ""  # Private tool, no hosted URL

theme:
  name: material
  features:
    - navigation.sections
    - navigation.expand
    - content.code.copy
  palette:
    - scheme: default

nav:
  - Home: index.md
  - Reference:
    - CLI: reference/cli.md

plugins:
  - search
  - mkdocs-click  # or mkdocs-typer2

markdown_extensions:
  - admonition
  - pymdownx.highlight
  - pymdownx.superfences
```

### Anti-Patterns to Avoid
- **Over-configuring mkdocs.yml on first pass:** Start minimal. Add features (tabs, versioning, social cards) only when needed. Phase 11 is foundation, not polish.
- **Putting docs dependencies in main `[project.dependencies]`:** These are build-time tools, not runtime. Always use a separate dependency group.
- **Using `site_url` with a real URL for a private tool:** Navigator is never hosted publicly. Set `site_url: ""` to avoid strict mode warnings about missing site_url while making it clear this is local-only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI documentation | Manual markdown files listing commands | mkdocs-click or mkdocs-typer2 directive | CLI changes constantly; manual docs drift immediately. Auto-generation stays in sync. |
| Theme / styling | Custom CSS and HTML templates | mkdocs-material built-in features | Material covers navigation, search, code highlighting, dark mode out of the box. |
| Search | Custom search implementation | mkdocs built-in search plugin | Built-in lunr.js search works perfectly for small-medium doc sites. |

## Common Pitfalls

### Pitfall 1: `--strict` Mode Warnings from Missing site_url
**What goes wrong:** `mkdocs build --strict` fails with a warning about missing `site_url`.
**Why it happens:** MkDocs wants `site_url` for canonical URLs, sitemaps, and social cards. Strict mode treats all warnings as errors.
**How to avoid:** Set `site_url: ""` (empty string) in mkdocs.yml. This satisfies the config requirement without implying the site is hosted.
**Warning signs:** Build succeeds without `--strict` but fails with it.

### Pitfall 2: Bridge Module Import Path Issues
**What goes wrong:** mkdocs-click can't find `docs._cli` module because `docs/` isn't on the Python path.
**Why it happens:** mkdocs-click imports the module at build time. If the docs directory isn't a package or isn't on sys.path, the import fails.
**How to avoid:** Either (a) add `docs/` to the Python path in mkdocs.yml or (b) place the bridge module inside the `src/navigator/` package (e.g., `src/navigator/_click_bridge.py`) so it's importable via the installed package. Option (b) is cleaner.
**Warning signs:** `ModuleNotFoundError` during `mkdocs build`.

### Pitfall 3: mkdocs-click Requiring the Package to Be Installed
**What goes wrong:** `mkdocs build` fails because it can't import `navigator.cli`.
**Why it happens:** mkdocs-click introspects the Click objects at build time by importing the module. The package must be importable.
**How to avoid:** Run `uv sync --group docs` which installs the project in development mode along with docs dependencies. The project is then importable.
**Warning signs:** `ModuleNotFoundError: No module named 'navigator'`.

### Pitfall 4: nav Section Mismatch with Files
**What goes wrong:** `mkdocs build --strict` warns about files listed in `nav` that don't exist, or files that exist but aren't in `nav`.
**Why it happens:** Strict mode validates that nav and docs directory are in sync.
**How to avoid:** Ensure every `.md` file in `docs/` is listed in `nav`, and every `nav` entry has a corresponding file.
**Warning signs:** Warnings about orphan pages or missing files.

### Pitfall 5: Plugin Load Order
**What goes wrong:** CLI auto-generation directive isn't processed.
**Why it happens:** MkDocs plugins are loaded in the order listed in `mkdocs.yml`. If search is not explicitly listed, it may conflict.
**How to avoid:** Explicitly list `search` before the CLI plugin in the `plugins:` list.
**Warning signs:** Raw directive text appears in rendered output instead of generated CLI docs.

## Code Examples

### Complete mkdocs.yml (Verified Pattern)
```yaml
# mkdocs.yml - Navigator documentation
site_name: Navigator
site_description: Autonomous task orchestrator for Claude Code sessions
site_url: ""

theme:
  name: material
  features:
    - navigation.sections
    - navigation.expand
    - content.code.copy
  palette:
    - scheme: default

nav:
  - Home: index.md
  - Reference:
    - CLI: reference/cli.md

plugins:
  - search
  - mkdocs-click  # Replace with mkdocs-typer2 if testing shows better output

markdown_extensions:
  - admonition
  - pymdownx.highlight
  - pymdownx.superfences
```

### Complete pyproject.toml Addition
```toml
# Add to existing [dependency-groups] section
docs = [
    "mkdocs>=1.6",
    "mkdocs-material>=9.7",
    "mkdocs-click>=0.9",
]
```

### Bridge Module (for mkdocs-click)
```python
# src/navigator/_click_bridge.py
"""Expose Navigator's Typer CLI as a Click group for mkdocs-click."""
import typer.main

from navigator.cli import app

cli = typer.main.get_command(app)
```

### CLI Reference Page
```markdown
# CLI Reference

Complete reference for the `navigator` command-line interface.

::: mkdocs-click
    :module: navigator._click_bridge
    :command: cli
    :prog_name: navigator
    :style: table
    :list_subcommands: true
```

### Minimal index.md
```markdown
# Navigator

Autonomous task orchestrator for Claude Code sessions.

## Quick Links

- [CLI Reference](reference/cli.md)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Sphinx + RST | MkDocs + Markdown | ~2020 onward | MkDocs is simpler, Markdown is universal. Sphinx still dominates for API-heavy Python libraries. |
| mkdocs-typer (original) | mkdocs-typer2 or mkdocs-click | 2025 | Original mkdocs-typer is unmaintained. Use mkdocs-typer2 or mkdocs-click. |
| Manual CLI docs | Auto-generated from Click/Typer objects | Standard practice | Eliminates doc drift. |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0+ |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/ -x` |
| Full suite command | `uv run pytest tests/` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DINF-01 | `uv sync --group docs` installs MkDocs + Material + plugin | smoke | `uv sync --group docs && uv run python -c "import mkdocs; import material"` | N/A (command check) |
| DINF-01 | mkdocs.yml exists at project root with correct config | smoke | `test -f mkdocs.yml && uv run mkdocs build --strict` | N/A (file check) |
| DINF-03 | `mkdocs build --strict` produces site with zero warnings | smoke | `uv run mkdocs build --strict 2>&1` | N/A (build check) |
| DINF-03 | `mkdocs serve` launches dev server | manual-only | Manual -- requires interactive browser check | N/A |
| DINF-01 | `site/` is gitignored | smoke | `grep -q 'site/' .gitignore` | N/A (grep check) |

### Sampling Rate
- **Per task commit:** `uv run mkdocs build --strict`
- **Per wave merge:** `uv run mkdocs build --strict && uv run pytest tests/ -x`
- **Phase gate:** Full suite green + `mkdocs build --strict` passes

### Wave 0 Gaps
None -- this phase does not require new test files. Validation is via `mkdocs build --strict` (zero warnings = pass). No pytest tests needed for documentation infrastructure.

## Open Questions

1. **mkdocs-click vs mkdocs-typer2: Which produces better output for TyperGroup?**
   - What we know: mkdocs-click works with Click objects (Typer's TyperGroup is a Click Group subclass). mkdocs-typer2 is purpose-built for Typer with a `native` engine that walks the Click tree.
   - What's unclear: Which plugin handles nested subcommand groups (e.g., `navigator namespace create`) better in terms of output formatting and completeness.
   - Recommendation: The plan should include a testing task that installs both, generates output, and picks the winner. mkdocs-click is the safer default if both are equivalent.

2. **Bridge module placement**
   - What we know: mkdocs-click needs a Click object. Typer exposes this via `typer.main.get_command(app)`.
   - What's unclear: Whether `docs/_cli.py` or `src/navigator/_click_bridge.py` is the better location.
   - Recommendation: Place in `src/navigator/_click_bridge.py` so it's importable without path manipulation. The package is already installed in dev mode via `uv sync`.

3. **site_url for private tool**
   - What we know: `--strict` warns if site_url is missing or empty.
   - What's unclear: Whether `site_url: ""` fully suppresses the warning or if a placeholder like `http://localhost:8000` is needed.
   - Recommendation: Test during implementation. Try `""` first, fall back to `http://localhost:8000` if strict mode complains.

## Navigator CLI Structure (Verified)

The CLI has been verified to have the following structure, which the plugin must document:

```
navigator (TyperGroup)
├── register
├── list
├── show
├── update
├── delete
├── pause
├── resume
├── exec
├── schedule
├── watch
├── chain
├── logs
├── daemon
├── install-service
├── uninstall-service
├── service
├── doctor
└── namespace (TyperGroup)
    ├── create
    ├── list
    └── delete
```

18 top-level commands + 3 namespace subcommands = 21 total command pages the plugin must generate.

## Sources

### Primary (HIGH confidence)
- [PyPI mkdocs 1.6.1](https://pypi.org/project/mkdocs/) - version verified
- [PyPI mkdocs-material 9.7.6](https://pypi.org/project/mkdocs-material/) - version verified
- [PyPI mkdocs-click 0.9.0](https://pypi.org/project/mkdocs-click/) - version and dependencies verified (requires click>=8.1, markdown>=3.3)
- [PyPI mkdocs-typer2 0.2.0](https://pypi.org/project/mkdocs-typer2/) - version verified (released Jan 2026, requires mkdocs>=1.6.1, typer>=0.12.5)
- Local codebase verification: `typer.main.get_command(app)` returns TyperGroup with 18 commands + namespace subgroup

### Secondary (MEDIUM confidence)
- [mkdocs-click README](https://github.com/mkdocs/mkdocs-click) - directive syntax and nested group support
- [mkdocs-typer2 README](https://github.com/syn54x/mkdocs-typer2) - directive syntax, engine options
- [Material for MkDocs - Creating your site](https://squidfunk.github.io/mkdocs-material/creating-your-site/) - minimal mkdocs.yml configuration

### Tertiary (LOW confidence)
- mkdocs-click + Typer compatibility via TyperGroup being a Click Group subclass -- verified locally but no official documentation confirms this pattern

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all packages verified on PyPI with current versions
- Architecture: HIGH - mkdocs.yml structure and dependency groups are well-documented patterns
- Pitfalls: MEDIUM - strict mode edge cases need validation during implementation
- Plugin choice: MEDIUM - both plugins should work but need hands-on testing

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable ecosystem, 30-day validity)
