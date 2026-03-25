# Phase 14: Feature Guides - Research

**Researched:** 2026-03-25
**Domain:** Documentation -- task-oriented feature guides for Navigator capabilities
**Confidence:** HIGH

## Summary

Phase 14 creates seven feature guide documents and a configuration reference for Navigator. All features are fully implemented and tested (v1.0 complete). The domain is documentation authoring in MkDocs Material Markdown, following patterns established in Phases 11-13. Every guide documents a real, functional CLI command with actual flags, defaults, and behaviors verified directly from source code.

The primary challenge is content accuracy and consistency across seven guides. Each guide must use real CLI commands with correct flag names, show realistic output, and cross-link to related guides. The codebase review captured all CLI flags, model defaults, config options, and execution behaviors needed to write accurate guides.

Research examined every relevant source file: `cli.py` (all command signatures and flags), `models.py` (defaults and validation rules), `config.py` (all config.toml options), `scheduler.py` (crontab behavior), `watcher.py` + `watcher_handler.py` (debounce, ignore patterns, time windows, self-trigger guard), `chainer.py` (chain walking, cycle detection, correlation IDs, failure semantics), `secrets.py` (.env loading, permission warnings), `namespace.py` (qualified names, secrets path resolution), `service.py` (systemd unit generation, install/uninstall, linger), and `executor.py` (environment isolation, whitelist, retry, timeout).

**Primary recommendation:** Write all seven guides using verified CLI flags and defaults from source code. Follow the Phase 13 established tone (direct, concise). Target 100-150 lines per guide. Validate with `uv run mkdocs build --strict`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Consistent structure across all 7 guides: Overview -> Prerequisites -> Usage -> Examples -> Troubleshooting
- Flat file organization: `docs/guides/{feature}.md` -- 7 files in one directory
- Real CLI commands with expected output shown inline (consistent with getting started from Phase 13)
- Cross-link related guides (e.g., scheduling -> systemd for persistence, secrets -> namespaces for isolation)
- Task-oriented: show how to DO things, not explain internals
- Config reference uses table format per section: option, type, default, description
- Include 2-3 real-world "common patterns" per guide (e.g., cron: "daily at 9am", "weekdays only")
- Direct and concise tone -- same as getting started (established in Phase 13)
- Use MkDocs admonitions for important caveats (e.g., "secrets are plaintext .env files")
- Target ~100-150 lines per guide -- enough to be useful, short enough to scan

### Claude's Discretion
- Exact content and examples within each guide
- Ordering of guides in nav
- Which features to cross-reference within each guide

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GUIDE-01 | Scheduling guide -- cron-based scheduling with examples | Verified `navigator schedule` flags (--cron, --remove, --list), CrontabManager behavior, cron expression validation |
| GUIDE-02 | File watching guide -- watchdog triggers with debounce, ignore patterns, time windows | Verified `navigator watch` flags (--path, --pattern, --debounce, --ignore, --active-hours, --list, --remove, --start), default ignore patterns, debounce default (500ms), active_hours format (HH:MM-HH:MM) |
| GUIDE-03 | Command chaining guide -- sequential triggers, correlation IDs, cycle detection | Verified `navigator chain` flags (--next, --show, --remove, --on-failure), NAVIGATOR_CHAIN_ID env var, max_chain_depth config, cycle detection behavior |
| GUIDE-04 | Secrets management guide -- .env loading, environment isolation, security model | Verified `load_secrets()` behavior, ENV_WHITELIST (PATH, HOME, LANG, TERM, SHELL), permission warning for group/other readable files, `--secrets` flag on register/update |
| GUIDE-05 | Namespaces guide -- multi-project organization, cross-namespace references | Verified `navigator namespace` subcommands (create, list, delete), qualified name format (namespace:command), auto-secrets path (~/.secrets/<namespace>/), --namespace flag on register/list |
| GUIDE-06 | Systemd service guide -- daemon persistence, install/uninstall, reboot survival | Verified `navigator install-service` (--no-linger), `navigator uninstall-service`, `navigator service` (start/stop/restart/status), unit file generation, linger behavior |
| GUIDE-07 | Configuration reference -- config.toml options, paths, defaults | Verified all NavigatorConfig fields: db_path, log_dir, secrets_base_path, default_retry_count (3), default_timeout (300), max_chain_depth (10), XDG paths via platformdirs |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python >=3.12 runtime requirement
- uv is the preferred toolchain
- MkDocs with Material theme for documentation
- `uv run mkdocs build --strict` for build validation
- Admonition, highlight, superfences, mkdocs-click extensions configured
- content.code.copy theme feature enabled

## Architecture Patterns

