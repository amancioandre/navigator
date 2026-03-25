# Milestones

## v1.0 Navigator v1.0 (Shipped: 2026-03-25)

**Phases completed:** 10 phases, 20 plans, 40 tasks

**Key accomplishments:**

- Navigator Python package with Typer CLI, 8 subcommand stubs, and pytest test infrastructure using src layout and hatchling build
- TOML-based config with Pydantic validation, XDG-compliant paths via platformdirs, and resolve_path() for absolute path normalization
- Pydantic Command model with name validation regex and SQLite CRUD layer using WAL mode with atomic transactions
- 7 registry CLI subcommands (register/list/show/update/delete/pause/resume) with Rich output, TDD tests, and full error handling
- Secret loading from .env files via python-dotenv and subprocess executor with environment whitelist isolation and Claude CLI argument assembly
- Wired `navigator exec <name>` CLI subcommand to executor module with paused-command rejection, error handling, and 6 integration tests
- Popen-based executor with process group isolation, exponential backoff retry, SIGTERM/SIGKILL timeout, and per-execution log files
- Exec command wired with --timeout/--retries override flags; logs command shows Rich table of execution history with --tail for full output
- CrontabManager class wrapping python-crontab with fcntl file locking, tagged entry management, and post-write verification
- Full schedule CLI wiring: --cron creates crontab entries, --remove deletes them, --list shows Rich table, with validation for missing/paused/invalid inputs
- Watchdog-based file watcher with Pydantic model, SQLite CRUD, debounced event handler, self-trigger guard, and time-window filtering
- Watch CLI command wired with register/remove/list/start modes and foreground daemon via watchdog Observer
- Namespace model with shared name validation, SQLite CRUD with auto-created default, qualified name parser, and per-namespace secrets path resolution
- Namespace CLI subcommands (create/list/delete), --namespace on register, and qualified name resolution (myns:cmd) in exec/show
- Sequential command chain execution with cycle detection, depth limits, and UUID4 correlation IDs passed as NAVIGATOR_CHAIN_ID
- Chain CLI with --next/--show/--remove/--on-failure flags and automatic chain execution on `navigator exec` with correlation ID output
- Systemd user service module with dynamic unit file generation, install/uninstall lifecycle, and systemctl --user wrapper for daemon management
- Typer CLI commands for daemon, install-service, uninstall-service, and service wrapping the systemd service module
- --output json global flag on all list/show commands with consistent {status, data, message} wrapper, plus --dry-run on exec for safe command previews without execution
- Self-diagnosable Navigator with 5 health checks (DB, binary, paths, crontab, service), --fix auto-remediation, and JSON output

---
