# Namespaces

Namespaces organize commands into groups, each with its own secrets directory.

## Prerequisites

- Navigator installed (see [Installation](../getting-started/installation.md))

## Create a Namespace

```bash
navigator namespace create myproject --description "My web app"
```

```text
Created namespace 'myproject'
```

Namespace names must use lowercase letters, numbers, and hyphens only (`^[a-z0-9][a-z0-9-]*$`).

!!! tip
    The `default` namespace is used when no `--namespace` flag is provided. You do not need to create it.

## Register Commands in a Namespace

```bash
navigator register build --prompt "build the project" --environment ./app --namespace myproject
```

```text
Registered command 'build' in namespace 'myproject'
```

List commands in a specific namespace:

```bash
navigator list --namespace myproject
```

```text
                         Registered Commands (myproject)
┏━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Name  ┃ Status ┃ Namespace ┃ Environment ┃ Created             ┃
┡━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ build │ active │ myproject │ ./app       │ 2026-03-25T20:30:…  │
└───────┴────────┴───────────┴─────────────┴─────────────────────┘
```

## Common Patterns

### Cross-namespace references

Use qualified names (`namespace:command`) when chaining commands across namespaces:

```bash
navigator chain myproject:build --next myproject:deploy
```

See [Command Chaining](chaining.md) for full details on chain configuration and failure handling.

### Per-namespace secrets

Commands in a namespace auto-resolve secrets to `~/.secrets/{namespace}/`. For example, commands in the `myproject` namespace look for secrets in `~/.secrets/myproject/`.

An explicit `--secrets` flag on register or update overrides auto-resolution:

```bash
navigator register deploy --prompt "deploy app" --environment ./app --namespace myproject --secrets ~/custom/deploy.env
```

## List and Delete Namespaces

List all namespaces with their command counts:

```bash
navigator namespace list
```

```text
                        Namespaces
┏━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name      ┃ Commands ┃ Description             ┃
┡━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ default   │ 3        │ Default namespace       │
│ myproject │ 2        │ My web app              │
└───────────┴──────────┴─────────────────────────┘
```

Delete a namespace:

```bash
navigator namespace delete myproject --force
```

```text
Deleted namespace 'myproject'
```

The `--force` flag is required if the namespace contains commands. Without it, Navigator refuses the deletion. The `default` namespace cannot be deleted.

## Troubleshooting

- **Invalid namespace name:** names must match `^[a-z0-9][a-z0-9-]*$` -- use lowercase letters, numbers, and hyphens only. Names must start with a letter or number.

- **Cannot delete namespace:** use the `--force` flag to delete a namespace that contains commands, or remove the commands first. The `default` namespace cannot be deleted under any circumstances.

- **Secrets not loading for namespace:** verify that the `~/.secrets/{namespace}/` directory exists and contains `.env` files. Check the command's secrets path with `navigator show command-name`.

## What's Next

- [Secrets](secrets.md) -- environment isolation and permission details
- [Command Chaining](chaining.md) -- cross-namespace chain configuration
