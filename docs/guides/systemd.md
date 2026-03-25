# Systemd Service

Navigator installs a systemd user service so the watcher daemon starts automatically and survives reboots.

## Prerequisites

- A systemd-based Linux system (Ubuntu, Pop!_OS, etc.)
- At least one file watcher configured (see [File Watching](file-watching.md))

## Install the Service

```bash
navigator install-service
```

```text
Service file written to ~/.config/systemd/user/navigator.service
Daemon reloaded
Service enabled
Linger enabled for user
Navigator service installed and started
```

This command:

1. Writes a unit file to `~/.config/systemd/user/navigator.service`
2. Runs `systemctl --user daemon-reload`
3. Enables the service to start on boot
4. Calls `loginctl enable-linger` so the service runs even when you are not logged in

If linger is already configured or not desired, use the `--no-linger` flag:

```bash
navigator install-service --no-linger
```

## Control the Service

```bash
navigator service start
```

```bash
navigator service stop
```

```bash
navigator service restart
```

```bash
navigator service status
```

```text
navigator.service - Navigator Watcher Daemon
     Loaded: loaded (~/.config/systemd/user/navigator.service; enabled)
     Active: active (running) since Tue 2026-03-25 14:30:00 PDT
   Main PID: 12345 (navigator)
     CGroup: /user.slice/user-1000.slice/user@1000.service/app.slice/navigator.service
```

## Common Patterns

### Verify reboot survival

After installing the service, reboot and confirm the daemon is still running:

```bash
navigator install-service
sudo reboot
```

After reboot:

```bash
navigator service status
```

The service should show `active (running)`. If linger is enabled, the service starts without requiring a login session.

### Foreground mode for debugging

Run the watcher daemon in the foreground with visible log output:

```bash
navigator daemon
```

!!! tip
    Run `navigator daemon` in the foreground first to verify your watchers work correctly, then install the systemd service for permanent operation.

This is useful for troubleshooting watcher configuration before installing the service.

## Uninstall the Service

```bash
navigator uninstall-service
```

```text
Service stopped
Service disabled
Service file removed
Daemon reloaded
Navigator service uninstalled
```

This stops the service, disables it from starting on boot, removes the unit file from `~/.config/systemd/user/`, and reloads the systemd daemon.

## Unit File Details

The generated unit file:

```ini
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
```

- `Restart=on-failure` means the daemon restarts automatically if it crashes
- `RestartSec=5` waits 5 seconds before each restart attempt
- `Environment=PYTHONUNBUFFERED=1` ensures log output is not buffered
- `{navigator_path}` is replaced with the actual path to your Navigator installation

## Troubleshooting

- **Service not starting:** run `navigator daemon` in the foreground to see error output directly. Check system logs with `journalctl --user -u navigator` for details.

- **Service does not survive reboot:** verify linger is enabled with `loginctl show-user $USER | grep Linger`. If it shows `Linger=no`, re-run `navigator install-service` without the `--no-linger` flag.

- **Service running but watchers not triggering:** verify watchers are configured with `navigator watch --list`. The service only runs watchers that were set up before install.

## What's Next

- [File Watching](file-watching.md) -- configure watchers for the daemon to manage
- [Scheduling](scheduling.md) -- cron-based triggers that do not need the daemon
