# Phase 1: Project Scaffold - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-23
**Phase:** 1-project-scaffold
**Areas discussed:** Package structure, CLI command hierarchy, Config file format, Project tooling
**Mode:** Auto (recommended defaults selected)

---

## Package Structure

| Option | Description | Selected |
|--------|-------------|----------|
| src layout (`src/navigator/`) | Modern Python best practice, avoids import ambiguity | ✓ |
| Flat layout (`navigator/`) | Simpler but can cause import issues during development | |

**User's choice:** [auto] src layout (recommended default)
**Notes:** Standard for modern Python packages with pyproject.toml

---

## CLI Command Hierarchy

| Option | Description | Selected |
|--------|-------------|----------|
| Flat subcommands | `navigator register`, `navigator list`, etc. — simple, discoverable | ✓ |
| Nested groups | `navigator command register`, `navigator command list` — grouped by domain | |
| Mixed | Top-level for common, nested for advanced | |

**User's choice:** [auto] Flat subcommands (recommended default)
**Notes:** Simpler for CLI discoverability and Claude Code agent invocation

---

## Config File Format

| Option | Description | Selected |
|--------|-------------|----------|
| TOML (`~/.config/navigator/config.toml`) | stdlib tomllib in 3.12+, consistent with pyproject.toml | ✓ |
| YAML | More flexible but requires PyYAML dependency | |
| JSON | No comments, less human-friendly | |

**User's choice:** [auto] TOML (recommended default)
**Notes:** Aligns with Python ecosystem conventions

---

## Project Tooling

| Option | Description | Selected |
|--------|-------------|----------|
| uv + pytest + ruff + hatchling | Modern, fast, single-tool for each concern | ✓ |
| Poetry + pytest + black/isort | Established but heavier | |
| pip + setuptools | Traditional but less ergonomic | |

**User's choice:** [auto] uv + pytest + ruff + hatchling (recommended default)
**Notes:** Matches STACK.md research recommendations

---

## Claude's Discretion

- SQLite database location default
- Log directory default
- Whether to include `navigator version` subcommand

## Deferred Ideas

None — discussion stayed within phase scope.
