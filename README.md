# Navigator

A private Python CLI that schedules, triggers, and chains Claude Code sessions with proper context, secrets, and permissions. Navigator manages the system crontab and file watchers to run registered commands autonomously -- never exposed to the public internet.

## Installation

**Prerequisites:** Python 3.12+

### With uv (recommended)

```bash
git clone <repo-url> navigator
cd navigator
uv tool install .
```

### With pip

```bash
pip install .
```

### Verify

```bash
navigator doctor
```

All checks passing means Navigator is installed and ready.

## Quick Start

Register a command:

```bash
navigator register hello-world --prompt "echo hello from navigator" --environment /tmp
```

List registered commands:

```bash
navigator list
```

Preview what would execute:

```bash
navigator exec hello-world --dry-run
```

Clean up:

```bash
navigator delete hello-world --force
```

## Features

- [Cron Scheduling](docs/guides/scheduling.md) -- schedule commands via system crontab
- [File Watching](docs/guides/file-watching.md) -- trigger commands on filesystem changes with debounce
- [Command Chaining](docs/guides/chaining.md) -- run commands in sequence with correlation tracking and cycle protection
- [Secrets Management](docs/guides/secrets.md) -- inject environment variables from `.env` files
- [Namespaces](docs/guides/namespaces.md) -- organize commands into groups with isolated secrets
- [Systemd Service](docs/guides/systemd.md) -- persistent daemon that starts automatically and survives reboots
- [Configuration](docs/guides/configuration.md) -- TOML-based settings with sensible defaults

## Documentation

For detailed guides and reference material, browse the docs site locally:

```bash
uv run mkdocs serve
```

Or read the source files directly:

- [Installation](docs/getting-started/installation.md)
- [Quick Start](docs/getting-started/quickstart.md)
- [CLI Reference](docs/reference/cli.md)
