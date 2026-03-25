# Pitfalls Research

**Domain:** Adding MkDocs documentation to an existing Python CLI project (Navigator v1.1)
**Researched:** 2026-03-25
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Documentation Drift from Day One

**What goes wrong:**
Hand-written CLI reference docs go stale the moment a command's options change. Someone adds `--timeout` to `navigator run` but nobody updates the docs page. Within weeks the CLI reference is unreliable, and users (including AI agents) learn to distrust the docs and just run `--help` instead -- making the entire docs site dead weight.

**Why it happens:**
CLI code and documentation are in separate files with no automated link between them. Developers update Python code but have no feedback loop telling them the docs are now wrong. Manual doc maintenance requires discipline that erodes over time, especially on a single-person private project where there is no review process.

**How to avoid:**
Use `mkdocs-click` (maintained by the MkDocs organization, works with Typer since Typer wraps Click) to auto-generate CLI reference pages at build time. The CLI reference should be generated from the actual Typer `app` object, never hand-written. For non-CLI docs (guides, tutorials), keep prose minimal and link to the auto-generated reference rather than duplicating option descriptions.

**Warning signs:**
- CLI reference pages contain hardcoded option lists instead of auto-generation directives
- `mkdocs build` succeeds even when CLI signatures have changed (no validation step)
- Docs mention options or commands that no longer exist

**Phase to address:**
Phase 1 (MkDocs setup) -- auto-generation must be the foundation, not bolted on later.

---

### Pitfall 2: Over-Engineering Docs for a Private Single-User Tool

**What goes wrong:**
Building a full documentation site with contribution guidelines, API reference for every internal module, changelog automation, versioned docs, search analytics, and deployment pipelines -- for a tool used by one person on one machine. The docs take longer to build than the features they describe. Maintenance burden kills motivation to update docs at all.

**Why it happens:**
MkDocs Material is feature-rich and it is tempting to enable everything. Open-source documentation patterns (versioned docs, contributor guides, code of conduct) get cargo-culted into private projects. The tooling makes it easy to over-scope.

**How to avoid:**
Navigator's docs serve exactly two audiences: (1) the developer/user recalling how their own tool works, and (2) Claude Code agents discovering the CLI API. Neither audience needs versioned docs, a blog, or contribution guidelines. Scope the docs to:
- README.md: install, quick start, link to full docs
- CLI reference: auto-generated, exhaustive
- Feature guides: one page per major capability (scheduling, watching, chaining, secrets, namespaces, systemd)
- Getting started tutorial: one walkthrough from install to first scheduled command

Do NOT build: versioned docs (mike), blog plugin, API reference for internal modules, deployment pipeline, search analytics, contribution guidelines, code of conduct.

**Warning signs:**
- `mkdocs.yml` has more than 10 plugins configured
- Docs site has pages with placeholder content ("Coming soon", "TODO")
- More time spent configuring docs tooling than writing actual content
- Internal implementation modules (db.py, executor.py) appear in the docs navigation

**Phase to address:**
Phase 1 (MkDocs setup) -- scope must be locked before the site structure is created.

---

### Pitfall 3: README.md Duplicates the MkDocs Site

**What goes wrong:**
The README becomes a mini-documentation site of its own -- full CLI reference, every configuration option, all feature descriptions. Now the same information lives in two places. When something changes, one gets updated and the other does not. The README and docs site contradict each other.

**Why it happens:**
The README is written first (or already exists), and content is copied into MkDocs pages. Or vice versa -- MkDocs is built and then the README is expanded to "also be useful standalone." Without a clear boundary, both grow to cover everything.

**How to avoid:**
Define a strict content boundary:
- **README.md**: Project description (2-3 sentences), installation instructions, one quick-start example (register a command + schedule it), link to full docs. Target: under 150 lines, fits on one screen without excessive scrolling.
- **MkDocs site**: Everything else -- CLI reference, feature guides, configuration reference, tutorial.

The README should make someone productive in 2 minutes and then point them to the docs site. It should never contain a CLI reference table or full configuration file examples.

