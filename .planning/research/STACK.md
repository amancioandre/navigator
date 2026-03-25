# Stack Research: v1.1 Documentation

**Domain:** MkDocs documentation site for a Python CLI tool
**Researched:** 2026-03-25
**Confidence:** HIGH

## Context

This research covers ONLY the stack additions for the v1.1 Documentation milestone. The existing Navigator stack (Typer, Pydantic, Rich, watchdog, python-crontab, etc.) is validated and unchanged. We are adding a documentation site built with MkDocs and a comprehensive README.

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| mkdocs | 1.6.1 | Static site generator | The standard Python documentation SSG. Pin to `>=1.6.1,<2` because MkDocs 2.0 is a ground-up rewrite that removes the plugin system and theme architecture -- it is incompatible with Material and the entire plugin ecosystem. 1.6.1 is the latest 1.x release (Aug 2024) and is stable. | HIGH |
| mkdocs-material | 9.7.6 | Theme | The dominant MkDocs theme -- used by FastAPI, Pydantic, Typer, and most major Python projects. Version 9.7.0 released ALL former Insiders features to the public (search highlighting, annotations, content tabs, code copy, instant navigation). 9.7.6 (March 2026) pins `mkdocs<2` automatically. Now in maintenance mode (bug/security fixes until Nov 2026), but this is fine -- the feature set is complete and mature. | HIGH |
| pymdown-extensions | 10.21 | Markdown extensions | Required by mkdocs-material for admonitions, code highlighting, tabbed content, task lists, emoji, and more. Actively maintained (Feb 2026 release). Provides `superfences`, `tabbed`, `tasklist`, `highlight`, `details`, and other extensions that make CLI docs readable. | HIGH |

### Supporting Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| mkdocs-typer2 | 0.1.6 | Auto-generate CLI reference | Generates Markdown docs from Typer CLI apps automatically. Uses Typer's built-in `utils docs` command. Add a `:::mkdocs-typer2` directive in your Markdown and it renders the full command tree with options, arguments, and help text. Requires Python >=3.10, Typer >=0.12.5, Pydantic >=2.9.2 -- all satisfied by existing stack. | HIGH |
| mkdocs-section-index | ~0.3 | Section index pages | Allows a section (directory) to also be a page. Without this, clicking a nav section heading does nothing. With it, `docs/guides/index.md` serves as both the section page and the link target. Small, zero-config. | MEDIUM |
| mkdocs-git-revision-date-localized-plugin | ~1.4 | "Last updated" dates | Adds "last updated" timestamps to each page based on git history. Useful for docs that evolve -- readers know if content is current. Only if you want timestamps; skip if you want minimal build dependencies. | LOW |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv (existing) | Install docs dependencies | Add mkdocs packages to `[dependency-groups] docs` in pyproject.toml. Run with `uv run mkdocs serve`. No new tooling needed. |

## MkDocs Material Built-in Plugins to Enable

These ship with mkdocs-material and require NO extra packages -- just configuration in `mkdocs.yml`:

| Plugin/Feature | Purpose | Why Use It |
|----------------|---------|------------|
| search | Full-text search | Built into Material. Zero config. Readers can find any CLI command or concept. |
| tags | Page tagging | Tag pages by topic (scheduling, watching, chaining). Generates a tags index page. Formerly Insiders-only, now free in 9.7.0. |
| navigation.tabs | Top-level nav tabs | Separates "Getting Started", "Guides", "CLI Reference", "Configuration" into tabs. Makes large docs navigable. |
| navigation.sections | Expandable nav groups | Groups related pages in sidebar. Better than flat list for 10+ pages. |
| navigation.instant | SPA-like navigation | Loads pages without full reload. Feels fast. |
| content.code.copy | Copy button on code blocks | Essential for CLI docs -- users copy-paste commands constantly. |
| content.tabs.link | Synced content tabs | When showing different OS install instructions or shell variants, tabs sync across the page. |

## Recommended Markdown Extensions

Configure these in `mkdocs.yml` -- they come from `pymdown-extensions` (installed as a dependency of mkdocs-material):

