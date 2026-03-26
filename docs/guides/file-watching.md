# File Watching

Navigator monitors directories for file changes and triggers commands automatically.

## Prerequisites

- A registered, active command (see [Quick Start](../getting-started/quickstart.md))
- A directory to watch

## Watch a Directory

```bash
navigator watch my-task --path /home/user/projects/myapp --pattern "*.py"
```

```text
Watching '/home/user/projects/myapp' for '*.py' changes -> my-task
```

Watching is recursive by default -- subdirectories are included automatically.

!!! warning
    The watcher daemon must be running for file triggers to work. Use `navigator watch --start` for foreground mode or install the systemd service for background operation.

## Common Patterns

### Watch Python Files

```bash
navigator watch my-task --path ./src --pattern "*.py"
```

### Watch with Custom Debounce

```bash
navigator watch my-task --path ./docs --pattern "*.md" --debounce 2000
```

The debounce value is in milliseconds. The default is 500ms. A higher value prevents rapid-fire triggers when multiple files change in quick succession (e.g., a `git checkout`).

### Business Hours Only

```bash
navigator watch my-task --path ./data --active-hours "09:00-17:00"
```

Events outside the active hours window are silently dropped. Overnight ranges like `22:00-06:00` also work -- Navigator handles the day boundary correctly.

## Ignore Patterns

Navigator ignores common temporary files by default:

- `.git/**`
- `*.swp`
- `*.tmp`
- `*~`
- `__pycache__/**`

Add custom ignore patterns with `--ignore` (repeatable):

```bash
navigator watch my-task --path ./src --ignore "*.log" --ignore "build/**"
```

## List and Remove Watchers

List all active watchers:

```bash
navigator watch --list
```

```text
                              Active Watchers
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┓
┃ Command   ┃ Path                         ┃ Pattern ┃ Debounce ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━┩
│ my-task   │ /home/user/projects/myapp    │ *.py    │ 500ms    │
└───────────┴──────────────────────────────┴─────────┴──────────┘
```

Remove a watcher:

```bash
navigator watch my-task --remove
```

```text
Removed watcher for 'my-task'
```

## Start the Watcher

Run the watcher daemon in the foreground:

```bash
navigator watch --start
```

Or use the `daemon` command directly:

```bash
navigator daemon
```

For persistent background operation, install the systemd service (see the [Systemd Service](systemd.md) guide).

## Troubleshooting

- **Command triggers too often:** Increase the debounce value. The default 500ms works for most cases, but bulk file operations may need 2000ms or higher.

- **Changes not detected:** Verify the watched path exists and your glob pattern matches the files you expect. Check that your ignore patterns are not excluding the files.

- **Self-triggering loop:** Navigator includes a SelfTriggerGuard that prevents a command from re-triggering while it is already executing. If your command writes to the watched directory, the guard suppresses the resulting file event.

## What's Next

- [Scheduling](scheduling.md) -- use time-based triggers instead of file events
- [Systemd Service](systemd.md) -- run the watcher daemon persistently in the background
