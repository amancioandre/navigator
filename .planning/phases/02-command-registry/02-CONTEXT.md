# Phase 2: Command Registry - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver full CRUD operations for the command registry — users can register, list, show, update, delete, pause, and resume commands through the CLI. All data persists in SQLite with crash-safe atomic writes. After this phase, `navigator register`, `navigator list`, `navigator show`, `navigator update`, `navigator delete`, `navigator pause`, and `navigator resume` are functional commands backed by a persistent registry.

</domain>

<decisions>
## Implementation Decisions

### Command Identity
- **D-01:** Name as the primary user-facing identifier. Commands are referenced by name in all CLI operations (`navigator show my-command`, `navigator delete my-command`).
- **D-02:** Auto-generated UUID as internal primary key. Used for database references and future cross-namespace resolution (Phase 7).
- **D-03:** Names must be unique within a namespace. Name validation: lowercase alphanumeric + hyphens, no spaces.

### Register CLI UX
- **D-04:** `name` is a required positional argument: `navigator register my-command --prompt "..."`.
- **D-05:** `--prompt` is a required option (the Claude Code prompt/instruction to execute).
- **D-06:** Optional flags with sensible defaults: `--environment` (working directory, defaults to cwd), `--secrets` (secrets path, defaults to none), `--allowed-tools` (comma-separated list, defaults to none).
- **D-07:** All paths resolved to absolute at registration time via `resolve_path()` from config module (INFRA-07 carry-forward).

### Output Formatting
- **D-08:** Rich tables for human-readable output on `list` and `show` commands. Consistent with Rich being in the stack.
- **D-09:** JSON output mode (`--output json`) deferred to Phase 10 (INFRA-04). For now, Rich tables only.

### Update Granularity
- **D-10:** Field-level patching — `navigator update my-command --prompt "new prompt"` updates only the prompt field. Unspecified fields remain unchanged.
- **D-11:** All update-able fields are optional flags on the `update` subcommand.

### Pause/Resume Model
- **D-12:** Status field on the command record: `active` or `paused`. Simple enum, no separate table.
- **D-13:** Paused commands are skipped by the executor (Phase 3) and scheduler (Phase 5). The registry just stores the state.

### SQLite Schema
- **D-14:** Single `commands` table with columns for all command fields. SQLite chosen over TinyDB per REG-10 for crash-safe atomic transactions.
- **D-15:** Use Python `sqlite3` stdlib module — no ORM. Direct SQL with parameterized queries. Keeps dependencies minimal and control explicit.
- **D-16:** Pydantic model for the Command record — validates data before DB writes, serializes for display.

### Claude's Discretion
- Exact SQLite column types and constraints (NOT NULL, defaults, indexes)
- Whether to add a `show` subcommand vs overloading `list` with a `--name` filter
- Internal module organization (single `registry.py` vs `models.py` + `db.py`)
- Whether `created_at` / `updated_at` timestamps use ISO 8601 strings or Unix epoch integers
- Test structure and fixtures

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project
- `.planning/PROJECT.md` — Core value, constraints, key decisions
- `.planning/REQUIREMENTS.md` — REG-01 through REG-08, REG-10 (all mapped to this phase)

### Research
- `.planning/research/STACK.md` — Recommended stack with versions (Pydantic, Rich, SQLite over TinyDB rationale)
- `.planning/research/ARCHITECTURE.md` — Component boundaries, module layout
- `.planning/research/PITFALLS.md` — Pitfall #8 (stale paths) applies to path resolution at registration

### Prior Phase
- `.planning/phases/01-project-scaffold/01-CONTEXT.md` — Package structure, CLI hierarchy, config system decisions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/navigator/config.py:resolve_path()` — Absolute path resolution, use for all path fields at registration time
- `src/navigator/config.py:NavigatorConfig` — Has `db_path` field pointing to SQLite location (`~/.local/share/navigator/registry.db`)
- `src/navigator/config.py:get_data_dir()` — XDG data directory for DB and logs

### Established Patterns
- Pydantic `BaseModel` with `Field(default_factory=...)` for deferred defaults (from config.py)
- `tomllib` for reading, `tomli_w` for writing (TOML config pattern)
- Typer with type-annotated arguments and `Annotated` syntax (from cli.py)

### Integration Points
- `src/navigator/cli.py` — Subcommand stubs already exist for `register`, `list`. Need to add `show`, `update`, `delete`, `pause`, `resume` subcommands.
- `src/navigator/config.py:load_config()` — Provides `db_path` for SQLite connection
- `pyproject.toml` — May need new dependency (none expected — sqlite3 is stdlib, Rich is already in stack)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. Follow the stack recommendations from research.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-command-registry*
*Context gathered: 2026-03-23*
