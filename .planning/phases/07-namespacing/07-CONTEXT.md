# Phase 7: Namespacing - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver multi-project namespacing — commands are organized into namespaces with isolated secrets, explicit namespace CRUD, and cross-namespace command references. After this phase, `navigator namespace create/list/delete` manages namespaces, commands use `namespace:command` format, and secrets live under `~/.secrets/<namespace>/`.

</domain>

<decisions>
## Implementation Decisions

### Namespace Format & Storage
- **D-01:** Namespace format: `namespace:command` colon-separated. All CLI operations support qualified names.
- **D-02:** New `namespaces` table in SQLite — stores name, created_at, optional description.
- **D-03:** Default namespace: `default` — already exists in Command model. Auto-created if namespaces table is empty.
- **D-04:** Namespace name validation: same rules as command names — lowercase alphanumeric + hyphens.

### Secret Isolation
- **D-05:** Secret directory structure: `~/.secrets/<namespace>/` per namespace.
- **D-06:** Default namespace secrets: `~/.secrets/default/`.
- **D-07:** No migration needed — existing commands have absolute secrets paths that continue to work.

### CLI UX
- **D-08:** Create: `navigator namespace create <name>` — explicit subcommand group.
- **D-09:** List: `navigator namespace list` — Rich table with namespace name, command count, created date.
- **D-10:** Delete: `navigator namespace delete <name> --force` — rejects if commands exist without --force flag.
- **D-11:** Cross-namespace reference: `navigator exec gamescout:scrape` — fully qualified names work everywhere.

### Claude's Discretion
- Whether to add a Typer subcommand group or flat commands with `namespace` prefix
- Whether to add `--namespace` filter to existing `navigator list` command
- How to handle `navigator register` with namespace — `--namespace` flag or parse from name
- Migration strategy for `namespaces` table (auto-insert "default" on init_db)
- Test approach for namespace isolation

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project
- `.planning/PROJECT.md` — Core value, constraints
- `.planning/REQUIREMENTS.md` — NS-01 through NS-04

### Prior Phases
- `.planning/phases/02-command-registry/02-CONTEXT.md` — Command model with namespace field
- `src/navigator/models.py` — Command model, namespace field defaults to "default"
- `src/navigator/db.py` — Commands table with namespace column and index
- `src/navigator/cli.py` — Current CLI structure

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/navigator/models.py` — Command.namespace field already exists (defaults to "default")
- `src/navigator/db.py` — idx_commands_namespace index already created, get_all_commands has namespace filter
- `src/navigator/config.py` — NavigatorConfig with secrets_base_path

### Established Patterns
- SQLite tables with init_db pattern
- Typer CLI with Annotated type hints
- Rich Console/Table for output
- Pydantic models for validation

### Integration Points
- `src/navigator/db.py` — Add namespaces table, namespace CRUD functions
- `src/navigator/cli.py` — Add namespace subcommand group, update register/list/exec for qualified names
- `src/navigator/models.py` — May need Namespace model

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-namespacing*
*Context gathered: 2026-03-24*
