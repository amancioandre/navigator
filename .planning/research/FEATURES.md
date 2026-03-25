# Feature Research

**Domain:** Documentation for a Python CLI orchestrator tool (v1.1 milestone)
**Researched:** 2026-03-25
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist in any well-documented CLI tool. Missing these means the docs feel incomplete or unusable.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| README.md with installation instructions | First thing anyone sees on the repo. Without it, project looks abandoned or internal-only. | LOW | Copy-paste-ready `uv tool install` and `pip install` commands. Must cover both uv and pip paths. |
| README.md quick-start example | Users want to go from install to working in 60 seconds. A wall of text without a runnable example loses people. | LOW | Show register + exec in 3-4 commands. End-to-end from zero to first command running. |
| README.md feature overview | Users scan for "does this do what I need?" before reading anything else. | LOW | Bullet list or short table of capabilities: scheduling, watching, chaining, secrets, namespaces, systemd. |
| CLI reference for all commands | Users expect to find every flag and argument documented somewhere searchable. `--help` is good but not browsable. | MEDIUM | 18 commands/subcommands to document. Use mkdocs-typer2 to auto-generate from Typer app -- avoids manual sync drift. Depends on: clean `--help` strings in cli.py. |
| Installation guide (docs site) | Expanded version of README install section. Covers prerequisites (Python 3.12+, uv), troubleshooting, verifying install. | LOW | Single page. Include `navigator doctor` verification step. |
| Getting started tutorial | Walk-through from install to a useful outcome. Table stakes for any tool with more than 5 commands. | MEDIUM | Should register a command, execute it, schedule it, then show logs. Narrative flow, not reference. |
| Configuration reference | Users need to know what goes in `~/.config/navigator/config.toml` and what the defaults are. | LOW | Document every config key, type, default value. Single page. Depends on: config.py and the Pydantic model. |
| Feature guides (one per major capability) | Each major feature (scheduling, watching, chaining, secrets, namespaces, systemd) needs its own guide page. Users come with a specific task ("I want to schedule something") and need focused instructions. | MEDIUM | 6 guides total. Each is 1-2 pages with examples. This is the bulk of the documentation work. |

### Differentiators (Competitive Advantage)

Features that make Navigator's docs stand out from typical CLI tools. Not required, but signal quality and thoughtfulness.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Claude Code integration guide | Navigator's core audience is Claude Code users. A dedicated guide showing how agents discover and use the CLI (via `--help` and `--output json`) is unique to this tool. No other orchestrator has this. | LOW | Short guide: how Claude Code reads `--help`, how `--output json` enables machine parsing, example agent prompts that use Navigator. |
| Real-world workflow examples | Goes beyond "here's the flag" to "here's how you'd actually set up a daily content pipeline." Connects features into workflows that match the user's actual use cases (Gamescout content, Obsidian automation). | MEDIUM | 2-3 examples: daily content pipeline, file-triggered processing, chained multi-step workflow. Uses multiple features together. |
| Architecture/design decisions page | Explains why system crontab instead of APScheduler, why subprocess isolation, why CLI-first. Builds trust and helps users understand the tool's mental model. | LOW | Already documented in STACK.md research. Mostly prose, no code examples needed. |
| JSON output documentation | Navigator supports `--output json` for machine-readable output. Documenting the JSON schemas for each command's output enables programmatic integration beyond Claude Code. | MEDIUM | Requires documenting the JSON shape for each command. Could be auto-generated from Pydantic output models if they exist. |
| Searchable docs site | MkDocs Material includes built-in search. Users expect to search "cron" and find the scheduling guide. Zero extra work with Material theme. | LOW | Comes free with mkdocs-material. Just configure it. |
| Copy-to-clipboard on code blocks | Small UX touch that signals polished docs. Users copy-paste CLI commands constantly. | LOW | Built into mkdocs-material. Single config line in mkdocs.yml. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create maintenance burden or actively harm the documentation.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| API reference auto-generated from all docstrings | "Document everything" instinct. Seems thorough. | Navigator is a CLI tool, not a library. Users interact via the CLI, not by importing Python modules. Auto-generated API docs from internal modules (db.py, executor.py, models.py) creates noise that no user will read. Maintenance burden for zero user value. | Auto-generate CLI reference only (mkdocs-typer2). Keep internal code docs as inline comments/docstrings for developers, not in the public docs site. |
| Hosted docs on Read the Docs or GitHub Pages | "Docs should be online." | This is a private, single-user tool. Hosting docs publicly is unnecessary and the deployment pipeline is maintenance overhead. The docs site is for local `mkdocs serve` or building a static site locally. | Build locally with `mkdocs build` or `mkdocs serve`. If hosting is ever wanted, GitHub Pages is trivial to add later -- the MkDocs structure supports it with zero changes. |
| Changelog page in docs | "Users want to know what changed." | For a single-user private tool, the git log is the changelog. Maintaining a separate CHANGELOG.md that duplicates git history is busywork. | Git log and GitHub releases (if ever published). Omit from docs site. |
| Video tutorials or GIFs | "Visual learners need videos." | Videos go stale faster than text. Every CLI flag change requires re-recording. For a rapidly evolving private tool, this is a maintenance trap. | Good code examples with expected output shown as text. Terminal output is already visual thanks to Rich formatting. |
| Exhaustive troubleshooting page | "Cover every possible error." | Impossible to predict all errors upfront. Becomes a dumping ground of unstructured Q&A that nobody maintains. | `navigator doctor` command already handles diagnostics. Document the doctor command output and common issues in the installation guide. Add troubleshooting tips to individual feature guides where relevant. |
| Multi-language / i18n docs | "Accessibility." | Single-user tool. English only. Adding i18n infrastructure for one reader is absurd overhead. | English only. |

