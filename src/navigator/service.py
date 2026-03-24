"""Navigator service -- systemd unit file generation and service management.

Generates a systemd user unit file pointing to the navigator binary,
installs/uninstalls the service, and wraps systemctl --user commands
for start/stop/restart/status control.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def generate_unit_file() -> str:
    """Generate the systemd unit file content for the Navigator watcher daemon.

    Resolves the navigator binary path via shutil.which so the ExecStart
    always points to the correct installation location.

    Raises:
        FileNotFoundError: If navigator binary is not found on PATH.
    """
    navigator_path = shutil.which("navigator")
    if navigator_path is None:
        msg = "navigator binary not found on PATH"
        raise FileNotFoundError(msg)

    return f"""\
[Unit]
Description=Navigator Watcher Daemon
After=network.target

[Service]
Type=simple
ExecStart={navigator_path} daemon
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
"""


def get_service_path() -> Path:
    """Return the path to the systemd user unit file.

    Systemd user units have a fixed location; platformdirs is not used here.
    """
    return Path.home() / ".config" / "systemd" / "user" / "navigator.service"


def install_service(enable_linger: bool = True) -> Path:
    """Install the Navigator systemd user service.

    Generates the unit file, writes it, reloads systemd, enables the service,
    and optionally enables loginctl linger for the current user.

    Args:
        enable_linger: If True, run loginctl enable-linger so the user service
            starts at boot even without a login session.

    Returns:
        Path to the installed unit file.
    """
    content = generate_unit_file()
    service_path = get_service_path()
    service_path.parent.mkdir(parents=True, exist_ok=True)
    service_path.write_text(content)

    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(
        ["systemctl", "--user", "enable", "navigator.service"], check=True
    )

    if enable_linger:
        subprocess.run(["loginctl", "enable-linger"], check=False)

    return service_path


def uninstall_service() -> bool:
    """Uninstall the Navigator systemd user service.

    Stops and disables the service, removes the unit file, and reloads systemd.

    Returns:
        True if the unit file existed before removal, False otherwise.
    """
    subprocess.run(
        ["systemctl", "--user", "stop", "navigator.service"], check=False
    )
    subprocess.run(
        ["systemctl", "--user", "disable", "navigator.service"], check=False
    )

    service_path = get_service_path()
    existed = service_path.exists()
    service_path.unlink(missing_ok=True)

    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)

    return existed


def service_control(action: str) -> subprocess.CompletedProcess:
    """Run a systemctl --user command for the Navigator service.

    Args:
        action: One of "status", "start", "stop", "restart".

    Returns:
        The CompletedProcess result from systemctl.

    Raises:
        ValueError: If action is not a valid systemctl action.
    """
    valid_actions = ("status", "start", "stop", "restart")
    if action not in valid_actions:
        msg = f"Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}"
        raise ValueError(msg)

    return subprocess.run(
        ["systemctl", "--user", action, "navigator.service"],
        capture_output=True,
        text=True,
    )
