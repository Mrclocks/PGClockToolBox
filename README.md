# PGClockToolBox

PasarGuard Server Toolbox — a simple, safe and modern web panel for managing the same server where PasarGuard is installed.

## Scope

- Full PasarGuard + node backup compatible with PGClockMG
- Telegram delivery with optional proxy and scheduled backups
- Server/network optimizer
- DNS management
- WARP egress and selective routing
- GeoIP/GeoSite-style direct/proxy routing for Xray and WireGuard traffic
- Health monitoring, validation, rollback and auto-recovery

## Requirements

- Ubuntu 22.04+
- Installed PasarGuard on the same server
- Xray and/or WireGuard as used by the PasarGuard installation
- Root privileges

## Web panel

The panel listens on port `6000` by default.

Default language: Persian (`fa`)

Supported languages:

- فارسی (`fa`)
- English (`en`)
- Русский (`ru`)

## Design principles

1. Safe before clever: never apply a risky network change without validation and rollback protection.
2. Detect before changing: discover the actual PasarGuard, Xray, WireGuard, database, network and DNS state first.
3. Verify every operation: Apply → Verify → Roll back or repair when necessary.
4. No arbitrary shell execution from the web UI.
5. PGClockMG is treated as an external compatibility target; its source code is not modified.

## Development status

Foundation phase in progress.
