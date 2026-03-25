# Configuration

Navigator stores settings in a TOML configuration file with sensible defaults for all options.

## Config File Location

The configuration file lives at `~/.config/navigator/config.toml`, resolved via [platformdirs](https://pypi.org/project/platformdirs/) for XDG compliance. If you have `XDG_CONFIG_HOME` set, Navigator follows it; otherwise it defaults to `~/.config/`.

Navigator creates this file with defaults on first run -- you do not need to create it manually.

To find your config file location:

```bash
echo "${XDG_CONFIG_HOME:-$HOME/.config}/navigator/config.toml"
```

!!! tip
    Navigator creates the config file with defaults on first run. You only need to edit it if you want to change a default value.

## Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `db_path` | path | `~/.local/share/navigator/registry.db` | SQLite database for the command registry |
| `log_dir` | path | `~/.local/share/navigator/logs` | Directory for execution log files |
| `secrets_base_path` | path | `~/.secrets/navigator` | Base directory for namespace secrets resolution |
| `default_retry_count` | integer | `3` | Number of retry attempts when a command fails |
| `default_timeout` | integer | `300` | Maximum execution time in seconds before a command is killed |
| `max_chain_depth` | integer | `10` | Maximum number of links in a command chain |

## Example Config File

A complete `config.toml` with all options at their default values:

```toml
db_path = "~/.local/share/navigator/registry.db"
log_dir = "~/.local/share/navigator/logs"
secrets_base_path = "~/.secrets/navigator"
default_retry_count = 3
default_timeout = 300
max_chain_depth = 10
```

## Path Resolution

Navigator resolves all paths to absolute paths when loading the configuration:

- **Home directory expansion** -- `~` is expanded to the current user's home directory.
- **Data directory** -- follows `XDG_DATA_HOME`, which defaults to `~/.local/share/` when not set.
- **Config directory** -- follows `XDG_CONFIG_HOME`, which defaults to `~/.config/` when not set.
- **Relative paths** -- any relative path is resolved against the current working directory at load time.

## Common Patterns

### Increase timeout for long-running commands

Set `default_timeout` to a higher value for commands that need more time:

```toml
default_timeout = 600  # 10 minutes
```

Individual commands can override this default with the `--timeout` flag on `navigator register`.

### Custom secrets location

Change where namespace auto-resolution looks for secrets files:

```toml
secrets_base_path = "/path/to/secrets"
```

Navigator resolves secrets for each namespace under this base path (e.g., `/path/to/secrets/my-namespace/.env`).

## Troubleshooting

### Config not loading

Verify the file exists at the expected location:

```bash
ls -la ~/.config/navigator/config.toml
```

If the file exists but Navigator ignores it, check that the TOML syntax is valid. A missing quote or bracket causes a silent parse failure.

### Paths not resolving

Ensure paths use forward slashes. Navigator supports `~` for the home directory but does not expand shell variables like `$HOME` in config values.

### Changes not taking effect

Navigator reads the config file on each CLI invocation -- there is no daemon to restart. If changes are not reflected, confirm you are editing the correct file (check `XDG_CONFIG_HOME` if set).

## What's Next

- [Secrets](secrets.md) -- details on secret injection and namespace resolution
- [CLI Reference](../reference/cli.md) -- per-command overrides of configuration defaults
