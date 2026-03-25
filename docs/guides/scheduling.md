# Scheduling

Navigator uses the system crontab to run commands on a schedule.

## Prerequisites

- A registered, active command (see [Quick Start](../getting-started/quickstart.md))

## Schedule a Command

```bash
navigator schedule hello-world --cron "0 9 * * *"
```

```text
Scheduled 'hello-world' with cron: 0 9 * * *
```

Navigator validates that the command exists and is active before creating the schedule. Each crontab entry is tagged with a `navigator:{command_name}` comment so Navigator can find and manage its own entries without touching other crontab lines.

!!! tip
    Re-scheduling a command updates the existing crontab entry rather than creating a duplicate.

## Common Patterns

### Daily at 9 AM

```bash
navigator schedule my-task --cron "0 9 * * *"
```

### Every Hour

```bash
navigator schedule my-task --cron "0 * * * *"
```

### Weekdays Only at 9 AM

```bash
navigator schedule my-task --cron "0 9 * * 1-5"
```

### Every 15 Minutes

```bash
navigator schedule my-task --cron "*/15 * * * *"
```

### Weekly on Sunday at Midnight

```bash
navigator schedule my-task --cron "0 0 * * 0"
```

## List and Remove Schedules

List all scheduled commands:

```bash
navigator schedule --list
```

```text
                         Scheduled Commands
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Command     ┃ Cron          ┃ Description                     ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ hello-world │ 0 9 * * *     │ Every day at 09:00              │
│ my-task     │ 0 9 * * 1-5   │ Weekdays at 09:00               │
└─────────────┴───────────────┴─────────────────────────────────┘
```

Remove a schedule:

```bash
navigator schedule my-task --remove
```

```text
Removed schedule for 'my-task'
```

## Troubleshooting

- **Schedule not running:** Verify the command is active with `navigator list`. Check the system crontab with `crontab -l | grep navigator` to confirm the entry exists.

- **Wrong time zone:** Cron uses the system time zone. Check your current time zone with `date`. Navigator does not override or convert time zones.

## What's Next

- [Command Chaining](chaining.md) -- trigger commands after scheduled runs complete
- Systemd Service -- ensure the Navigator daemon survives reboots (coming soon)
