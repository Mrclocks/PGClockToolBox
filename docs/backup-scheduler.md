# Scheduled Backups

PGClockToolBox runs a lightweight systemd timer every 15 minutes. The timer only performs a backup when the configured interval is due.

Supported intervals: 1, 2, 3, 4, 6, 8, 12, 24, 48 and 72 hours.

Retention is enforced after a successful local backup. The newest N `pasarguard-full-*.zip` archives are retained.

## Telegram

Telegram delivery is optional. Configuration is stored in `/var/lib/pgclocktoolbox/data/telegram.env` with mode `0600` and is never returned by the API.

Supported settings:

- Bot token
- Chat ID
- Optional HTTP(S) proxy

The scheduled worker sends the completed archive only after local integrity validation succeeds. A delivery failure is recorded separately from a local backup failure.