| Extension | Purpose | Why |
|-----------|---------|-----|
| `pymdownx.highlight` | Syntax highlighting | CLI output, config files, Python code in docs. |
| `pymdownx.superfences` | Fenced code blocks + Mermaid | Nested code blocks, custom fences. Enable Mermaid for architecture diagrams if needed. |
| `pymdownx.tabbed` | Content tabs | Show different install methods (pip vs uv) side by side. |
| `pymdownx.details` | Collapsible sections | Hide verbose output or advanced options behind expandable sections. |
| `pymdownx.snippets` | Include external files | Pull real config examples or code from the repo into docs. Keeps docs in sync with actual code. |
| `admonition` | Callout boxes | Warning, note, tip, danger boxes. Standard Markdown extension (not pymdown). |
| `attr_list` | Attribute lists | Required for some Material features like button styling. |
| `def_list` | Definition lists | Good for CLI option reference formatting. |
| `toc` (with `permalink: true`) | Table of contents | Adds anchor links to headings. Essential for linking to specific sections. |

## Installation

```bash
# Add docs dependency group to pyproject.toml
uv add --group docs mkdocs mkdocs-material mkdocs-typer2 mkdocs-section-index

# Serve docs locally
uv run mkdocs serve

# Build static site
uv run mkdocs build
```

**pyproject.toml addition:**
```toml
[dependency-groups]
docs = [
    "mkdocs>=1.6.1,<2",
    "mkdocs-material>=9.7,<10",
    "mkdocs-typer2>=0.1.6",
    "mkdocs-section-index>=0.3",
]
```

Note: `pymdown-extensions` is a transitive dependency of `mkdocs-material` -- do NOT add it explicitly. Let mkdocs-material manage the compatible version.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| mkdocs-material | Sphinx + furo | If you need autodoc for Python API (class/function docs from docstrings). Navigator is a CLI tool, not a library -- users interact via the CLI, not Python imports. MkDocs is simpler, faster to write, and Material's UX is superior for end-user docs. |
| mkdocs-material | Docusaurus | If docs were JS/React ecosystem. Python project should use Python tooling -- same `uv run` workflow, same dependency management. |
| mkdocs-typer2 | mkdocs-click | mkdocs-click (v0.9.0) works with Click apps. Since Typer wraps Click, it partially works, but mkdocs-typer2 uses Typer's native doc generation and handles Typer-specific features (type hints, rich help) better. |
| mkdocs-typer2 | Manual CLI docs | If the CLI is very small or has unusual output formatting. Navigator has 20+ subcommands across multiple groups -- manual docs would drift from implementation. Auto-generation keeps them in sync. |
| mkdocs-typer2 | mkdocs-typer (original) | The original mkdocs-typer by bruce-szalwinski is inactive/unmaintained. mkdocs-typer2 is a maintained fork that works with current Typer versions. |
| Dependency group | Separate docs/requirements.txt | Never. The project uses uv with pyproject.toml. Dependency groups (`[dependency-groups] docs`) are the correct pattern -- they install only when needed (`uv sync --group docs`) and keep all deps in one lockfile. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| MkDocs 2.0 | Removes plugin system, theme support, and YAML config. Incompatible with Material, mkdocs-typer2, and all community plugins. No license specified. Closed contribution model. | Pin `mkdocs>=1.6.1,<2` |
| Sphinx | Overkill for CLI user docs. RST syntax is harder to write than Markdown. autodoc is irrelevant -- Navigator exposes a CLI, not a Python API. Slower build times, worse default UX. | MkDocs + Material |
| mkdocs-material Insiders | No longer exists as a separate product. All features shipped in 9.7.0 for free. Do not pay for or configure Insiders access. | mkdocs-material >=9.7 |
| Zensical | The mkdocs-material team's next-gen SSG. Pre-release, not yet stable, and mkdocs-material 9.7.x works perfectly for this project's needs. Revisit only if MkDocs 1.x becomes unsupported. | mkdocs 1.6.1 + mkdocs-material 9.7.x |
| mkdocs-pdf-export / mkdocs-with-pdf | Bloated plugins that add wkhtmltopdf or weasyprint dependencies. A personal CLI tool's docs do not need PDF export. Adds build complexity for zero value. | Skip entirely |
| mkdocs-awesome-pages-plugin | Reorders nav based on YAML files in each directory. Overkill -- define nav structure explicitly in mkdocs.yml. Explicit is better than implicit for a project this size. | Explicit `nav:` in mkdocs.yml |
| mike (versioned docs) | Deploys multiple doc versions to GitHub Pages. Navigator is a personal tool with one version in use. Versioned docs add complexity with no audience to serve. | Single-version docs |