**Warning signs:**
- README.md exceeds 200 lines
- README contains the same code examples as a MkDocs guide page
- README has a table of contents with more than 5 entries
- Updating a feature requires editing both README and a docs page

**Phase to address:**
Phase 2 (README) -- enforce the boundary at creation time.

---

### Pitfall 4: mkdocs-typer Plugin Fragmentation and Staleness

**What goes wrong:**
You pick `mkdocs-typer` (the original), which has not been updated since June 2023 and is marked dormant. It breaks with a newer Typer or MkDocs version. Or you pick `mkdocs-typer2` which is actively maintained but has a small user base (~6K downloads/month). Either way, the auto-generation plugin becomes a single point of failure for the entire CLI reference.

**Why it happens:**
The Typer ecosystem for MkDocs doc generation is fragmented. There are at least three options: `mkdocs-typer` (dormant), `mkdocs-typer2` (active but small), and `mkdocs-click` (official MkDocs org, works with Typer since Typer wraps Click). Developers pick whichever appears first in search results without checking maintenance status.

**How to avoid:**
Evaluate in this priority order:
1. **`mkdocs-click`** -- maintained by the MkDocs organization, works with Typer apps (Typer is built on Click), largest community, most stable long-term bet. This is the recommended choice.
2. **`mkdocs-typer2`** -- actively maintained, Typer-native, pretty table output. Use only if `mkdocs-click` cannot handle a specific Typer pattern.
3. **`typer utils docs` command** -- Typer's built-in doc generation. Can generate Markdown files as a build step. No plugin dependency, but loses MkDocs nav integration.

Whichever is chosen, add a build-time validation: `mkdocs build --strict` catches broken references. If the plugin breaks on upgrade, the build fails immediately rather than silently serving stale docs.

**Warning signs:**
- The chosen plugin's GitHub repo has no commits in 6+ months
- Plugin's issue tracker has open issues matching your Typer/MkDocs version
- CLI reference pages show outdated or missing commands after a code change

**Phase to address:**
Phase 1 (MkDocs setup) -- plugin choice is a foundational decision that is expensive to change later.

---

### Pitfall 5: Treating Docs as a One-Time Deliverable

**What goes wrong:**
Documentation is written as a separate milestone (v1.1), and after the milestone is complete, docs are never touched again. New features in future milestones ship without corresponding doc updates. The docs fossilize at v1.1 while the code evolves.

**Why it happens:**
When documentation is its own milestone, the implicit mental model is "we'll do docs once and move on." Future feature milestones do not include doc update tasks because "docs are already done." Without a build-time check, nobody notices the drift until the docs are useless.

**How to avoid:**
The v1.1 documentation milestone must deliver two things: (1) the initial content, and (2) the maintenance convention. Concretely:
- Add `mkdocs build --strict` to the dev workflow. Strict mode catches broken internal links, missing pages, and plugin errors.
- Feature guide pages should be structured so adding a new feature means adding one new `.md` file and one nav entry in `mkdocs.yml` -- low friction.
- Future milestone phase definitions should include "update docs" as a completion criterion.
- The auto-generated CLI reference (via mkdocs-click) handles code drift automatically. Manual guides are the risk area.

**Warning signs:**
- No `mkdocs build` step in any development workflow
- Feature guides reference old behavior or missing features
- Last commit to `docs/` directory is months older than last commit to `src/`
- New commands appear in `navigator --help` but not in the docs site

**Phase to address:**
Final phase of this milestone -- establish the maintenance convention as the last deliverable.

---

### Pitfall 6: MkDocs Cannot Import the Navigator Package at Build Time

**What goes wrong:**
Auto-generation plugins (`mkdocs-click`, `mkdocs-typer2`, `mkdocstrings`) need to import the Navigator Python package to introspect the CLI. If the package is not installed in the environment where `mkdocs build` runs, the build fails with `ModuleNotFoundError`. This is the single most common MkDocs + Python project integration failure.

**Why it happens:**
Docs dependencies and project dependencies live in different groups. Developers install MkDocs but forget to install the project itself (`uv pip install -e .`). Or the build runs in a fresh environment (CI, new machine) without the editable install.

