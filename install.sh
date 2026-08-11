#!/usr/bin/env bash
# PGClockToolBox installer - install, upgrade, status, uninstall
set -euo pipefail

APP_NAME="PGClockToolBox"
APP_ROOT="/opt/pgclocktoolbox"
DATA_ROOT="/var/lib/pgclocktoolbox"
VENV="$APP_ROOT/.venv"
REPO="${PGCLOCK_REPO:-https://github.com/Mrclocks/PGClockToolBox.git}"
SERVICE="pgclocktoolbox"
PORT="${PGCLOCK_PORT:-7100}"
TOKEN_FILE="$DATA_ROOT/data/admin_token"
GIT_REF="${PGCLOCK_GIT_REF:-main}"

ACTION="${1:-install}"

# colors (work for both TTY and curl | bash)
C_RESET=$'\033[0m'
C_BOLD=$'\033[1m'
C_DIM=$'\033[2m'
C_RED=$'\033[31m'
C_GREEN=$'\033[32m'
C_YELLOW=$'\033[33m'
C_BLUE=$'\033[34m'
C_CYAN=$'\033[36m'
C_ORANGE=$'\033[38;5;208m'

banner() {
  echo
  echo -e "${C_ORANGE}${C_BOLD}"
  cat <<'EOF'
  ____   ____  ____ _            _    _____           _ ____
 |  _ \ / ___|/ ___| | ___   ___| | _|_   _|__   ___ | | __ )  _____  __
 | |_) | |  _| |   | |/ _ \ / __| |/ / | |/ _ \ / _ \| |  _ \ / _ \ \/ /
 |  __/| |_| | |___| | (_) | (__|   <  | | (_) | (_) | | |_) | (_) >  <
 |_|    \____|\____|_|\___/ \___|_|\_\ |_|\___/ \___/|_|____/ \___/_/\_\
EOF
  echo -e "${C_RESET}"
  echo -e "  ${C_DIM}Modern toolbox for PasarGuard servers${C_RESET}"
  echo
}

hr() {
  echo -e "${C_DIM}──────────────────────────────────────────────────────────────${C_RESET}"
}

info()  { echo -e "  ${C_CYAN}•${C_RESET} $*"; }
ok()    { echo -e "  ${C_GREEN}✓${C_RESET} $*"; }
warn()  { echo -e "  ${C_YELLOW}!${C_RESET} $*"; }
fail()  { echo -e "  ${C_RED}✗${C_RESET} $*" >&2; }
die()   { fail "$*"; exit 1; }
step()  { echo; echo -e "${C_BOLD}${C_BLUE}▶${C_RESET} ${C_BOLD}$*${C_RESET}"; }

usage() {
  banner
  cat <<EOF
  ${C_BOLD}Usage${C_RESET}
    bash install.sh [command]

  ${C_BOLD}Commands${C_RESET}
    install       Install or upgrade (default)
    reinstall     Clear app files, keep data, then install again
    status        Show service, port and panel health
    uninstall     Remove the toolbox (keeps backups unless --purge)
    help          Show this help

  ${C_BOLD}Uninstall flags${C_RESET}
    --purge       Also delete ${DATA_ROOT} (config, logs, backups)
    --yes, -y     Do not ask for confirmation

  ${C_BOLD}One-liners${C_RESET}
    curl -fsSL https://raw.githubusercontent.com/Mrclocks/PGClockToolBox/main/install.sh | bash
    curl -fsSL https://raw.githubusercontent.com/Mrclocks/PGClockToolBox/main/install.sh | bash -s -- status
    curl -fsSL https://raw.githubusercontent.com/Mrclocks/PGClockToolBox/main/install.sh | bash -s -- uninstall
    curl -fsSL https://raw.githubusercontent.com/Mrclocks/PGClockToolBox/main/install.sh | bash -s -- uninstall --purge --yes

  ${C_BOLD}Environment${C_RESET}
    PGCLOCK_PORT=${PORT}          Web panel TCP port
    PGCLOCK_GIT_REF=${GIT_REF}    Git branch/tag to deploy
    PGCLOCK_REPO                  Git remote URL (advanced)

EOF
}

require_root() {
  [[ "$(id -u)" -eq 0 ]] || die "Run this script as root."
}

require_ubuntu() {
  [[ -f /etc/os-release ]] || die "Cannot detect OS (/etc/os-release missing)."
  # shellcheck disable=SC1091
  . /etc/os-release
  [[ "${ID:-}" == "ubuntu" ]] || die "PGClockToolBox requires Ubuntu 22.04+. Detected: ${ID:-unknown}"
  local major="${VERSION_ID%%.*}"
  (( major >= 22 )) || die "PGClockToolBox requires Ubuntu 22.04+. Detected: ${VERSION_ID}"
  ok "Ubuntu ${VERSION_ID} detected"
}

