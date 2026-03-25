# Quick Start

This tutorial registers a command, runs it, and cleans up -- all in under a minute.

## Step 1: Register a command

```bash
navigator register hello-world --prompt "echo hello from navigator" --environment /tmp
```

```text
Registered command 'hello-world'
```

This registers a command named "hello-world" that tells Claude to echo a message, running in `/tmp`.

## Step 2: Run the command

Check that the command is registered:

```bash
navigator list
```

```text
                              Registered Commands
┏━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Name        ┃ Status ┃ Namespace ┃ Environment ┃ Created             ┃
┡━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ hello-world │ active │ default   │ /tmp        │ 2026-03-25T20:18:…  │
└─────────────┴────────┴───────────┴─────────────┴─────────────────────┘
```

Preview what would execute without actually running it:

```bash
navigator exec hello-world --dry-run
```

```text
╭────────────────────────────── Dry Run ──────────────────────────────╮
│ Command:    hello-world                                             │
│ Namespace:  default                                                 │
│ Directory:  /tmp                                                    │
│ Args:       claude -p echo hello from navigator --print             │
│ Env keys:   HOME, LANG, PATH, SHELL, TERM                          │
│ Tools:      (none)                                                  │
╰─────────────────────────────────────────────────────────────────────╯
```

The dry run shows the exact Claude Code invocation, working directory, and environment variables that would be passed.

## Step 3: Clean up

Remove the test command:

```bash
navigator delete hello-world --force
```

```text
Deleted command 'hello-world'
```

!!! tip
    All commands support `--output json` for machine-readable output. See the [CLI Reference](../reference/cli.md) for details.

## What's Next

- [CLI Reference](../reference/cli.md) -- full command documentation
- Feature Guides -- scheduling, file watching, chaining, and more (coming soon)