### Current Docs Structure
```
docs/
  index.md
  getting-started/
    installation.md
    quickstart.md
  reference/
    cli.md
```

### Target Structure After Phase 14
```
docs/
  index.md
  getting-started/
    installation.md
    quickstart.md
  guides/
    scheduling.md        # GUIDE-01
    file-watching.md     # GUIDE-02
    chaining.md          # GUIDE-03
    secrets.md           # GUIDE-04
    namespaces.md        # GUIDE-05
    systemd.md           # GUIDE-06
    configuration.md     # GUIDE-07
  reference/
    cli.md
```

### mkdocs.yml Nav Update
```yaml
nav:
  - Home: index.md
  - Getting Started:
    - Installation: getting-started/installation.md
    - Quick Start: getting-started/quickstart.md
  - Guides:
    - Scheduling: guides/scheduling.md
    - File Watching: guides/file-watching.md
    - Command Chaining: guides/chaining.md
    - Secrets: guides/secrets.md
    - Namespaces: guides/namespaces.md
    - Systemd Service: guides/systemd.md
    - Configuration: guides/configuration.md
  - Reference:
    - CLI: reference/cli.md
```

### Established Writing Patterns (from Phase 13)
- Shell commands in fenced code blocks with `bash` language
- Expected output in fenced code blocks with `text` language
- MkDocs admonitions: `!!! tip` for helpful hints, `!!! warning` for caveats
- Relative cross-links: `[CLI Reference](../reference/cli.md)`
- "What's Next" section at end of each guide linking to related guides

### Guide Template Structure
```markdown
# {Feature Name}

{1-2 sentence overview of what this feature does.}

## Prerequisites

- {What must be done before using this feature}

## {Primary Action}

{How to do the main thing, with CLI command and output.}

## Common Patterns

### {Pattern 1}
{Real-world example with command and output.}

### {Pattern 2}
{Real-world example with command and output.}

## {Secondary Actions}

{List, remove, inspect operations.}

## Troubleshooting

- **{Problem}:** {Solution}

## What's Next

- [{Related Guide}]({link}) -- {why it's relevant}
```

## Verified CLI Reference Data

### Scheduling (`navigator schedule`)

| Flag | Type | Description |
|------|------|-------------|
| `COMMAND` | argument (optional) | Command name to schedule |
| `--cron` | string | Cron expression (e.g., "*/5 * * * *") |
| `--remove` | flag | Remove schedule for command |
| `--list` | flag | List all scheduled commands |

**Behaviors:**
- Validates command exists and is active before scheduling
- Cron expression validated by python-crontab (`job.setall()` + `job.is_valid()`)
- Entries tagged with `navigator:{command_name}` comment in crontab
- Post-write verification: re-reads crontab to confirm entry exists
- Idempotent: re-scheduling updates existing entry
- Crontab entry runs: `{navigator_path} exec {command_name}`

**Common cron expressions:**
- `0 9 * * *` -- daily at 9:00 AM
- `0 * * * *` -- every hour
- `0 9 * * 1-5` -- weekdays at 9:00 AM
- `*/15 * * * *` -- every 15 minutes
- `0 0 * * 0` -- weekly on Sunday at midnight

### File Watching (`navigator watch`)

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `COMMAND` | argument (optional) | - | Command name |
| `--path` | string | - | Directory to watch |
| `--pattern` | string | `*` (all files) | Glob pattern (e.g., `*.md`) |
| `--debounce` | int | 500 | Debounce in milliseconds |
| `--ignore` | string (repeatable) | See defaults | Ignore pattern |
| `--active-hours` | string | None (always) | HH:MM-HH:MM time window |
| `--remove` | flag | - | Remove watchers for command |
| `--list` | flag | - | List all watchers |
| `--start` | flag | - | Start watcher daemon |

**Default ignore patterns** (from models.py):
- `.git/**`
- `*.swp`
- `*.tmp`
- `*~`
- `__pycache__/**`

**Behaviors:**
- Recursive watching by default (`recursive=True`)
- DebouncedHandler: collects rapid events, fires once after quiet period
- SelfTriggerGuard: prevents re-triggering while command executes
- Active hours support overnight ranges (e.g., `22:00-06:00`)
- Directory modified events filtered out (noisy on Linux inotify)
- Daemon mode: `navigator daemon` or `navigator watch --start`

### Command Chaining (`navigator chain`)

| Flag | Type | Description |
|------|------|-------------|
| `COMMAND` | argument | Command name (supports namespace:command) |
| `--next` | string | Next command to chain (supports namespace:command) |
| `--show` | flag | Show chain starting from this command |
| `--remove` | flag | Remove chain link from this command |
| `--on-failure` | string | `stop` (default) or `continue` |