**How to avoid:**
- Document the docs build command as a two-step process: `uv pip install -e .` then `mkdocs build`.
- Or better: create a single `uv run mkdocs build` setup where `pyproject.toml` has both docs and project deps available.
- Add docs dependencies as a dependency group: `[dependency-groups] docs = ["mkdocs-material", "mkdocs-click"]` in `pyproject.toml`.
- The first thing the docs setup phase should verify is that `mkdocs build` succeeds with a trivial CLI reference page, before writing any content.

**Warning signs:**
- `mkdocs build` fails with `ImportError` or `ModuleNotFoundError`
- Docs build works on the dev machine but fails on a fresh clone
- Auto-generated CLI pages are empty or show errors

**Phase to address:**
Phase 1 (MkDocs setup) -- the build pipeline must be validated before any content is written.

---

### Pitfall 7: Docstring Format Incompatibility with mkdocstrings

**What goes wrong:**
If you use `mkdocstrings` for any API documentation, it only renders Google-style docstrings correctly by default. Navigator's existing code may use reStructuredText, NumPy, or inconsistent docstring styles. The rendered output is malformed -- raw `:param:` directives visible in the HTML, broken formatting, missing parameter descriptions.

**Why it happens:**
Developers write docstrings in whatever style they learned first. mkdocstrings uses `griffe` for parsing, which defaults to Google style. Nobody checks how docstrings render until the docs site is "finished."

**How to avoid:**
This pitfall is mostly avoidable for Navigator because the docs should NOT include internal API reference (see Pitfall 2 -- over-engineering). The CLI reference is auto-generated from Typer's help strings, not from docstrings. However, if any module docs are added later:
- Standardize on Google-style docstrings across the codebase.
- Configure `mkdocstrings` with the correct docstring style in `mkdocs.yml`.
- Add a ruff rule to enforce docstring style consistency.

**Warning signs:**
- Raw `:param name:` or `Args:` text visible in rendered docs
- Parameter tables are missing or empty in mkdocstrings output
- Different pages show different docstring formatting

