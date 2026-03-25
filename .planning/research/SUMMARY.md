# Project Research Summary

**Project:** Navigator v1.1 Documentation
**Domain:** MkDocs documentation site for a Python CLI tool
**Researched:** 2026-03-25
**Confidence:** HIGH

## Executive Summary

Navigator v1.1 is a documentation milestone adding a static docs site and README to an existing, working Python CLI tool. This is a mature, well-understood domain — the toolchain (MkDocs + Material + mkdocs-typer2/mkdocs-click) is the de facto standard across the Python ecosystem (uv, Typer, Ruff, FastAPI all use it). The recommended approach is a docs-as-code pattern with an auto-generated CLI reference and hand-written narrative guides, organized around user tasks rather than code structure. The docs serve two audiences: the developer recalling how the tool works, and Claude Code agents discovering the CLI API — neither needs versioned docs, a deployment pipeline, or internal API reference.

The primary risk is not technical — it is scope creep. MkDocs Material is feature-rich and it is easy to over-engineer docs for a private single-user tool. A second major risk is documentation drift: if the CLI reference is hand-written instead of auto-generated, it will become unreliable within weeks. Both risks have clear preventions that must be established in the first phase (foundation setup), not bolted on later. The MkDocs ecosystem is in a transitional period (Material entering maintenance mode, MkDocs 2.0 breaking the plugin ecosystem), but the current stack is stable for years — pin `mkdocs<2` and proceed.

The implementation is purely additive — no existing Navigator source code needs modification. The docs layer reads the existing Typer app at build time to produce the CLI reference automatically, and new `.md` files provide the narrative content. Total scope is approximately 14 pages across 6 phases.

## Key Findings

### Recommended Stack

The documentation stack adds four packages to the existing Navigator project as an isolated dependency group. MkDocs 1.6.1 (pinned `<2` to avoid the incompatible 2.0 rewrite), mkdocs-material 9.7.6 (all former Insiders features now free, Material is the dominant Python docs theme), and either mkdocs-typer2 0.1.6 or mkdocs-click (for CLI auto-generation from the Typer app). All packages install via `uv sync --group docs` without affecting the runtime or dev dependency graph. Note: STACK.md recommends mkdocs-typer2; PITFALLS.md recommends mkdocs-click — this conflict must be resolved by testing both against Navigator's nested subcommand structure before Phase 1 begins.

**Core technologies:**
- `mkdocs>=1.6.1,<2`: Static site generator — pin `<2` to avoid the ecosystem-breaking 2.0 rewrite; 1.6.1 is stable and feature-complete
- `mkdocs-material>=9.7,<10`: Theme — dominant Python docs theme; 9.7.0 made all Insiders features free; maintenance mode is fine for this use case
- `mkdocs-typer2>=0.1.6` or `mkdocs-click`: CLI auto-generation — reads the live Typer `app` object at build time; `mkdocs-click` is safer long-term (MkDocs org maintained); `mkdocs-typer2` is Typer-native; test both for nested subcommand support
- `pymdown-extensions`: Markdown extensions for admonitions, code highlighting, tabbed content — transitive dependency of Material, do not pin explicitly

### Expected Features

The feature set for a 14-page docs site serving the developer and Claude Code agents is clearly scoped. The three-phase priority model from FEATURES.md maps cleanly to implementation phases.

**Must have (table stakes):**
- README.md with install, quick-start, feature overview — first thing anyone sees; must be under 150 lines and point to the docs site for depth
- MkDocs project scaffolding (mkdocs.yml, docs/ directory, theme config) — foundation for all other docs
- Auto-generated CLI reference — covers all 18 commands/subcommands without drift risk
- Installation guide — prerequisites, install steps, `navigator doctor` verification
- Getting started tutorial — self-contained narrative from install to first scheduled command
- Configuration reference — every config key, type, and default from the Pydantic config model
- Feature guides (one per major capability): scheduling, watching, chaining, secrets, namespaces, systemd