**Behaviors:**
- Chain stored as `chain_next` field on Command model
- Cycle detection before linking: checks self-links and transitive cycles
- Correlation ID: UUID4 passed as `NAVIGATOR_CHAIN_ID` env var to every step
- Max chain depth: configurable via `max_chain_depth` (default: 10)
- Failure semantics: stops on first failure unless `on_failure_continue=True`
- `--show` displays chain as: `cmd1 -> cmd2 -> cmd3`
- Cross-namespace chaining supported via qualified names (`project:command`)

### Secrets (`--secrets` on register/update)

**Loading behavior** (from secrets.py):
- Reads `.env` files via `python-dotenv`
- Returns empty dict if path is None or file missing (with warning)
- Warns if file permissions allow group/other read access
- Only key names logged, never values

**Environment isolation** (from executor.py):
- ENV_WHITELIST: `PATH`, `HOME`, `LANG`, `TERM`, `SHELL`
- Only whitelisted vars copied from parent process
- Secrets merged after whitelist
- Extra env (chain correlation ID) merged last

**Namespace auto-resolution:**
- Non-default namespace commands auto-resolve secrets to `~/.secrets/{namespace}/`
- Explicit `--secrets` flag overrides auto-resolution

### Namespaces (`navigator namespace`)

| Subcommand | Arguments/Flags | Description |
|------------|----------------|-------------|
| `create` | `NAME`, `--description/-d` | Create a new namespace |
| `list` | (none) | List all namespaces with command counts |
| `delete` | `NAME`, `--force/-f` | Delete a namespace |

**Behaviors:**
- Name validation: `^[a-z0-9][a-z0-9-]*$` (same as command names)
- `default` namespace cannot be deleted
- Commands reference namespaces via `--namespace/-n` flag on register/list
- Cross-namespace references use `namespace:command` syntax
- `--force` required to delete namespace with existing commands
- Secrets auto-resolve per namespace: `~/.secrets/{namespace}/`

### Systemd Service

| Command | Flags | Description |
|---------|-------|-------------|
| `navigator install-service` | `--no-linger` | Install systemd user service |
| `navigator uninstall-service` | (none) | Remove systemd user service |
| `navigator service` | `ACTION` (start/stop/restart/status) | Control service |
| `navigator daemon` | (none) | Run watcher daemon in foreground |

**Unit file generated:**
```ini
[Unit]
Description=Navigator Watcher Daemon
After=network.target

[Service]
Type=simple
ExecStart={navigator_path} daemon
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
```

**Behaviors:**
- Installs to `~/.config/systemd/user/navigator.service`
- Runs `systemctl --user daemon-reload` + `enable`
- `loginctl enable-linger` by default (skip with `--no-linger`)
- Uninstall: stops, disables, removes file, reloads daemon

### Configuration (`config.toml`)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `db_path` | path | `{XDG_DATA}/navigator/registry.db` | SQLite database location |
| `log_dir` | path | `{XDG_DATA}/navigator/logs` | Execution log directory |
| `secrets_base_path` | path | `~/.secrets/navigator` | Base path for secrets files |
| `default_retry_count` | int | `3` | Default retry attempts on failure |
| `default_timeout` | int | `300` | Default timeout in seconds |
| `max_chain_depth` | int | `10` | Maximum chain link depth |

**Path resolution:**
- Config file: `~/.config/navigator/config.toml` (via platformdirs)
- Data dir: `~/.local/share/navigator/` (via platformdirs)
- All paths resolved to absolute on load
- First run creates config with defaults automatically

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI output examples | Fabricated output | Actual command output format from cli.py | Inaccurate examples mislead users; source-verified output ensures guides match reality |
| Cron expression explanations | Custom cron syntax docs | Well-known 5-field format with Navigator-specific examples | Cron syntax is universal; document Navigator's usage, not cron itself |

## Common Pitfalls

### Pitfall 1: Fabricated CLI Output
**What goes wrong:** Guide shows output that does not match actual CLI behavior.
**Why it happens:** Writing docs without running or verifying commands.
**How to avoid:** Use exact flag names from cli.py, match table column names from Rich output, use real default values from models.py.
**Warning signs:** Flag names in docs that do not appear in `--help`, output format that does not match Rich table structure.

### Pitfall 2: Missing Cross-Links
**What goes wrong:** Guides exist in isolation; users cannot discover related features.
**Why it happens:** Each guide written independently without considering the user journey.
**How to avoid:** Every guide must have a "What's Next" section. Key cross-links: scheduling<->systemd, secrets<->namespaces, chaining<->namespaces, watching<->systemd.
**Warning signs:** A guide that mentions a feature without linking to its guide.

