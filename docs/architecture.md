# PGClockToolBox Architecture

## Deployment model

PGClockToolBox is installed on the same Ubuntu 22.04+ server that already runs PasarGuard. It is not a remote management server.

The application listens on TCP port `7100` by default.

## Traffic/core scope

PasarGuard traffic is treated as Xray and WireGuard traffic. sing-box is not a project dependency or routing core.

WARP is an optional egress layer for selected traffic; it does not replace Xray or WireGuard.

## Safety model

Every mutating feature must follow:

```text
Discover → Validate → Snapshot → Apply → Verify → Repair/Rollback
```

The web layer never accepts arbitrary shell strings. Operations expose typed, allow-listed actions through services.

## Foundation services

- discovery: read-only host and service inventory
- installation: PasarGuard/Xray/WireGuard/Docker inventory
- backup: database detection, manifest and collection planning
- future: backup execution, Telegram delivery, optimizer, DNS, WARP, routing, health/healing

## Backup compatibility

The producer must remain compatible with the existing PGClockMG restore/analyze behavior. PGClockMG source code is not modified by this project.

The ToolBox may add metadata such as `pgclock/manifest.json`, but must continue to emit the layouts already recognized by PGClockMG.

## Secrets

Credentials are never returned by discovery endpoints or written to ordinary logs. Backup encryption and secret handling will be implemented before production backup delivery.