**Should have (differentiators):**
- Claude Code integration guide — unique to Navigator; explains how agents discover the CLI via `--help` and `--output json`
- Real-world workflow examples — 2-3 end-to-end pipeline examples combining multiple features
- `mkdocs build --strict` in the dev workflow — maintenance convention establishing docs longevity

**Defer (future only if needed):**
- Architecture/design decisions page — low priority for a private tool
- JSON output schema documentation — only if external integrations emerge
- GitHub Pages deployment — only if the project becomes public

### Architecture Approach

The docs layer is purely additive: `mkdocs.yml` and `docs/` directory at the project root, a `[dependency-groups] docs` entry in pyproject.toml, and `site/` added to `.gitignore`. No source code changes are needed. At build time, the CLI auto-generation plugin imports `navigator.cli:app`, walks the Click/Typer command tree, and renders the full CLI reference automatically. Hand-written `.md` files cover narrative guides, tutorial, and configuration reference.

**Major components:**
1. `mkdocs.yml` — central configuration: theme, nav, plugins, markdown extensions; lives at project root
2. `docs/` — Markdown source organized as `getting-started/`, `guides/`, `reference/`; approximately 14 files
3. CLI auto-generation plugin — reads live `navigator.cli:app` at build time; CLI reference stays current automatically with no manual maintenance
4. Material theme — search, dark mode, nav tabs, code copy buttons, admonitions; zero extra configuration beyond enabling built-in features
5. `README.md` — standalone, not part of MkDocs; under 150 lines; entry point that links to the docs site

### Critical Pitfalls

1. **Documentation drift** — Hand-writing the CLI reference is the single most costly mistake; it becomes unreliable within weeks. Use `mkdocs-typer2` or `mkdocs-click` for auto-generation. This must be the foundation of Phase 1, not an afterthought. Warning sign: CLI reference pages contain hardcoded option lists instead of auto-generation directives.

2. **Package not importable at build time** — Auto-generation plugins need `navigator` importable in the build environment. The build must run `uv pip install -e .` before `mkdocs build`. Validate this in Phase 1 with a trivial CLI reference page before writing any content. Warning sign: `mkdocs build` fails with `ModuleNotFoundError`.

3. **Over-engineering for a private tool** — MkDocs Material makes it tempting to enable versioned docs (mike), a blog plugin, API reference for internal modules, and deployment pipelines. None serve the two actual audiences. Lock scope in Phase 1: no `mike`, no blog, no `docs/api/` directory, `mkdocs.yml` under 10 plugins. Warning sign: more time spent configuring tooling than writing content.

4. **README duplicating the docs site** — Without a clear boundary, README and docs pages cover the same ground and diverge. Hard rule: README is under 150 lines, contains no CLI reference table, and links to docs for everything beyond install + quick-start. Warning sign: README exceeds 200 lines or has a table of contents with more than 5 entries.

5. **Plugin fragmentation** — `mkdocs-typer` (original) is dormant since June 2023 and breaks with current Typer. Use `mkdocs-click` or `mkdocs-typer2`. Test against Navigator's nested subcommand groups (`app.add_typer(namespace_app)`) in Phase 1 — this specific pattern may behave differently across plugins.

6. **Docs fossilizing after the milestone** — The v1.1 milestone must deliver a maintenance convention in addition to content. Add `mkdocs build --strict` to the dev workflow and include "update docs" in future milestone completion criteria.

## Implications for Roadmap

Both FEATURES.md and ARCHITECTURE.md independently converged on the same 5-6 phase build order. The ordering is driven by hard dependencies: auto-generation plugins require a working MkDocs setup; narrative guides need the CLI reference to cross-link to; and the README benefits from having consistent installation docs to reference.

### Phase 1: Foundation Setup
**Rationale:** All subsequent phases depend on this. The MkDocs project must exist and build successfully before any content is written. Plugin choice must be resolved here — it is expensive to change later.
**Delivers:** Working MkDocs skeleton that builds cleanly; docs dependency group in pyproject.toml; `site/` in .gitignore; plugin validated with Navigator CLI introspection; build pipeline confirmed end-to-end
**Addresses:** Auto-generation plugin selection (mkdocs-click vs mkdocs-typer2), dependency group isolation pattern, build environment setup
**Avoids:** Package import failure (Pitfall 6), wrong plugin choice (Pitfall 4), scope overrun (Pitfall 2 locked out at setup time)

