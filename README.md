# PGClockToolBox

PasarGuard Server Toolbox — a simple, safe and modern web panel for managing the same server where PasarGuard is installed.

## Requirements

- Ubuntu 22.04+
- PasarGuard installed on the same server
- Xray and/or WireGuard as used by the installation
- Root privileges
- Web panel: port `6000`

## Current capabilities

- Read-only installation discovery
- PasarGuard / database / Xray / WireGuard / Docker discovery
- Full backup engine with SQLite, PostgreSQL, TimescaleDB, MySQL and MariaDB support
- PGClockMG-compatible archive layouts plus ToolBox manifest
- Local node recovery artifacts where safely discoverable
- ZIP integrity validation and SHA-256 checksum
- Scheduled backups and retention
- Telegram delivery with HTTP/SOCKS proxy support through curl
- Automatic Telegram chunking for backups larger than the Bot API multipart limit
- DNS management with rollback
- Conservative BBR/network optimizer
- WARP status/connect/disconnect and selective host/IP controls
- Routing policy store with domain/IP/CIDR/GeoIP/GeoSite/port rules
- Xray routing preview and structural validation
- Health monitoring
- Conservative service auto-healing
- Protected audit log
- Modern responsive Persian-first dashboard

## Routing safety

PGClockToolBox deliberately does **not** edit a generated PasarGuard Xray configuration directly. PasarGuard owns core configuration and validates configurations through its API. Direct file edits could be overwritten or break synchronization. The current routing engine therefore supports rule management, preview and validation; live application will use the detected PasarGuard core-config API rather than bypassing it.

## Safety model

`Detect → Snapshot → Apply → Verify → Rollback/Repair`

The web layer never exposes arbitrary shell execution.

## Backup compatibility

PGClockMG is an external restore target. **PGClockMG source code is not modified.** The ToolBox backup contract and fixtures must remain compatible with the currently implemented PGClockMG analyzer/restore layouts.

## Languages

- فارسی (`fa`) — default
- English (`en`)
- Русский (`ru`)

## Development

The foundation is being developed on `feature/foundation` and CI runs the backend test suite on every push/PR.