require_pasarguard() {
  if [[ ! -d /opt/pasarguard ]] || [[ ! -f /opt/pasarguard/.env ]]; then
    die "PasarGuard was not found at /opt/pasarguard (missing directory or .env)."
  fi
  ok "PasarGuard installation detected"
}

detect_ipv4() {
  local ip=""
  ip="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i = 1; i <= NF; i++) if ($i == "src") { print $(i + 1); exit }}' || true)"
  if [[ -z "$ip" ]]; then
    ip="$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^[0-9]+(\.[0-9]+){3}$' | head -n1 || true)"
  fi
  printf '%s' "${ip:-}"
}

detect_public_ipv4() {
  local ip="" url
  for url in \
    "https://api.ipify.org" \
    "https://ifconfig.me/ip" \
    "https://icanhazip.com"
  do
    ip="$(curl -4 -fsS --max-time 4 "$url" 2>/dev/null | tr -d '[:space:]' || true)"
    if [[ "$ip" =~ ^[0-9]+(\.[0-9]+){3}$ ]]; then
      printf '%s' "$ip"
      return 0
    fi
  done
  return 1
}

open_firewall() {
  if command -v ufw >/dev/null 2>&1; then
    if ufw status 2>/dev/null | grep -q '^Status: active'; then
      ufw allow "${PORT}/tcp" >/dev/null || true
      ok "UFW: allowed TCP ${PORT}"
      return 0
    fi
  fi
  warn "UFW is inactive or missing - open TCP ${PORT} in your provider firewall if needed"
}

close_firewall() {
  if command -v ufw >/dev/null 2>&1; then
    if ufw status 2>/dev/null | grep -q '^Status: active'; then
      ufw delete allow "${PORT}/tcp" >/dev/null 2>&1 || true
      ok "UFW: removed TCP ${PORT} rule (if present)"
    fi
  fi
}

service_is_active() {
  systemctl is-active --quiet "$SERVICE.service" 2>/dev/null
}

show_service_logs() {
  journalctl -u "$SERVICE" --no-pager -n 80 >&2 || true
}

wait_for_listen() {
  local _
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    if ss -lntp 2>/dev/null | grep -Eq ":${PORT}\\b"; then
      return 0
    fi
    sleep 0.5
  done
  return 1
}

verify_panel() {
  local body code
  body="$(mktemp)"
  code="$(curl -sS -o "$body" -w '%{http_code}' --max-time 8 "http://127.0.0.1:${PORT}/" || true)"
  if [[ "$code" != "200" ]]; then
    rm -f "$body"
    return 1
  fi
  if ! grep -q 'PGClockToolBox' "$body"; then
    rm -f "$body"
    return 2
  fi
  rm -f "$body"
  return 0
}

print_success() {
  local local_ip public_ip token
  local_ip="$(detect_ipv4)"
  public_ip="$(detect_public_ipv4 || true)"
  token=""
  [[ -f "$TOKEN_FILE" ]] && token="$(tr -d '[:space:]' < "$TOKEN_FILE" || true)"

  echo
  hr
  echo -e "  ${C_GREEN}${C_BOLD}${APP_NAME} is ready${C_RESET}"
  hr
  echo
  echo -e "  ${C_BOLD}Web Panel${C_RESET}"
  if [[ -n "$public_ip" ]]; then
    echo -e "    ${C_CYAN}http://${public_ip}:${PORT}/${C_RESET}"
  fi
  if [[ -n "$local_ip" && "$local_ip" != "$public_ip" ]]; then
    echo -e "    ${C_DIM}http://${local_ip}:${PORT}/${C_RESET}  (server IPv4)"
  fi
  if [[ -z "$public_ip" && -z "$local_ip" ]]; then
    echo -e "    ${C_CYAN}http://YOUR_SERVER_IP:${PORT}/${C_RESET}"
  fi
  echo
  echo -e "  ${C_BOLD}Admin Token${C_RESET}"
  if [[ -n "$token" ]]; then
    echo -e "    ${C_YELLOW}${token}${C_RESET}"
    echo -e "    ${C_DIM}saved at ${TOKEN_FILE}${C_RESET}"
  else
    echo -e "    ${TOKEN_FILE}"
  fi
  echo
  echo -e "  ${C_BOLD}Useful commands${C_RESET}"
  echo -e "    systemctl status ${SERVICE} --no-pager"
  echo -e "    journalctl -u ${SERVICE} -f"
  echo -e "    curl -fsSL https://raw.githubusercontent.com/Mrclocks/PGClockToolBox/main/install.sh | bash -s -- status"
  echo -e "    curl -fsSL https://raw.githubusercontent.com/Mrclocks/PGClockToolBox/main/install.sh | bash -s -- uninstall"
  echo
  echo -e "  ${C_DIM}If the panel does not load remotely, allow TCP ${PORT} in your cloud/provider firewall.${C_RESET}"
  echo
  hr
  echo
}