### Phase 2: CLI Reference
**Rationale:** The highest-value single page and the fastest to produce (auto-generated). Validates the full pipeline with real Navigator CLI introspection. May surface the need to improve `--help` strings in `cli.py` before writing narrative guides.
**Delivers:** `docs/reference/cli.md` covering all 18 commands/subcommands, auto-generated from live Typer app; review pass of `cli.py` help strings for completeness
**Uses:** CLI auto-generation plugin configured in Phase 1
**Implements:** The "auto-generated reference, hand-written guides" architecture boundary

### Phase 3: Getting Started
**Rationale:** The narrative entry point that all feature guides assume the reader has completed. Writing this before guides ensures a consistent install baseline and forces clarity on the user's starting state.
**Delivers:** `docs/getting-started/installation.md` (prerequisites, install steps, doctor verification) and `docs/getting-started/quickstart.md` (self-contained: register + execute + schedule + verify logs)
**Uses:** Hand-written Markdown cross-referencing Phase 2 CLI reference for command details

### Phase 4: Feature Guides
**Rationale:** The bulk of the docs content. Each guide is independent and can be written in any order within the phase. All reference the CLI docs from Phase 2 rather than duplicating option descriptions.
**Delivers:** Six feature guides (scheduling, watching, chaining, secrets, namespaces, systemd) plus the Claude Code integration guide (7 pages total)
**Avoids:** Module-oriented organization (UX pitfall) — guides are organized by user task, not code structure

### Phase 5: README.md
**Rationale:** Written after guides so install instructions are consistent with the installation guide, and the quick-start matches the tutorial. Strict scope boundary enforced at creation time.
**Delivers:** README.md under 150 lines: 2-3 sentence description, uv+pip install paths, 4-5 command quick-start, link to full docs
**Avoids:** README duplicating docs site (Pitfall 3); content boundary enforced at creation time, not retrofit later

### Phase 6: Polish and Conventions
**Rationale:** Validate the complete site and establish the maintenance workflow so docs do not fossilize after this milestone is closed.
**Delivers:** `mkdocs build --strict` passes with zero warnings; navigation audit (all 14 pages reachable, no orphans); configuration reference verified against `navigator config show` output; "update docs" added to future milestone templates; workflow examples (optional if time permits)
**Avoids:** Docs fossilization (Pitfall 5); all items from PITFALLS.md "looks done but isn't" checklist addressed

### Phase Ordering Rationale

- Phase 1 before everything: MkDocs build pipeline must exist before any content phases
- Phase 2 before guides: guides should cross-link to specific commands; having the reference live when writing guides ensures accurate links
- Phase 3 before Phase 4: feature guides assume the reader completed the tutorial; writing tutorial first locks in the assumed baseline
- Phase 5 after Phase 3: README install instructions must match the installation guide exactly
- Phase 6 last: strict-mode validation and navigation audit only meaningful when all content exists
- README is MkDocs-independent but intentionally written after guides to prevent content divergence

### Research Flags

All phases use standard, well-documented patterns. No phase requires `/gsd:research-phase` during planning.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** MkDocs scaffolding and `uv` dependency groups are thoroughly documented with working examples
- **Phase 2 (CLI Reference):** Both candidate plugins have documentation and working examples; Typer-on-Click pattern is well-understood
- **Phase 3 (Getting Started):** Pure Markdown writing; uv/Typer/Ruff docs provide strong reference patterns
- **Phase 4 (Feature Guides):** Hand-written narrative content following standard CLI tool docs patterns
- **Phase 5 (README):** pyOpenSci guidelines and makeareadme.com cover this completely
- **Phase 6 (Polish):** `mkdocs build --strict` is a single-flag addition; checklist items are well-defined

