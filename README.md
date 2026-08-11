# PGClockToolBox

> 🛠️ A modern, safe and simple server toolbox for **PasarGuard**.

## 🚀 Installation

PGClockToolBox is installed **directly on the same Ubuntu server where PasarGuard is already installed**.

### Requirements

- Ubuntu **22.04 or newer**
- A working PasarGuard installation on the same server
- Root access
- Internet access during installation

### One-line installation

Run this command as `root` **on the PasarGuard server itself**:

```bash
curl -fsSL https://raw.githubusercontent.com/Mrclocks/PGClockToolBox/main/install.sh | bash
```

The installer automatically checks Ubuntu/PasarGuard, installs dependencies, creates the Python environment, initializes authentication, installs the systemd service and starts the panel.

### 🌐 Open the Web Panel

**The installer prints the exact URL at the end of a successful installation.**

It will look like:

```text
==================================================
 PGClockToolBox installed successfully
==================================================

Web Panel:
  http://YOUR_SERVER_IP:7100/

Admin token:
  /var/lib/pgclocktoolbox/data/admin_token

Service:
  systemctl status pgclocktoolbox --no-pager

Logs:
  journalctl -u pgclocktoolbox -f
==================================================
```

Open the displayed `http://YOUR_SERVER_IP:7100/` address in your browser.

If the panel does not open, first run:

```bash
systemctl status pgclocktoolbox --no-pager
ss -lntp | grep ':7100'
```

Then check:

```bash
journalctl -u pgclocktoolbox -n 100 --no-pager
```

> If port `7100` is blocked by your server provider's firewall/security group, allow TCP port `7100` there as well.

### 🔑 Admin Token

The initial admin token is stored at:

```text
/var/lib/pgclocktoolbox/data/admin_token
```

Keep it private. It provides access to protected Toolbox APIs.

### Service commands

```bash
systemctl status pgclocktoolbox --no-pager
systemctl restart pgclocktoolbox
journalctl -u pgclocktoolbox -f
```

### Uninstall

PGClockToolBox does not currently provide an automatic destructive uninstall command. Preserve any local backups first.

```bash
systemctl disable --now pgclocktoolbox
rm -rf /opt/pgclocktoolbox
rm -rf /var/lib/pgclocktoolbox
rm -f /etc/systemd/system/pgclocktoolbox.service
systemctl daemon-reload
```

> **Warning:** Removing `/var/lib/pgclocktoolbox` deletes Toolbox configuration, logs and locally stored backups. It does not uninstall or modify PasarGuard.

## ✨ What is PGClockToolBox?

PGClockToolBox is installed **directly on the same Ubuntu server where PasarGuard is running**. It puts important server, backup, network and traffic-management operations behind a clean web panel.

The core safety principle is:

**Detect → Snapshot → Apply → Verify → Rollback / Repair**

## 🚀 Features

### 💾 Professional PasarGuard Backup

- Full PasarGuard backup from the same server
- SQLite, PostgreSQL, TimescaleDB, MySQL and MariaDB detection
- PGClockMG-compatible archive layouts
- Backup manifest and metadata
- SHA-256 integrity checks
- ZIP/archive validation
- Local Node recovery artifacts where safely discoverable
- Backup history and status
- Scheduled automatic backups
- Retention and automatic cleanup
- Telegram delivery
- HTTP/SOCKS proxy support for Telegram
- Large-backup handling

### ⚡ Server Optimizer

- System and network discovery
- BBR detection and controlled configuration
- Conservative TCP/network tuning
- Pre-change snapshots
- Validation and rollback

### 🌐 DNS Manager

- Resolver detection
- Common DNS providers
- IPv4/IPv6 aware configuration
- systemd-resolved aware
- Backup and restore
- Connectivity validation

### 🛡️ WARP

- WARP detection
- Connect / disconnect
- Host/IP/CIDR selective routing
- Selective egress instead of forcing all traffic through WARP

### 🎯 Traffic Routing

- Domain
- IP / CIDR
- Port
- GeoIP
- GeoSite
- DIRECT / WARP / PROXY policies
- Policy validation and preview

### 🩺 Health & Auto-Healing

- PasarGuard
- Xray
- WireGuard
- Docker
- DNS
- Internet connectivity
- Disk / memory / load
- Conservative recovery actions

### 🔐 Security

- No arbitrary shell execution from the web UI
- Fixed argument-list subprocess calls
- Authentication
- Protected configuration files
- Audit trail
- Snapshots before risky mutations
- Validation and rollback where possible

## 🖥️ Web Panel

Default address:

```text
http://SERVER_IP:7100/
```

Languages:

- 🇮🇷 فارسی — default
- 🇬🇧 English
- 🇷🇺 Русский

The UI is RTL/LTR aware, responsive, minimal and based on the orange PGClock brand identity.

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

## 💾 Backup & PGClockMG

PGClockMG is an external restore target. **Its source code is not modified.** ToolBox produces backups against the existing PGClockMG compatibility contract documented in:

```text
docs/backup-restore-contract.md
```

## 🔒 Routing Safety

PGClockToolBox does not blindly overwrite PasarGuard-generated Xray configuration. Active core configuration must remain under the appropriate PasarGuard configuration/API lifecycle.

## 📁 Project Structure

```text
PGClockToolBox/
├── backend/
│   └── app/
│       ├── api/
│       ├── core/
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
├── deploy/
├── systemd/
└── tests/
```

## 🧪 Testing

GitHub Actions runs the backend test suite automatically.

## ⚠️ Production Status

The foundation and major server-control components are implemented. Live routing integration and full end-to-end backup/restore validation across every supported PasarGuard/database/version combination should be validated on real installations before a stable production release.

## 🤝 Related Project

**PGClockMG** — companion migration/restore project for PGClockToolBox backups.

**PGClockMG source code is intentionally not modified by PGClockToolBox.**

## 📜 License

License will be defined before the first stable release.

---

Made for the PasarGuard ecosystem by **MrClock** 🟧
