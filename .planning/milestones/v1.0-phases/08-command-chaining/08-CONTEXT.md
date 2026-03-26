# Phase 8: Command Chaining - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver command chaining — completing one command automatically triggers the next with shared state via the environment path. Chains run as separate Claude Code sessions, support cross-namespace linking, have configurable failure semantics, depth limits with cycle detection, and correlation IDs for log tracing. After this phase, `navigator chain` manages chain links, and `navigator exec` follows chains automatically.

</domain>

<decisions>
## Implementation Decisions

### Chain Registration & Storage
- **D-01:** `chain_next` column on the commands table — each command optionally points to its successor (nullable TEXT field storing the next command's qualified name).
- **D-02:** Registration: `navigator chain <command> --next <command>` — explicit linking. Both commands must exist.
- **D-03:** Cross-namespace chains: fully qualified names work — `navigator chain scrape --next content:generate`.
- **D-04:** View chain: `navigator chain <command> --show` — displays the chain as an arrow diagram (A → B → C).

### Safety & Failure Semantics
- **D-05:** Default: stop-on-failure — chain halts if any command returns non-zero exit code.
- **D-06:** Continue option: `--on-failure continue` flag when registering a chain link — stored per-link.
- **D-07:** Depth limit: default 10, stored in NavigatorConfig as `max_chain_depth`. Checked at execution time.
- **D-08:** Cycle detection at registration time — traverse the chain graph when adding a link, reject if adding it would create a cycle.

### Execution Model
- **D-09:** Sequential execution — each command fully completes (Popen.communicate() returns) before the next starts. No race conditions possible since execution is blocking and sequential.
- **D-10:** Shared state via environment path (filesystem) — each chained command inherits the same working directory, reads/writes shared files. No in-memory state sharing.
- **D-11:** Each chained command runs as a separate Claude Code session (separate subprocess invocation).

### Correlation & Logging
- **D-12:** Correlation ID: UUID4 generated per chain run.
- **D-13:** Passed as `NAVIGATOR_CHAIN_ID` environment variable to each subprocess in the chain.
- **D-14:** Chain execution logged via execution logger — chain start, each step, chain end — all with correlation ID. Visible via `navigator logs`.

### Claude's Discretion
- Whether to add `chain_next` and `on_failure_continue` to Command model or use a separate chain_links table
- Whether chain execution logic lives in executor.py or a new chainer.py module
- How to handle `navigator chain <cmd> --remove` (unlink from chain)
- Test approach for chain execution (mock subprocess vs integration)
- Config key name for max_chain_depth

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project
- `.planning/PROJECT.md` — Core value, constraints
- `.planning/REQUIREMENTS.md` — CHAIN-01 through CHAIN-06

### Prior Phases
- `.planning/phases/07-namespacing/07-CONTEXT.md` — Namespace format, qualified names
- `src/navigator/namespace.py` — parse_qualified_name() for cross-namespace references
- `src/navigator/executor.py` — execute_command() that chains will invoke
- `src/navigator/execution_logger.py` — Logging infrastructure for chain correlation
- `src/navigator/db.py` — Commands table, get_command_by_name()

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/navigator/executor.py` — execute_command(cmd, config) for running each chain step
- `src/navigator/namespace.py` — parse_qualified_name() for resolving cross-namespace names
- `src/navigator/execution_logger.py` — write_execution_log() for per-step logging
- `src/navigator/db.py` — Command CRUD, get_command_by_name()
- `src/navigator/models.py` — Command model (needs chain_next field)

### Established Patterns
- SQLite column additions via ALTER TABLE or schema migration
- Pydantic models for validation
- Lazy imports in CLI
- Rich Console for output

### Integration Points
- `src/navigator/models.py` — Add chain_next, on_failure_continue fields
- `src/navigator/db.py` — Update schema, add chain-related queries
- `src/navigator/executor.py` — Add chain execution logic or new module
- `src/navigator/cli.py` — chain() stub exists, needs implementation
- `src/navigator/config.py` — Add max_chain_depth

</code_context>

<specifics>
## Specific Ideas

- Race condition avoidance: sequential blocking execution is the key design choice. Each subprocess fully completes before the next starts.
- Environment path sharing: commands in a chain share the filesystem working directory, not process memory.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 08-command-chaining*
*Context gathered: 2026-03-24*