One pre-Phase-1 decision (not a research phase — a 15-minute test):
- **Plugin choice:** Run both `mkdocs-click` and `mkdocs-typer2` against Navigator's nested `app.add_typer()` subcommand structure. Pick whichever correctly renders all subcommands. Default to `mkdocs-click` if both work equally (MkDocs org maintained, larger community).

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All package versions verified against PyPI on 2026-03-25; ecosystem stability caveat (MkDocs 2.0 transition) is well-documented and the mitigation (pin `<2`) is definitive |
| Features | HIGH | Cross-validated against uv, Typer, and Ruff documentation patterns; 18 commands/subcommands verified from Navigator CLI source |
| Architecture | HIGH | Standard MkDocs docs-as-code pattern; component responsibilities and data flow are established and confirmed against Navigator's existing codebase structure |
| Pitfalls | HIGH | Grounded in Navigator-specific codebase inspection (cli.py Typer structure, pyproject.toml dependency layout); common MkDocs pitfalls corroborated by multiple independent sources |

**Overall confidence:** HIGH

### Gaps to Address

- **Plugin choice conflict (mkdocs-click vs mkdocs-typer2):** STACK.md recommends mkdocs-typer2; PITFALLS.md recommends mkdocs-click. Both are valid choices. Resolve by testing nested subcommand generation before Phase 1 begins — 15 minutes, not a blocker for planning.
- **`--help` string quality in cli.py:** Auto-generation produces docs from Typer help strings verbatim. If strings are terse or missing, the CLI reference will be poor. FEATURES.md flags this explicitly. Include a help-string review pass as part of Phase 2 scope.
- **`navigator doctor` output:** The installation guide troubleshooting section depends on knowing what `navigator doctor` checks. Read `doctor.py` before writing the installation guide in Phase 3.

## Sources

### Primary (HIGH confidence)
- [mkdocs-material PyPI](https://pypi.org/project/mkdocs-material/) — version 9.7.6 verified 2026-03-25
- [mkdocs PyPI](https://pypi.org/project/mkdocs/) — version 1.6.1 verified 2026-03-25
- [mkdocs-typer2 GitHub](https://github.com/syn54x/mkdocs-typer2) — version 0.1.6, requirements verified
- [mkdocs-click GitHub](https://github.com/mkdocs/mkdocs-click) — MkDocs org maintained; works with Typer via Click compatibility
- [MkDocs 2.0 blog post](https://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/) — ecosystem transition details; confirms pin `<2` strategy
- [mkdocs-material Insiders announcement](https://squidfunk.github.io/mkdocs-material/blog/2025/11/11/insiders-now-free-for-everyone/) — all features free in 9.7.0
- [Material for MkDocs built-in plugins](https://squidfunk.github.io/mkdocs-material/plugins/) — plugin reference
- [uv dependency management](https://docs.astral.sh/uv/concepts/projects/dependencies/) — dependency-groups vs optional-dependencies
- [uv documentation site](https://docs.astral.sh/uv/guides/) — exemplary CLI docs structure reference
- Navigator codebase (`src/navigator/cli.py`) — verified Typer app with nested subcommand groups (18 commands/subcommands)
- Navigator `pyproject.toml` — verified dependency structure, entry points, existing stack

### Secondary (MEDIUM confidence)
- [pyOpenSci README best practices](https://www.pyopensci.org/python-package-guide/documentation/repository-files/readme-file-best-practices.html) — README structure guidelines
- [Typer mkdocs.yml](https://github.com/fastapi/typer/blob/master/mkdocs.yml) — real-world Typer project docs configuration
- [Real Python: Build Your Python Project Documentation With MkDocs](https://realpython.com/python-project-documentation-with-mkdocs/) — practical setup guide covering common pitfalls
- [Documentation Drift analysis](https://gaudion.dev/blog/documentation-drift) — prevention strategies
- [makeareadme.com](https://www.makeareadme.com/) — README structure patterns

---
*Research completed: 2026-03-25*
*Ready for roadmap: yes*
