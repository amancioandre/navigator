# Installation

## Prerequisites

- Python 3.12 or later

Check your version:

```bash
python3 --version
```

## Install with uv (recommended)

!!! tip
    [uv](https://docs.astral.sh/uv/) is Navigator's preferred toolchain -- faster and more reliable than pip.

Clone the repository and install globally:

```bash
git clone <repo-url> navigator
cd navigator
uv tool install .
```

This makes the `navigator` command available globally on your PATH.

## Install with pip

From the project directory:

```bash
pip install .
```

Ensure pip's script directory (typically `~/.local/bin`) is on your PATH.

## Verify installation

Run the built-in health check:

```bash
navigator doctor
```

Expected output:

```text
  PASS  Database: Database OK (0 commands)
  PASS  Navigator binary: Found at /home/user/.local/bin/navigator
  PASS  Registered paths: No commands registered
  PASS  Crontab sync: No crontab entries
  PASS  Service: Service not installed (optional)

5 checks: 5 passed, 0 failed, 0 warned
```

All checks passing means Navigator is installed and ready.

## What's Next

Follow the [Quick Start](quickstart.md) to register and run your first command.