**Phase to address:**
Not applicable for v1.1 scope (no API docs planned). Flag for future if internal API docs are ever added.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hand-write CLI reference instead of auto-generating | Faster initial setup, no plugin dependency | Every CLI change requires manual doc update; drift is inevitable within weeks | Never for a Typer project -- auto-generation plugins exist and are trivial to configure |
| Put everything in README.md, skip MkDocs entirely | One file to maintain, no build step | README becomes unreadable; no navigation, search, or cross-linking; does not scale past 5 commands | Never for Navigator -- 14+ source modules, 6 feature areas |
| Copy-paste `--help` output into Markdown files | Quick "reference" docs with zero tooling | Output format changes with Typer/Rich updates; stale immediately; no hyperlinks between commands | Never -- auto-generate instead |
| Skip `mkdocs build --strict` validation | Faster builds during drafting | Broken internal links and missing pages accumulate silently; users hit 404s | During initial drafting only; must enable strict before milestone completion |
| Use MkDocs Material Insiders (paid features) | Better UI components (privacy plugin, etc.) | Paid dependency for a private tool; insiders features may not work with all plugins | Never for this project -- free tier is more than sufficient |
| Write docs without installing the package | Faster to start writing prose | Auto-generation plugins fail; blocks the entire CLI reference section | Never -- always `uv pip install -e .` first |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| mkdocs-click with Typer app | Pointing at the module path instead of the Click/Typer app object; plugin fails to resolve | Use the format `:module: navigator.cli` and `:command: app` -- point at the Typer app instance, not just the module |
| mkdocs-click with Typer subcommand groups | Navigator uses `app.add_typer(namespace_app)` for nested commands; plugin may not traverse nested Typer instances | Test that all subcommands (e.g., `navigator namespace create`) appear in the generated output; may need separate directives per subcommand group |
| MkDocs with uv project management | Running `mkdocs serve` outside the venv where Navigator is installed | Use `uv run mkdocs serve` to ensure the project's venv is active, or install docs deps in the project's dev group |
| platformdirs config paths in docs | Documenting paths as hardcoded `~/.config/navigator/` | Document that paths are resolved by platformdirs and may vary; show `navigator config path` output as the canonical way to find paths |
| MkDocs nav with many feature guides | Forgetting to add new pages to `mkdocs.yml` nav -- pages exist but are invisible to users | Use explicit nav in `mkdocs.yml` (not auto-discovery) so missing nav entries are caught during review |
| Raw docstrings in code blocks | MkDocs renders backslash escapes in code examples; `\n` becomes a newline | Use raw strings (`r"""..."""`) in docstrings that contain backslashes, or fence code blocks properly in Markdown |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Installing full MkDocs Material with all optional deps | Slow `uv sync`, bloated venv, slow `mkdocs serve` startup | Only install `mkdocs-material` + the 1-2 plugins actually used; keep docs deps in a separate group | Immediate -- adds 30+ transitive deps for unused features |
| Building docs in the main project venv | Docs plugin versions conflict with project deps; hard to isolate build issues | Use `[dependency-groups] docs` in `pyproject.toml` for docs-only deps | When a docs plugin pulls a conflicting transitive dependency |
| Watching docs directory with Navigator during development | Infinite rebuild loop if `site/` output overlaps with a Navigator watch path | Add `site/` to `.gitignore` and exclude from any Navigator watch patterns | Immediately if project root is watched |
| Using `mkdocs serve` with livereload on large sites | Rebuilds the entire site on every file save; slow for 20+ page sites | Not an issue for Navigator's ~10 pages; only flag if docs grow significantly | 30+ documentation pages |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Including real secret paths or actual API keys in documentation examples | Readers (or AI agents) treat example values as real; leaks if repo is ever shared or backed up | Use obviously fake paths (`/path/to/your/secrets/.env`) and placeholder values (`API_KEY=your-key-here`) in all examples |
| Committing `site/` directory to git | Built HTML may embed local filesystem paths from MkDocs build metadata; unnecessary repo bloat | Add `site/` to `.gitignore` before first `mkdocs build`; never commit built docs |
| Documenting internal network details or machine-specific absolute paths | If repo is ever shared, cloned to another machine, or backed up to cloud, machine-specific details are exposed | Use generic paths and `~` notation in examples; reference `platformdirs` for actual resolution |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Feature guides organized by source module (`db.py`, `executor.py`) instead of user task | User cannot find how to do what they want; has to understand code structure | Organize by user task: "Scheduling Commands", "Watching Files", "Managing Secrets" -- mirror what the user wants to accomplish |
| CLI reference without usage examples | User sees option descriptions but cannot figure out how to combine them for real workflows | Every command section should have at least one realistic example showing the command in a real use case |
| Getting started tutorial that requires reading 3 other pages first | User abandons the tutorial before completing it | Tutorial must be self-contained: install, configure, register first command, schedule it, verify it ran -- all on one page with copy-pasteable commands |
| Docs assume reader remembers all prior context | Returning users (including future-you after 3 months away) cannot use a single guide page without re-reading everything | Each feature guide should be standalone: brief context, prerequisites list, the guide content, next steps links |
| Navigation structure does not match CLI structure | User looks for "namespace" docs under "Commands" but it is under "Features" | Mirror the CLI hierarchy in docs nav: top-level commands at one level, subcommand groups nested |
| No search or inability to find things quickly | User with a specific question scrolls through pages to find the answer | MkDocs Material includes search by default -- ensure it is enabled and that page titles and headings are descriptive |

## "Looks Done But Isn't" Checklist

