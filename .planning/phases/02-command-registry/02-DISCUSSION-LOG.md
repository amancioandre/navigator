# Phase 2: Command Registry - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-23
**Phase:** 02-command-registry
**Areas discussed:** Command identity, Register CLI UX, Output formatting, Update granularity, Pause/resume model
**Mode:** --auto (all decisions auto-selected)

---

## Command Identity

| Option | Description | Selected |
|--------|-------------|----------|
| Name only | Human-readable names as sole identifier | |
| UUID only | Auto-generated UUIDs, no human names | |
| Name + UUID | Name as user-facing ID, UUID as internal PK | ✓ |

**User's choice:** [auto] Name + UUID (recommended default)
**Notes:** Human-readable names for CLI UX, UUIDs for internal references and future cross-namespace use (Phase 7).

---

## Register CLI UX

| Option | Description | Selected |
|--------|-------------|----------|
| All flags | Every field as --flag options | |
| Positional name + required flags | Name positional, prompt required, rest optional | ✓ |
| Interactive prompts | Wizard-style interactive registration | |

**User's choice:** [auto] Positional name + required flags (recommended default)
**Notes:** Balances discoverability with minimal friction. `navigator register my-command --prompt "..."` with optional flags for environment, secrets, allowed-tools.

---

## Output Formatting

| Option | Description | Selected |
|--------|-------------|----------|
| Plain text | Simple text output | |
| Rich tables | Formatted tables via Rich library | ✓ |
| JSON by default | Machine-readable JSON | |

**User's choice:** [auto] Rich tables (recommended default)
**Notes:** Consistent with Rich being in the project stack. JSON output deferred to Phase 10 (INFRA-04).

---

## Update Granularity

| Option | Description | Selected |
|--------|-------------|----------|
| Full replacement | All fields required on every update | |
| Field-level patching | Only passed flags are updated | ✓ |

**User's choice:** [auto] Field-level patching (recommended default)
**Notes:** Standard CLI pattern. Avoids requiring all fields on every update. Each updatable field is an optional flag.

---

## Pause/Resume Model

| Option | Description | Selected |
|--------|-------------|----------|
| Status field | Enum column on command record (active/paused) | ✓ |
| Separate table | Dedicated pause state table | |
| Delete + re-register | No pause concept, just delete and recreate | |

**User's choice:** [auto] Status field (recommended default)
**Notes:** Simple single-table approach. Paused commands skipped by executor (Phase 3) and scheduler (Phase 5).

---

## Claude's Discretion

- SQLite column types and constraints
- Whether to add `show` subcommand vs filter on `list`
- Internal module organization
- Timestamp format
- Test structure and fixtures

## Deferred Ideas

None — discussion stayed within phase scope.
