# PGClockToolBox

> 🛠️ A modern, safe and simple server toolbox for **PasarGuard**.

## 🚀 Installation

PGClockToolBox is installed **directly on the same Ubuntu server where PasarGuard is already installed**.

### Requirements

- Ubuntu **22.04 or newer**
- A working PasarGuard installation on the same server
- Root access
- Internet access during installation

The installer automatically installs the required system packages, creates an isolated Python environment, installs PGClockToolBox, creates its data/backup directories and registers the systemd service.

### One-line installation

Run the following command as `root`:

```bash
curl -fsSL https://raw.githubusercontent.com/Mrclocks/PGClockToolBox/main/install.sh | bash
```

> **Important:** Run this on the **PasarGuard server itself**, not on a separate management server.

### Installation process

The installer automatically:

1. Checks that the OS is Ubuntu 22.04+.
2. Verifies that PasarGuard exists at `/opt/pasarguard`.
3. Installs required packages.
4. Downloads PGClockToolBox to `/opt/pgclocktoolbox`.
5. Creates an isolated Python virtual environment.
6. Installs backend dependencies.
7. Creates protected application directories under `/var/lib/pgclocktoolbox`.
8. Generates the initial admin authentication token.
9. Installs and enables the `pgclocktoolbox.service` systemd service.
10. Starts the web panel and verifies that the service is running.

### Open the panel

After installation, open:

```text
http://SERVER_IP:6000
```

The installer prints the location of the admin token:

```text
/var/lib/pgclocktoolbox/data/admin_token
```

Keep this token private. It provides access to protected Toolbox APIs.

### Check service status

```bash
systemctl status pgclocktoolbox --no-pager
```

View logs:

```bash
journalctl -u pgclocktoolbox -f
```

Restart:

```bash
systemctl restart pgclocktoolbox
```

### Uninstall

PGClockToolBox does not currently provide an automatic destructive uninstall command. If you want to remove it, first preserve any backups under `/var/lib/pgclocktoolbox/backups`, then stop and disable the service before removing its files.

```bash
systemctl disable --now pgclocktoolbox
rm -rf /opt/pgclocktoolbox
rm -rf /var/lib/pgclocktoolbox
rm -f /etc/systemd/system/pgclocktoolbox.service
systemctl daemon-reload
```

> **Warning:** Removing `/var/lib/pgclocktoolbox` deletes Toolbox configuration, logs and locally stored backups. It does **not** uninstall or modify PasarGuard itself.

## ✨ What is PGClockToolBox?

PGClockToolBox is installed **directly on the same Ubuntu server where PasarGuard is running**. It puts the most important server, backup, network and traffic-management operations behind a clean web panel so users do not need to work with complicated shell commands or configuration files.

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

The contract covers database formats, archive layouts, manifest metadata, node recovery information, integrity verification, secrets handling, compatibility metadata and validation fixtures.

## 🔒 Routing Safety

PGClockToolBox does not blindly overwrite PasarGuard's generated Xray configuration.

PasarGuard owns the active core configuration, so the toolbox first works with validated routing policies and previews. Live application must go through the appropriate PasarGuard configuration/API path rather than bypassing the panel's configuration lifecycle.

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
├── deploy/
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

The foundation and major server-control components are implemented. Live routing integration and full end-to-end backup/restore validation against every supported database/version combination should still be validated on real PasarGuard installations before a stable production release.

Do not enable automated destructive operations on a production server until the corresponding integration test has passed for that environment.

## 🤝 Related Project

### PGClockMG

PGClockMG is the companion migration/restore project used as the external Backup restore target.

**PGClockMG source code is intentionally not modified by PGClockToolBox.**

## 📜 License

License will be defined before the first stable release.

---

Made for the PasarGuard ecosystem by **MrClock** 🟧