cmd_install() {
  require_root
  banner
  echo -e "  ${C_BOLD}Installing / upgrading ${APP_NAME}${C_RESET}"
  echo -e "  ${C_DIM}Port ${PORT} · ref ${GIT_REF}${C_RESET}"
  hr

  step "Checking system"
  require_ubuntu
  require_pasarguard

  step "Installing packages"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq \
    python3 python3-venv python3-pip git curl ca-certificates \
    unzip procps iproute2 sqlite3 wireguard-tools >/dev/null
  ok "System packages ready"

  step "Fetching source"
  if [[ -d "$APP_ROOT/.git" ]]; then
    git -C "$APP_ROOT" fetch --all --prune
    git -C "$APP_ROOT" checkout "$GIT_REF"
    if ! git -C "$APP_ROOT" pull --ff-only "origin" "$GIT_REF"; then
      git -C "$APP_ROOT" reset --hard "origin/${GIT_REF}"
    fi
    ok "Updated existing checkout at ${APP_ROOT}"
  else
    rm -rf "$APP_ROOT"
    git clone --depth 1 --branch "$GIT_REF" "$REPO" "$APP_ROOT"
    ok "Cloned repository to ${APP_ROOT}"
  fi

  step "Python environment"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --upgrade pip -q
  "$VENV/bin/pip" install -r "$APP_ROOT/backend/requirements.txt" -q
  ok "Virtualenv and dependencies installed"

  step "Data directories & admin token"
  install -d -m 0700 "$DATA_ROOT"/{data,backups,logs}
  PYTHONPATH="$APP_ROOT/backend" "$VENV/bin/python" -c 'from app.services.auth import ensure_token; ensure_token()'
  ok "Token ready at ${TOKEN_FILE}"

  step "Systemd service"
  # Keep unit port in sync with PGCLOCK_PORT.
  sed "s/--port [0-9][0-9]*/--port ${PORT}/" \
    "$APP_ROOT/systemd/pgclocktoolbox.service" > "/etc/systemd/system/${SERVICE}.service"
  systemctl daemon-reload
  systemctl enable "$SERVICE.service" >/dev/null
  # Always restart so upgrades load new code (enable --now alone will not).
  systemctl restart "$SERVICE.service"
  ok "Service ${SERVICE} enabled and restarted"

  step "Firewall"
  open_firewall

  step "Health checks"
  sleep 1
  if ! service_is_active; then
    fail "Service failed to stay active"
    show_service_logs
    exit 1
  fi
  ok "Service is active"

  if ! wait_for_listen; then
    fail "Nothing is listening on TCP ${PORT}"
    show_service_logs
    exit 1
  fi
  ok "Listening on TCP ${PORT}"

  local vc=0
  set +e
  verify_panel
  vc=$?
  set -e
  if [[ $vc -eq 0 ]]; then
    ok "Web panel responded with dashboard HTML"
  elif [[ $vc -eq 2 ]]; then
    fail "Port ${PORT} answered but dashboard HTML was missing"
    show_service_logs
    exit 1
  else
    fail "Web panel did not respond on http://127.0.0.1:${PORT}/"
    show_service_logs
    exit 1
  fi

  print_success
}

cmd_status() {
  require_root
  banner
  echo -e "  ${C_BOLD}Status${C_RESET}"
  hr
  echo

  if systemctl cat "$SERVICE.service" >/dev/null 2>&1; then
    if service_is_active; then
      ok "Service: active"
    else
      fail "Service: inactive"
    fi
    systemctl status "$SERVICE.service" --no-pager -l | sed 's/^/    /' || true
  else
    warn "Service unit not installed"
  fi

  echo
  if ss -lntp 2>/dev/null | grep -Eq ":${PORT}\\b"; then
    ok "Port ${PORT}: listening"
    ss -lntp 2>/dev/null | grep -E ":${PORT}\\b" | sed 's/^/    /' || true
  else
    fail "Port ${PORT}: not listening"
  fi

  echo
  local vc=0
  set +e
  verify_panel
  vc=$?
  set -e
  if [[ $vc -eq 0 ]]; then
    ok "Local panel check: OK"
  else
    fail "Local panel check: failed"
  fi

  echo
  local local_ip public_ip
  local_ip="$(detect_ipv4)"
  public_ip="$(detect_public_ipv4 || true)"
  [[ -n "$public_ip" ]] && info "Public URL:  http://${public_ip}:${PORT}/"
  [[ -n "$local_ip" ]] && info "Server URL:  http://${local_ip}:${PORT}/"
  [[ -f "$TOKEN_FILE" ]] && info "Admin token: ${TOKEN_FILE}"
  echo
}

