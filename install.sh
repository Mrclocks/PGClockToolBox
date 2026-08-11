#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/opt/pgclocktoolbox"
VENV="$APP_ROOT/.venv"
REPO="https://github.com/Mrclocks/PGClockToolBox.git"
PORT="6000"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this installer as root." >&2
  exit 1
fi

. /etc/os-release
if [[ "${ID:-}" != "ubuntu" ]]; then
  echo "PGClockToolBox requires Ubuntu 22.04+." >&2
  exit 1
fi
major="${VERSION_ID%%.*}"
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
apt-get install -y python3 python3-venv python3-pip git curl ca-certificates unzip procps iproute2 sqlite3 wireguard-tools

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
PYTHONPATH="$APP_ROOT/backend" "$VENV/bin/python" -c 'from app.services.auth import ensure_token; ensure_token()'

install -m 0644 "$APP_ROOT/systemd/pgclocktoolbox.service" /etc/systemd/system/pgclocktoolbox.service
systemctl daemon-reload
systemctl enable --now pgclocktoolbox.service

sleep 2
if ! systemctl is-active --quiet pgclocktoolbox.service; then
  echo "PGClockToolBox failed to start." >&2
  journalctl -u pgclocktoolbox --no-pager -n 100 >&2 || true
  exit 1
fi

if ! curl -fsS --max-time 5 "http://127.0.0.1:${PORT}/" >/dev/null; then
  echo "PGClockToolBox service is running but the web panel did not respond on port ${PORT}." >&2
  echo "Check: journalctl -u pgclocktoolbox -n 100 --no-pager" >&2
  exit 1
fi

SERVER_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
SERVER_IP="${SERVER_IP:-YOUR_SERVER_IP}"

echo
printf '%s\n' '=================================================='
printf '%s\n' ' PGClockToolBox installed successfully'
printf '%s\n' '=================================================='
echo
echo "Web Panel:"
echo "  http://${SERVER_IP}:${PORT}/"
echo
echo "Admin token:"
echo "  /var/lib/pgclocktoolbox/data/admin_token"
echo
echo "Service:"
echo "  systemctl status pgclocktoolbox --no-pager"
echo
echo "Logs:"
echo "  journalctl -u pgclocktoolbox -f"
echo
echo "=================================================="
