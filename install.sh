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

# If UFW is installed and active, expose only the Toolbox web port.
if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q '^Status: active'; then
  ufw allow 6000/tcp >/dev/null
fi

sleep 2
if ! systemctl is-active --quiet pgclocktoolbox.service; then
  echo "PGClockToolBox failed to start." >&2
  journalctl -u pgclocktoolbox --no-pager -n 100 >&2 || true
  exit 1
fi

if ! ss -lntp 2>/dev/null | grep -Eq "LISTEN[[:space:]].*(0\.0\.0\.0:${PORT}|\[::\]:${PORT}|:::${PORT})"; then
  echo "PGClockToolBox service is active but nothing is listening on TCP ${PORT}." >&2
  journalctl -u pgclocktoolbox --no-pager -n 100 >&2 || true
  exit 1
fi

if ! curl -fsS --max-time 5 "http://127.0.0.1:${PORT}/" >/dev/null; then
  echo "PGClockToolBox is listening but the web panel did not respond on port ${PORT}." >&2
  journalctl -u pgclocktoolbox --no-pager -n 100 >&2 || true
  exit 1
fi

# Prefer the real IPv4 route address. hostname -I may return IPv6 first,
# which would produce an invalid browser URL without brackets.
SERVER_IP="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}')"
if [[ -z "$SERVER_IP" ]]; then
  SERVER_IP="$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^[0-9]+(\.[0-9]+){3}$' | head -n1 || true)"
fi
SERVER_IP="${SERVER_IP:-YOUR_SERVER_IPV4}"

FIREWALL_NOTE=""
if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q '^Status: active'; then
  FIREWALL_NOTE="UFW: TCP ${PORT} allowed"
else
  FIREWALL_NOTE="If your provider has a firewall/security group, allow TCP ${PORT}."
fi

echo
echo '=================================================='
echo ' PGClockToolBox installed successfully'
echo '=================================================='
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
echo "Network:"
echo "  ss -lntp | grep ':${PORT}'"
echo "  ${FIREWALL_NOTE}"
echo
echo '=================================================='