confirm_uninstall() {
  local purge="$1"
  local assume_yes="$2"
  if [[ "$assume_yes" == "1" ]]; then
    return 0
  fi
  echo
  warn "This will remove ${APP_NAME} from this server."
  warn "PasarGuard itself will NOT be touched."
  if [[ "$purge" == "1" ]]; then
    warn "Purge mode: ${DATA_ROOT} (config, logs, backups) will be deleted."
  else
    info "Data kept at ${DATA_ROOT} (use --purge to delete it)."
  fi
  echo
  # Non-interactive pipes cannot confirm — require --yes.
  if [[ ! -t 0 ]]; then
    die "Non-interactive uninstall requires --yes (and optionally --purge)."
  fi
  read -r -p "  Type 'yes' to continue: " answer
  [[ "$answer" == "yes" ]] || die "Uninstall cancelled."
}

cmd_uninstall() {
  require_root
  local purge=0 assume_yes=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --purge) purge=1 ;;
      --yes|-y) assume_yes=1 ;;
      *) die "Unknown uninstall option: $1" ;;
    esac
    shift
  done

  banner
  echo -e "  ${C_BOLD}Uninstall ${APP_NAME}${C_RESET}"
  hr
  confirm_uninstall "$purge" "$assume_yes"

  step "Stopping service"
  if systemctl cat "$SERVICE.service" >/dev/null 2>&1; then
    systemctl disable --now "$SERVICE.service" >/dev/null 2>&1 || true
    ok "Service stopped and disabled"
  else
    info "Service was not installed"
  fi

  systemctl disable --now pgclocktoolbox-backup.timer >/dev/null 2>&1 || true
  systemctl disable --now pgclocktoolbox-backup.service >/dev/null 2>&1 || true

  step "Removing unit files"
  rm -f "/etc/systemd/system/${SERVICE}.service"
  rm -f /etc/systemd/system/pgclocktoolbox-backup.service
  rm -f /etc/systemd/system/pgclocktoolbox-backup.timer
  systemctl daemon-reload
  ok "Systemd units removed"

  step "Removing application files"
  rm -rf "$APP_ROOT"
  ok "Removed ${APP_ROOT}"

  if [[ "$purge" == "1" ]]; then
    step "Purging data"
    rm -rf "$DATA_ROOT"
    ok "Removed ${DATA_ROOT}"
  else
    info "Kept data directory ${DATA_ROOT}"
  fi

  step "Firewall"
  close_firewall

  echo
  hr
  echo -e "  ${C_GREEN}${C_BOLD}${APP_NAME} has been removed${C_RESET}"
  hr
  echo
}

cmd_reinstall() {
  require_root
  banner
  echo -e "  ${C_BOLD}Reinstall ${APP_NAME}${C_RESET}"
  hr
  info "Clearing application files (data preserved), then installing fresh"

  systemctl disable --now "$SERVICE.service" >/dev/null 2>&1 || true
  systemctl disable --now pgclocktoolbox-backup.timer >/dev/null 2>&1 || true
  systemctl disable --now pgclocktoolbox-backup.service >/dev/null 2>&1 || true
  rm -f "/etc/systemd/system/${SERVICE}.service"
  rm -f /etc/systemd/system/pgclocktoolbox-backup.service
  rm -f /etc/systemd/system/pgclocktoolbox-backup.timer
  systemctl daemon-reload || true
  rm -rf "$APP_ROOT"
  ok "Application files cleared (data preserved)"

  cmd_install
}

case "$ACTION" in
  install)
    cmd_install
    ;;
  reinstall)
    cmd_reinstall
    ;;
  status)
    cmd_status
    ;;
  uninstall|remove)
    shift || true
    cmd_uninstall "$@"
    ;;
  help|-h|--help)
    usage
    ;;
  *)
    usage
    die "Unknown command: $ACTION"
    ;;
esac
