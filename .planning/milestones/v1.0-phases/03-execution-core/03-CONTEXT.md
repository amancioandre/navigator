# Phase 3: Execution Core - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the execution engine — `navigator exec <command>` launches a registered command as a Claude Code subprocess with secret injection, allowed tools configuration, and a clean environment. After this phase, users can execute any registered command and have it run in the correct working directory with the correct secrets and permissions.

</domain>

<decisions>
## Implementation Decisions

### Claude Code Invocation
- **D-01:** Invoke Claude Code via `claude` CLI using `subprocess.run` — standard, reliable, works in all environments.
- **D-02:** Pass the prompt using the `--print` flag with `-p` for the prompt text: `claude -p "..." --print`.
- **D-03:** Pass allowed tools via `--allowedTools` flag, one per tool: `--allowedTools "tool1" --allowedTools "tool2"`.
- **D-04:** Do NOT use `--dangerously-skip-permissions` — explicit `--allowedTools` per command is safer and more granular.

### Secret Loading
- **D-05:** Secret files use `.env` format (KEY=VALUE per line). Simple, widely understood.
- **D-06:** Parse secrets using `python-dotenv` library — handles quoting, comments, multiline values.
- **D-07:** If the secrets file does not exist or path is None, skip injection and log a warning. Command may work without secrets.
- **D-08:** No validation of secret values — values are opaque strings. Only validate the file exists and is readable.

### Environment Isolation
- **D-09:** Whitelist approach — start with an empty environment, then add only: PATH, HOME, LANG, TERM, SHELL from the parent process, plus injected secrets.
- **D-10:** PATH must pass through — Claude Code needs it to find executables. HOME needed for config files.
- **D-11:** Include LANG, TERM, SHELL — needed for proper terminal behavior in the subprocess.
- **D-12:** No custom environment variables in this phase. Future enhancement if needed.

### Paused Command Behavior
- **D-13:** Attempting to exec a paused command returns an error: "Command 'X' is paused. Run `navigator resume X` first." — clear, actionable.
- **D-14:** Exit code 1 (failure) when attempting to exec a paused command — consistent with CLI conventions.

### Claude's Discretion
- Internal module organization (single `executor.py` vs multiple files)
- Whether to create a helper function for building the subprocess command list
- How to structure the secret-loading utility (inline vs separate module)
- Test approach for subprocess execution (mock subprocess.run vs integration tests)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project
- `.planning/PROJECT.md` — Core value, constraints, key decisions
- `.planning/REQUIREMENTS.md` — EXEC-01, EXEC-02, EXEC-03, EXEC-07, EXEC-08 (mapped to this phase)

### Research
- `.planning/research/STACK.md` — python-dotenv recommendation, subprocess patterns
- `.planning/research/ARCHITECTURE.md` — Component boundaries
- `.planning/research/PITFALLS.md` — Secret leakage pitfalls

### Prior Phases
- `.planning/phases/01-project-scaffold/01-CONTEXT.md` — Package structure, CLI framework
- `.planning/phases/02-command-registry/02-CONTEXT.md` — Command model, DB layer, pause/resume model

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/navigator/models.py` — Command model with `prompt`, `environment`, `secrets`, `allowed_tools` fields
- `src/navigator/db.py` — `get_command_by_name()` to look up commands for execution
- `src/navigator/config.py` — `load_config()`, `resolve_path()` for path resolution

### Established Patterns
- Pydantic BaseModel with field validators (from models.py)
- SQLite connection via `get_connection()` with WAL mode (from db.py)
- Typer subcommands with `Annotated` syntax (from cli.py)
- Rich Console/Table for output (from cli.py)

### Integration Points
- `src/navigator/cli.py:exec_command()` — stub exists, needs implementation
- `src/navigator/db.py:get_command_by_name()` — retrieves command for execution
- `src/navigator/models.py:CommandStatus` — check for PAUSED status before execution

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

*Phase: 03-execution-core*
*Context gathered: 2026-03-24*
