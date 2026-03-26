# Command Chaining

Navigator chains commands so one triggers the next on completion, with correlation tracking and cycle protection.

## Prerequisites

- Two or more registered commands (see [Quick Start](../getting-started/quickstart.md))

## Chain Commands

Link one command to run after another:

```bash
navigator chain build-project --next run-tests
```

```text
Chained 'build-project' -> 'run-tests'
```

The chain is stored as a `chain_next` field on the command. View the full chain:

```bash
navigator chain build-project --show
```

```text
build-project -> run-tests
```

!!! tip
    Use `navigator chain cmd --show` to visualize the full chain before adding new links.

## Common Patterns

### Build-Test-Deploy Pipeline

Chain three commands together by linking each step to the next:

```bash
navigator chain build --next test
navigator chain test --next deploy
```

View the complete pipeline:

```bash
navigator chain build --show
```

```text
build -> test -> deploy
```

### Continue on Failure

By default, a chain stops when any command fails. Override this for non-critical steps:

```bash
navigator chain build-project --next notify-team --on-failure continue
```

With `continue`, the next command runs regardless of the previous command's exit status. The default behavior is `stop`.

### Cross-Namespace Chaining

Chain commands across namespaces using the qualified name syntax `namespace:command`:

```bash
navigator chain myproject:build --next myproject:deploy
```

This allows pipelines that span multiple project namespaces.

## Correlation IDs

Navigator generates a UUID4 correlation ID for each chain execution. This ID is passed as the `NAVIGATOR_CHAIN_ID` environment variable to every command in the chain.

Use correlation IDs to trace log output across chained executions:

```bash
# Inside a chained command, the correlation ID is available as:
echo $NAVIGATOR_CHAIN_ID
# e.g., 550e8400-e29b-41d4-a716-446655440000
```

All commands in a single chain run share the same correlation ID, making it straightforward to search logs for a complete pipeline execution.

## Cycle Detection

Navigator checks for cycles before creating a chain link. Both self-links and transitive cycles are rejected:

```bash
# Self-link: rejected
navigator chain build --next build
```

```text
Error: Cycle detected: build -> build
```

```bash
# Transitive cycle: A -> B -> C -> A is rejected
navigator chain deploy --next build
```

```text
Error: Cycle detected: deploy -> build -> test -> deploy
```

## Chain Depth Limit

The `max_chain_depth` configuration option limits how many commands can execute in a single chain run. The default is 10. Chains exceeding this depth stop executing and log a warning.

Adjust the limit in `config.toml`:

```toml
max_chain_depth = 20
```

## Remove a Chain Link

```bash
navigator chain build-project --remove
```

```text
Removed chain link from 'build-project'
```

This removes the `chain_next` link from the command. Downstream links are not affected.

## Troubleshooting

- **Chain stops unexpectedly:** Check if a command in the chain failed. The default behavior is to stop on the first failure. Use `--on-failure continue` on the link if the next step should run regardless.

- **Cycle detected error:** Run `navigator chain cmd --show` to see the full chain and identify which link creates the loop. Remove the conflicting link with `--remove` before adding the new one.

- **Chain too deep:** The chain exceeded the `max_chain_depth` limit (default: 10). Increase the value in `config.toml` if your pipeline legitimately requires more steps.

## What's Next

- [Namespaces](namespaces.md) -- organize commands across projects with isolated secrets
- [Configuration](configuration.md) -- adjust `max_chain_depth` and other settings
