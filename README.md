# PGClockToolBox

> 🛠️ A modern, safe and simple server toolbox for **PasarGuard**.

PGClockToolBox is installed **directly on the same Ubuntu server where PasarGuard is running**. It puts the most important server, backup, network and traffic-management operations behind a clean web panel so users do not need to work with complicated shell commands or configuration files.

[![Ubuntu](https://img.shields.io/badge/Ubuntu-22.04%2B-orange?logo=ubuntu)](https://ubuntu.com/)
[![PasarGuard](https://img.shields.io/badge/PasarGuard-supported-orange)](https://github.com/PasarGuard/panel)
[![Xray](https://img.shields.io/badge/Core-Xray-orange)](https://github.com/XTLS/Xray-core)
[![WireGuard](https://img.shields.io/badge/Network-WireGuard-orange)](https://www.wireguard.com/)

## ✨ What is PGClockToolBox?

PGClockToolBox is designed around one principle:

**Detect → Snapshot → Apply → Verify → Rollback / Repair**

Instead of exposing dangerous commands to the user, the application detects the actual server state, validates an operation, creates a recovery point when necessary, applies the change, verifies the result and rolls back or repairs when possible.

## 🚀 Features

### 💾 Professional PasarGuard Backup

- Full PasarGuard backup from the same server
- SQLite, PostgreSQL, TimescaleDB, MySQL and MariaDB detection
- PGClockMG-compatible archive layouts
- Backup manifest and metadata
- SHA-256 integrity checks
- ZIP/archive validation
- Local Node recovery artifacts when safely discoverable
- Backup history and status
- Scheduled automatic backups
- Retention and automatic cleanup
- Telegram delivery
- HTTP/SOCKS proxy support for Telegram
- Automatic handling of large Telegram backups
- Delivery status separated from backup status

### ⚡ Server Optimizer

- System and network discovery
- BBR detection and controlled configuration
- Conservative TCP/network tuning
- Pre-change snapshots
- Validation after changes
- Automatic rollback on failed verification
- Designed for VPN/proxy workloads rather than blindly applying internet "optimization scripts"

### 🌐 DNS Manager

- Detect current resolver configuration
- Support common DNS providers
- IPv4/IPv6 aware configuration
- systemd-resolved aware
- Configuration backup before mutation
- Connectivity validation
- Restore previous configuration

### 🛡️ WARP

- Detect Cloudflare WARP installation
- WARP status
- Connect / disconnect
- Host-based selective routing
- IP/CIDR selective routing
- Designed for selective egress rather than forcing all server traffic through WARP

### 🎯 Traffic Routing

Routing policies can describe:

- Domains
- IP addresses
- CIDRs
- Ports
- GeoIP rules
- GeoSite rules
- Direct routing
- WARP routing
- Proxy routing

Built-in examples include services such as Google, YouTube, Gemini, Spotify and OpenAI/ChatGPT.

The routing layer validates and previews policies before they are applied.

### 🩺 Health & Auto-Healing

The toolbox monitors important components such as:

- PasarGuard
- Xray
- WireGuard
- Docker
- DNS
- Internet connectivity
- Disk
- Memory
- Load

When a recoverable service failure is detected, the healing layer can perform conservative recovery actions and verify the result.

### 🔐 Security

Security is a core part of the design:

- No arbitrary shell execution from the web UI
- Fixed argument-list subprocess calls
- Authentication for protected APIs
- Protected configuration files
- Sensitive values are not written to normal logs
- Audit trail for important operations
- Snapshots before risky mutations
- Validation before applying configuration changes
- Rollback where technically possible

## 🖥️ Web Panel

PGClockToolBox runs on:

```text
http://SERVER_IP:6000
```

### Languages

- 🇮🇷 فارسی — default
- 🇬🇧 English
- 🇷🇺 Русский

The UI is designed for both RTL and LTR layouts, with Persian as the default experience.

### Design

- Minimal
- Modern
- Responsive
- Persian-first
- Orange brand identity
- Dark/light friendly architecture
- Designed to avoid unnecessary dashboards and configuration clutter

## 📦 Requirements

PGClockToolBox is intentionally designed for the server that already runs PasarGuard.

### Supported OS

- Ubuntu 22.04+

### Required environment

- PasarGuard installed on the same server
- Root privileges for installation and system operations
- Xray and/or WireGuard according to the PasarGuard installation

The application performs installation discovery instead of assuming a fixed server configuration.

## 🏗️ Architecture

```text
                         PGClockToolBox
                                │
                ┌───────────────┴───────────────┐
                │                               │
             Web UI                         Core Services
                │                               │
        ┌───────┼────────┐        ┌─────────────┼─────────────┐
        │       │        │        │             │             │
      Backup  Network   WARP   Discovery     Health       Security
        │       │        │        │             │             │
        └───────┴────────┴────────┴─────────────┴─────────────┘
                                │
                          PasarGuard Server
                                │
                         ┌──────┴──────┐
                         │             │
                       Xray        WireGuard
```

Long-running operations are designed to run outside the web request lifecycle so a large backup or network operation does not block the panel.

## 💾 Backup & PGClockMG

PGClockToolBox treats **PGClockMG as an external restore target**.

The important rule is:

> **PGClockMG is not modified to make ToolBox work. ToolBox produces backups compatible with the existing PGClockMG implementation.**

The backup contract is documented in:

```text
docs/backup-restore-contract.md
```

The contract covers:

- Database formats
- Archive layouts
- Manifest metadata
- Node recovery information
- Integrity verification
- Secrets handling
- Compatibility metadata
- Validation fixtures

## 🔒 Routing Safety

PGClockToolBox does not blindly overwrite PasarGuard's generated Xray configuration.

PasarGuard owns the active core configuration, so the toolbox first works with validated routing policies and previews. Live application must go through the appropriate PasarGuard configuration/API path rather than bypassing the panel's configuration lifecycle.

This prevents a common failure mode where a manually edited configuration is later overwritten by PasarGuard or leaves the panel and core out of sync.

## 📁 Project Structure

```text
PGClockToolBox/
├── backend/
│   └── app/
│       ├── api/
│       ├── core/
│       ├── models/
│       ├── services/
│       │   ├── backup/
│       │   ├── discovery/
│       │   ├── dns/
│       │   ├── optimizer/
│       │   ├── routing/
│       │   ├── health/
│       │   ├── nodes/
│       │   └── warp/
│       └── main.py
├── docs/
├── frontend/
├── scripts/
├── systemd/
└── tests/
```

## 🧪 Development & Testing

The project uses automated backend tests and GitHub Actions CI.

Before changing a server configuration, operations should follow the safety lifecycle:

```text
Detect
  ↓
Validate
  ↓
Snapshot
  ↓
Apply
  ↓
Verify
  ├── ✓ Success
  └── ✗ Rollback / Repair
```

## ⚠️ Production Status

The current branch contains the foundation and the major server-control components, but **not every advanced operation should be considered production-safe merely because its API exists**.

In particular, live routing integration and full end-to-end backup/restore validation against every supported database/version combination require real PasarGuard installations and integration fixtures.

Do not enable automated destructive operations on a production server until the corresponding integration test has passed for that environment.

## 🤝 Related Project

### PGClockMG

PGClockMG is the companion migration/restore project used as the external Backup restore target.

**PGClockMG source code is intentionally not modified by PGClockToolBox.**

## 📜 License

License will be defined before the first stable release.

---

Made for the PasarGuard ecosystem by **MrClock** 🟧
