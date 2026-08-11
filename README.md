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

The installer checks Ubuntu/PasarGuard, installs dependencies, deploys the app, creates the admin token, installs the systemd unit, **restarts** the service, opens UFW if active, and verifies that the dashboard HTML responds on port `7100`.

### 🌐 Open the Web Panel

The installer prints the public URL and admin token when it finishes.

```bash
# health / URLs / service state
curl -fsSL https://raw.githubusercontent.com/Mrclocks/PGClockToolBox/main/install.sh | bash -s -- status
```

If the panel does not open remotely:

```bash
systemctl status pgclocktoolbox --no-pager
ss -lntp | grep ':7100'
journalctl -u pgclocktoolbox -n 100 --no-pager
```

> Allow TCP `7100` in your cloud/provider firewall (or security group) as well as UFW.

Optional custom port:

```bash
PGCLOCK_PORT=2096 bash install.sh
```

### 🔑 Admin Token

Printed once by the installer and stored at:

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

```bash
# keep local backups/config
curl -fsSL https://raw.githubusercontent.com/Mrclocks/PGClockToolBox/main/install.sh | bash -s -- uninstall --yes

# also delete /var/lib/pgclocktoolbox (config, logs, backups)
curl -fsSL https://raw.githubusercontent.com/Mrclocks/PGClockToolBox/main/install.sh | bash -s -- uninstall --purge --yes
```

> Uninstall never modifies or removes PasarGuard.

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