### Pitfall 3: Broken mkdocs.yml Nav References
**What goes wrong:** `mkdocs build --strict` fails because nav references a file that does not exist (or exists but is not in nav).
**Why it happens:** File created but nav not updated, or typo in path.
**How to avoid:** Update mkdocs.yml nav as part of the same task that creates guide files. Build-validate after every file addition.
**Warning signs:** `mkdocs build --strict` emitting warnings about unreferenced files.

### Pitfall 4: Stale "Coming Soon" References
**What goes wrong:** Phase 13 quickstart.md has "Feature Guides -- scheduling, file watching, chaining, and more (coming soon)" text that should be updated with real links.
**Why it happens:** Placeholder text from Phase 13 not updated when guides actually exist.
**How to avoid:** Include a task to update quickstart.md "What's Next" section and index.md with real guide links.
**Warning signs:** Docs site still says "coming soon" after guides are published.

### Pitfall 5: Incorrect Default Values in Config Reference
**What goes wrong:** Config reference shows wrong defaults.
**Why it happens:** Defaults typed from memory instead of verified from source.
**How to avoid:** All defaults verified from `config.py` NavigatorConfig model and `models.py` Watcher/Command models during this research.
**Warning signs:** Default in docs differs from what `navigator doctor` or actual behavior shows.

## Integration Points

### Files to Update (Not Just Create)

1. **mkdocs.yml** -- add Guides section to nav
2. **docs/getting-started/quickstart.md** -- update "What's Next" to link to actual guide pages instead of "coming soon" text
3. **docs/index.md** -- add Guides link to Quick Links section

### Files to Create

1. `docs/guides/scheduling.md`
2. `docs/guides/file-watching.md`
3. `docs/guides/chaining.md`
4. `docs/guides/secrets.md`
5. `docs/guides/namespaces.md`
6. `docs/guides/systemd.md`
7. `docs/guides/configuration.md`

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | mkdocs build --strict |
| Config file | mkdocs.yml |
| Quick run command | `uv run mkdocs build --strict` |
| Full suite command | `uv run mkdocs build --strict` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GUIDE-01 | Scheduling guide renders without errors | build | `uv run mkdocs build --strict` | N/A (build validates all) |
| GUIDE-02 | File watching guide renders without errors | build | `uv run mkdocs build --strict` | N/A |
| GUIDE-03 | Chaining guide renders without errors | build | `uv run mkdocs build --strict` | N/A |
| GUIDE-04 | Secrets guide renders without errors | build | `uv run mkdocs build --strict` | N/A |
| GUIDE-05 | Namespaces guide renders without errors | build | `uv run mkdocs build --strict` | N/A |
| GUIDE-06 | Systemd guide renders without errors | build | `uv run mkdocs build --strict` | N/A |
| GUIDE-07 | Configuration reference renders without errors | build | `uv run mkdocs build --strict` | N/A |

### Sampling Rate
- **Per task commit:** `uv run mkdocs build --strict`
- **Per wave merge:** `uv run mkdocs build --strict`
- **Phase gate:** Full strict build green before `/gsd:verify-work`

### Wave 0 Gaps
None -- existing MkDocs infrastructure covers all phase requirements. No additional test setup needed.

## Sources

### Primary (HIGH confidence)
- `src/navigator/cli.py` -- all CLI command signatures, flags, and argument types
- `src/navigator/models.py` -- Command and Watcher model defaults, validation rules
- `src/navigator/config.py` -- NavigatorConfig fields, defaults, path resolution
- `src/navigator/scheduler.py` -- CrontabManager behavior, locking, verification
- `src/navigator/watcher.py` + `watcher_handler.py` -- daemon, debounce, guard, time windows
- `src/navigator/chainer.py` -- chain walking, cycle detection, correlation IDs
- `src/navigator/secrets.py` -- .env loading, permission checks
- `src/navigator/namespace.py` -- qualified name parsing, secrets path
- `src/navigator/service.py` -- systemd unit generation, install/uninstall
- `src/navigator/executor.py` -- environment whitelist, retry, timeout
- `docs/getting-started/quickstart.md` -- established writing pattern and tone
- `docs/getting-started/installation.md` -- established writing pattern
- `mkdocs.yml` -- current nav structure and extensions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries; pure documentation using existing MkDocs Material
- Architecture: HIGH -- docs structure follows established patterns from Phase 13
- Pitfalls: HIGH -- all verified from actual source code and existing docs
- Content accuracy: HIGH -- every flag, default, and behavior verified from source

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable -- documentation of already-shipped features)