- [ ] **CLI reference completeness:** Every command and subcommand appears -- run `navigator --help` recursively and compare against docs. Auto-generation handles this if configured correctly.
- [ ] **All options documented:** Global options (`--output`, `--version`) and subcommand-specific options all appear in the reference.
- [ ] **Internal links work:** `mkdocs build --strict` produces zero warnings about broken links or missing anchors.
- [ ] **Examples are runnable:** Copy-paste every example from the docs into a terminal. They should work on a fresh install (or clearly state prerequisites).
- [ ] **Navigation is complete:** Every `.md` file in `docs/` appears in `mkdocs.yml` nav. Orphaned pages are invisible to users.
- [ ] **README links to docs:** README contains a clear note about how to view the full docs (e.g., `mkdocs serve` instructions or file path).
- [ ] **Config reference matches reality:** Documented config options match what `navigator config show` actually produces. No phantom options, no missing new options.
- [ ] **`site/` is gitignored:** Built docs are not committed to the repository.
- [ ] **Docs build from clean state:** Clone the repo fresh, run install + build, docs render correctly. No "works on my machine" assumptions.
- [ ] **Feature guides cover all major features:** Scheduling, watching, chaining, secrets, namespaces, systemd -- each has its own guide page.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| CLI reference drifted from code | LOW | Switch to auto-generation plugin; delete hand-written reference; rebuild. One-time fix. |
| README duplicates docs site | LOW | Delete duplicated sections from README; replace with links to docs pages; keep README under 150 lines. |
| Over-engineered docs site | MEDIUM | Remove unused plugins and pages; simplify `mkdocs.yml`; may need to restructure navigation and delete dead pages. |
| Wrong plugin chosen (dormant/broken) | MEDIUM | Swap plugin (e.g., `mkdocs-typer` to `mkdocs-click`); update directive syntax in affected Markdown files; rebuild and verify. |
| Docs fossilized after milestone | HIGH | Audit all docs against current CLI state; update every guide page; establish workflow gates. The longer the gap between code and docs, the more painful the catch-up. |
| Build environment missing package install | LOW | Add `uv pip install -e .` to the docs build instructions; verify with `mkdocs build --strict`. |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Documentation drift | Phase 1 (MkDocs setup) | CLI reference is auto-generated from Typer app; `mkdocs build --strict` passes; no hand-written option tables exist |
| Over-engineering | Phase 1 (MkDocs setup) | `mkdocs.yml` uses fewer than 10 plugins; no versioned docs, no blog, no internal API reference |
| README duplication | Phase 2 (README) | README is under 150 lines; contains no CLI reference table; links to docs for details |
| Plugin fragmentation | Phase 1 (MkDocs setup) | Chosen plugin (`mkdocs-click`) has recent commits; `mkdocs build --strict` validates the CLI reference |
| Docs fossilization | Final phase (conventions) | Future milestone template includes "update docs" criterion; `mkdocs build --strict` is in dev workflow |
| Package import failure | Phase 1 (MkDocs setup) | Docs build instructions include editable install; `mkdocs build` works from a clean `uv sync` |
| Docstring format mismatch | Not in v1.1 scope | Flag for future if internal API docs are added; ruff docstring rules configured |

## Sources

- [MkDocs Material documentation](https://squidfunk.github.io/mkdocs-material/) -- official troubleshooting and configuration guidance
- [Documentation Drift](https://gaudion.dev/blog/documentation-drift) -- analysis of why docs go stale and prevention strategies
- [mkdocs-click](https://github.com/mkdocs/mkdocs-click) -- MkDocs-org maintained Click/Typer CLI docs plugin
- [mkdocs-typer2](https://github.com/syn54x/mkdocs-typer2) -- actively maintained Typer-native docs plugin (alternative)
- [mkdocs-typer (original)](https://github.com/bruce-szalwinski/mkdocs-typer) -- dormant since June 2023, do not use
- [Real Python: Build Your Python Project Documentation With MkDocs](https://realpython.com/python-project-documentation-with-mkdocs/) -- practical guide covering common setup pitfalls
- [Google documentation best practices](https://google.github.io/styleguide/docguide/best_practices.html) -- principles on minimal effective documentation
- [mkdocstrings troubleshooting](https://mkdocstrings.github.io/troubleshooting/) -- common import and rendering issues
- Navigator codebase (`src/navigator/cli.py`) -- verified Typer app structure with subcommand groups
- Navigator `pyproject.toml` -- verified dependency structure and entry points

---
*Pitfalls research for: Adding MkDocs documentation to Navigator CLI (v1.1 milestone)*
*Researched: 2026-03-25*