## Stack Patterns by Variant

**If deploying docs to GitHub Pages:**
- Add `mkdocs gh-deploy` to a GitHub Action or run manually
- Material handles the `site/` output directory
- Because GitHub Pages is free and the repo is already on GitHub

**If keeping docs local-only:**
- `uv run mkdocs build` generates `site/` directory
- Serve with any static file server or just open `site/index.html`
- Because Navigator is a private tool -- docs may not need public hosting

**If CLI reference drifts from mkdocs-typer2 output:**
- Write CLI reference manually in Markdown
- Use `pymdownx.snippets` to include `--help` output from build scripts
- Because auto-generation is only valuable if it produces good output

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| mkdocs 1.6.1 | mkdocs-material 9.7.x | Material 9.7.5+ pins `mkdocs<2` automatically |
| mkdocs-material 9.7.x | pymdown-extensions >=10.x | Transitive dependency, version managed by Material |
| mkdocs-typer2 0.1.6 | Typer >=0.12.5, Pydantic >=2.9.2 | Navigator has Typer 0.24.x and Pydantic 2.12.x -- both satisfy |
| mkdocs-typer2 0.1.6 | Python >=3.10 | Navigator targets >=3.12 -- satisfied |
| mkdocs-typer2 0.1.6 | mkdocs >=1.6.1 | Satisfied by our pin |
| mkdocs-section-index ~0.3 | mkdocs >=1.2 | Broadly compatible |

## Critical Note: MkDocs Ecosystem Stability

The MkDocs ecosystem is in a transitional period (March 2026):

1. **MkDocs core** has not released since Aug 2024 (1.6.1). MkDocs 2.0 is a controversial rewrite that breaks the ecosystem.
2. **mkdocs-material** is in maintenance mode (bug fixes until Nov 2026). The team is building Zensical as a successor.
3. **The current stack (MkDocs 1.6.1 + Material 9.7.x) is stable and feature-complete.** It will work fine for years -- these are static site generators, not rapidly-moving targets.
4. **Pin `mkdocs<2`** to avoid accidental breakage if MkDocs 2.0 lands in PyPI.
5. **If MkDocs 1.x becomes unmaintained**, Zensical is designed as a drop-in replacement. Migration would be minimal.

This is a "use now, migrate later if needed" situation. The stack is mature and the docs it produces are excellent.

## Sources

- [mkdocs-material PyPI](https://pypi.org/project/mkdocs-material/) -- version 9.7.6 verified
- [mkdocs PyPI](https://pypi.org/project/mkdocs/) -- version 1.6.1 verified
- [MkDocs 2.0 blog post](https://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/) -- ecosystem transition details
- [mkdocs-material Insiders announcement](https://squidfunk.github.io/mkdocs-material/blog/2025/11/11/insiders-now-free-for-everyone/) -- all features now free
- [mkdocs-typer2 GitHub](https://github.com/syn54x/mkdocs-typer2) -- version 0.1.6, requirements
- [mkdocs-click PyPI](https://pypi.org/project/mkdocs-click/) -- version 0.9.0, for comparison
- [pymdown-extensions PyPI](https://pypi.org/project/pymdown-extensions/) -- version 10.21
- [Material for MkDocs built-in plugins](https://squidfunk.github.io/mkdocs-material/plugins/) -- plugin reference

---
*Stack research for: Navigator v1.1 Documentation milestone*
*Researched: 2026-03-25*
