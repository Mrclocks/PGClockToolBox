# PGClockToolBox

PasarGuard Server Toolbox — a simple, safe and modern web panel for managing the same server where PasarGuard is installed.

## Scope

- Full PasarGuard + local node backup compatible with PGClockMG
- Scheduled backups with retention
- Telegram delivery with optional proxy
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

Supported languages: Persian (`fa`), English (`en`), Russian (`ru`).

## Safety principles

1. Detect before changing.
2. Never expose arbitrary shell execution through the web layer.
3. Validate network changes and keep rollback data.
4. A backup is successful only after archive integrity validation.
5. Telegram delivery is separate from local backup success.
6. PGClockMG is an external compatibility target; its source code is not modified.

## Development status

Foundation, backup engine, scheduled delivery, Telegram transport, DNS management, optimizer and WARP controls are implemented on `feature/foundation`. Advanced routing, health/auto-recovery and final hardening remain.
