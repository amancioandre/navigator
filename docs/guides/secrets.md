# Secrets

Navigator injects secrets from `.env` files into command environments, keeping credentials out of command definitions.

## Prerequisites

- A registered command (see [Quick Start](../getting-started/quickstart.md))
- A `.env` file containing your secrets

## Attach Secrets to a Command

Create a `.env` file with your credentials:

```bash
mkdir -p ~/.secrets/navigator
cat > ~/.secrets/navigator/my-task.env << 'EOF'
API_KEY=sk-example123
DATABASE_URL=postgres://user:pass@localhost:5432/mydb
EOF
```

Register a command with secrets attached:

```bash
navigator register my-task --prompt "run migration" --environment ./app --secrets ~/.secrets/navigator/my-task.env
```

The `--secrets` flag accepts a path to any `.env` file. Navigator reads the file at execution time and injects each key-value pair as an environment variable.

## Environment Isolation

Navigator does **not** pass the full parent environment to commands. Instead, it builds a clean environment in layers:

1. **Whitelist** -- only these variables are inherited from the parent process: `PATH`, `HOME`, `LANG`, `TERM`, `SHELL`
2. **Secrets** -- key-value pairs from the `.env` file are merged in after the whitelist
3. **Chain metadata** -- correlation IDs (`NAVIGATOR_CHAIN_ID`) are added last

This prevents accidental leakage of sensitive parent environment variables. Your command only sees what Navigator explicitly provides.

## Common Patterns

### Per-project secrets

Organize secrets by project using namespaces. Each namespace auto-resolves secrets from `~/.secrets/{namespace}/`:

```text
~/.secrets/myproject/api.env
~/.secrets/myproject/db.env
~/.secrets/another-project/keys.env
```

See [Namespaces](namespaces.md) for details on per-project secret organization.

### Update secrets path

Change the secrets file for an existing command:

```bash
navigator update my-task --secrets /new/path/to/.env
```

## File Permissions

!!! warning
    Navigator warns if your `.env` file has group or other read permissions. Secrets files should be readable only by your user: `chmod 600 <path>`.

Set restrictive permissions on secrets files:

```bash
chmod 600 ~/.secrets/navigator/my-task.env
```

## Troubleshooting

- **Secrets not available in command:** verify the secrets path with `navigator show my-task`, then check that the file exists and is not empty.

- **Permission warning:** run `chmod 600` on the secrets file to restrict access to your user only.

- **Wrong secrets loaded:** if you are using namespaces, check whether namespace auto-resolution is overriding your explicit path. An explicit `--secrets` flag always takes priority.

## What's Next

- [Namespaces](namespaces.md) -- organize commands and secrets by project
- Configuration guide -- customize `secrets_base_path` and other settings
