#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/opt/pgclocktoolbox"
VENV="$APP_ROOT/.venv"
REPO="https://github.com/Mrclocks/PGClockToolBox.git"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this installer as root." >&2
  exit 1
fi

if [[ ! -r /etc/os-release ]]; then
  echo "Cannot detect operating system." >&2
  exit 1
fi

. /etc/os-release
if [[ "${ID:-}" != "ubuntu" ]]; then
  echo "PGClockToolBox requires Ubuntu 22.04+." >&2
  exit 1
fi

major="${VERSION_ID%%.*}"
minor="${VERSION_ID#*.}"
if (( major < 22 )); then
  echo "PGClockToolBox requires Ubuntu 22.04+. Detected ${VERSION_ID}." >&2
  exit 1
fi

if [[ ! -d /opt/pasarguard ]] || [[ ! -f /opt/pasarguard/.env ]]; then
  echo "PasarGuard installation was not detected at /opt/pasarguard." >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3 python3-venv python3-pip git

if [[ -d "$APP_ROOT/.git" ]]; then
  git -C "$APP_ROOT" fetch --all --prune
  git -C "$APP_ROOT" checkout main
  git -C "$APP_ROOT" pull --ff-only
else
  rm -rf "$APP_ROOT"
  git clone --depth 1 "$REPO" "$APP_ROOT"
fi

python3 -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip
"$VENV/bin/pip" install -r "$APP_ROOT/backend/requirements.txt"

install -d -m 0700 /var/lib/pgclocktoolbox/{data,backups,logs}

install -m 0644 "$APP_ROOT/systemd/pgclocktoolbox.service" /etc/systemd/system/pgclocktoolbox.service
systemctl daemon-reload
systemctl enable --now pgclocktoolbox.service

sleep 1
if ! systemctl is-active --quiet pgclocktoolbox.service; then
  journalctl -u pgclocktoolbox.service --no-pager -n 80
  exit 1
fi

echo "PGClockToolBox is running on port 6000."