## Feature Dependencies

```
[MkDocs project setup]
    |
    |-- requires --> [mkdocs.yml configuration]
    |                    |
    |                    |-- requires --> [docs/ directory structure]
    |                    |
    |                    |-- requires --> [mkdocs-material theme installed]
    |                    |
    |                    +-- requires --> [mkdocs-typer2 plugin installed]
    |
    +-- enables --> [All documentation pages]

[CLI reference (auto-generated)]
    |
    +-- requires --> [mkdocs-typer2 plugin]
    +-- requires --> [Clean --help strings in cli.py]
    +-- requires --> [MkDocs project setup]

[README.md]
    |
    +-- independent (no MkDocs dependency)
    +-- should link to --> [docs site pages] (if hosted)

[Feature guides]
    |
    +-- requires --> [Getting started tutorial] (guides assume reader completed tutorial)
    +-- requires --> [CLI reference exists] (guides reference specific commands)

[Getting started tutorial]
    |
    +-- requires --> [Installation guide]
    +-- requires --> [CLI reference exists] (for cross-linking)

[Configuration reference]
    |
    +-- requires --> [MkDocs project setup]
    +-- depends on --> [config.py / Pydantic config model in codebase]

[Workflow examples]
    |
    +-- requires --> [Feature guides complete] (examples combine features)
```

### Dependency Notes

- **CLI reference requires clean --help strings:** mkdocs-typer2 generates docs from the Typer app's help text. If help strings are terse or missing, the auto-generated reference will be poor. May need a pass over cli.py to improve help text before generating docs.
- **Feature guides require getting started tutorial:** Guides assume familiarity with basic concepts (registering a command, executing it). The tutorial establishes this baseline.
- **README.md is independent:** Can be written first with no MkDocs dependency. Should be done early as it provides immediate value.
- **Workflow examples require feature guides:** Examples combine multiple features, so the individual feature docs must exist first for cross-references.

## MVP Definition

### Phase 1: Foundation (do first)

- [ ] README.md with install, quick-start, feature overview -- highest immediate value, zero tooling dependency
- [ ] MkDocs project scaffolding (mkdocs.yml, docs/ directory, theme config)
- [ ] Installation guide page
- [ ] Auto-generated CLI reference via mkdocs-typer2

### Phase 2: Core Content (do second)

- [ ] Getting started tutorial (narrative walkthrough)
- [ ] Configuration reference
- [ ] Feature guides: scheduling, watching, chaining (the three most complex features)

### Phase 3: Complete Coverage (do third)

- [ ] Feature guides: secrets, namespaces, systemd
- [ ] Claude Code integration guide
- [ ] Workflow examples (2-3 real-world scenarios)

### Future Consideration (only if needed)

- [ ] Architecture/design decisions page -- nice to have, low priority
- [ ] JSON output schema documentation -- only if external integrations emerge
- [ ] GitHub Pages deployment -- only if the tool becomes shared

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| README.md (install + quick-start + overview) | HIGH | LOW | P1 |
| MkDocs project setup | HIGH | LOW | P1 |
| CLI reference (auto-generated) | HIGH | LOW | P1 |
| Installation guide | HIGH | LOW | P1 |
| Getting started tutorial | HIGH | MEDIUM | P1 |
| Configuration reference | MEDIUM | LOW | P1 |
| Feature guide: scheduling | HIGH | MEDIUM | P2 |
| Feature guide: watching | HIGH | MEDIUM | P2 |
| Feature guide: chaining | HIGH | MEDIUM | P2 |
| Feature guide: secrets | MEDIUM | LOW | P2 |
| Feature guide: namespaces | MEDIUM | LOW | P2 |
| Feature guide: systemd | MEDIUM | LOW | P2 |
| Claude Code integration guide | MEDIUM | LOW | P2 |
| Workflow examples | MEDIUM | MEDIUM | P3 |
| Architecture page | LOW | LOW | P3 |
| JSON output docs | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have -- docs are useless without these
- P2: Should have -- fills out the docs site to "complete" coverage
- P3: Nice to have -- polish and depth

## Competitor Feature Analysis

How well-documented CLI tools in the Python ecosystem structure their docs.

| Feature | uv (astral.sh) | Typer (fastapi/typer) | Ruff | Our Approach |
|---------|----------------|----------------------|------|--------------|
| README quick-start | Yes, minimal and effective | Yes, with animated GIF | Yes, concise | Concise text example, no GIF (anti-feature) |
| CLI reference | Auto-generated, comprehensive | Auto-generated from Typer | Auto-generated | mkdocs-typer2 auto-generation |
| Getting started guide | Yes, multi-page tutorial | Yes, extensive tutorial | Yes, single page | Single-page narrative tutorial |
| Feature guides | Yes, one per concept | Yes, one per CLI concept | Yes, organized by rule category | One page per major feature (6 guides) |
| Configuration reference | Yes, comprehensive | N/A (no config file) | Yes, all options documented | Full config.toml reference |
| Search | Yes (Material theme) | Yes (Material theme) | Yes (Material theme) | Yes (Material theme) |
| Architecture docs | No | No | Yes, contributor guide | Optional, low priority |
| Workflow examples | Yes, "Guides" section | Yes, in tutorial | No | Real-world pipeline examples |
| Docs theme | Material for MkDocs | Material for MkDocs | Material for MkDocs | Material for MkDocs |

## Page Structure Recommendation

Based on research of uv, Typer, and Ruff documentation patterns, the docs site should have this navigation:

```yaml
nav:
  - Home: index.md
  - Installation: installation.md
  - Getting Started: getting-started.md
  - Guides:
    - Scheduling (Cron): guides/scheduling.md
    - File Watching: guides/watching.md
    - Command Chaining: guides/chaining.md
    - Secret Management: guides/secrets.md
    - Namespaces: guides/namespaces.md
    - Systemd Service: guides/systemd.md
    - Claude Code Integration: guides/claude-code.md
  - Configuration: configuration.md
  - CLI Reference: cli-reference.md
  - Examples: examples.md
```

Total: approximately 14 pages. This matches the depth of similar tools (uv, Typer, Ruff) while staying manageable for a single-user private tool.

## README.md Structure Recommendation

Based on research of well-received Python CLI READMEs (pyOpenSci guidelines, makeareadme.com patterns):

```markdown
# Navigator

One-line description.

## Features (bullet list, scannable)
## Installation (uv + pip paths)
## Quick Start (4-5 commands, end-to-end)
## Usage Overview (brief per-feature with links to docs)
## Documentation (link to docs site / mkdocs serve instructions)
## Development (for contributors -- uv sync, pytest, ruff)
## License
```

No badges (private tool), no GIFs, no contributing guide, no changelog. Keep it lean. The README is a landing page, not the documentation -- it points to the MkDocs site for depth.

## Codebase Dependencies for Documentation

These existing codebase elements directly affect documentation quality:

| Codebase Element | Documentation Impact | Action Needed |
|------------------|---------------------|---------------|
| cli.py `--help` strings | mkdocs-typer2 uses these verbatim for CLI reference | Review all 18 commands for completeness and clarity |
| config.py / Pydantic config model | Configuration reference page content | Extract all config keys, types, defaults from the model |
| models.py (Pydantic models) | Inform feature guide examples with real field names | Read to ensure examples use correct field names |
| doctor.py | Installation guide troubleshooting section | Document what `navigator doctor` checks |
| output.py (JSON output) | JSON output documentation (if pursued) | Understand output schema shapes |
| pyproject.toml entry point | Installation instructions | Verify `navigator` entry point name |

## Sources

- [mkdocs-typer2 documentation](https://syn54x.github.io/mkdocs-typer2/) -- auto-generating Typer CLI docs
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) -- theme features and configuration
- [pyOpenSci README best practices](https://www.pyopensci.org/python-package-guide/documentation/repository-files/readme-file-best-practices.html) -- README structure guidelines
- [uv documentation site](https://docs.astral.sh/uv/guides/) -- exemplary CLI docs structure pattern
- [Typer mkdocs.yml](https://github.com/fastapi/typer/blob/master/mkdocs.yml) -- real-world Typer project docs configuration
- [mkdocstrings](https://github.com/mkdocstrings/mkdocstrings) -- evaluated and rejected (library API docs, not CLI docs)
- [mkdocs-click](https://github.com/mkdocs/mkdocs-click) -- evaluated, mkdocs-typer2 is the Typer-specific equivalent
- Navigator CLI `--help` output -- verified 18 commands/subcommands to document
- [makeareadme.com](https://www.makeareadme.com/) -- README structure patterns

---
*Feature research for: Python CLI orchestrator documentation (Navigator v1.1)*
*Researched: 2026-03-25*
