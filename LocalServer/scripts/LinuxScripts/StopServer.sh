#!/usr/bin/env bash
# ============================================================
# stop_server.sh
# Bash-Equivalent zu: StopServer.ps1
# Läuft auf: Arch Linux (bash >= 4)
#
# Verzeichnisstruktur:
#   PyScrapper/
#   └── LocalServer/
#       ├── logs/
#       └── scripts/
#           └── LinuxScripts/   ← dieses Script liegt hier
#
# Usage:
#   bash ./stop_server.sh
#   bash ./stop_server.sh --host 0.0.0.0 --port 9000
# ============================================================

# Entspricht: $ErrorActionPreference = "SilentlyContinue"
# Kein set -e — Fehler werden geloggt aber ignoriert
set -uo pipefail

# --- Parameter parsen ---------------------------------------
# Entspricht: param([string]$HostAddr = "127.0.0.1", [int]$Port = 8765)
HOST_ADDR="127.0.0.1"
PORT=8765

while [[ $# -gt 0 ]]; do
    case "$1" in
        --host) HOST_ADDR="$2"; shift 2 ;;
        --port) PORT="$2";      shift 2 ;;
        *) shift ;;
    esac
done

# --- Verzeichnisse berechnen --------------------------------
SCRIPT_DIR="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")" && pwd)"
SCRIPTS_DIR="$(dirname "$SCRIPT_DIR")"
LOCAL_SERVER="$(dirname "$SCRIPTS_DIR")"

# --- Logging Setup ------------------------------------------
LOG_DIR="$LOCAL_SERVER/logs"

if [[ ! -d "$LOG_DIR" ]]; then
    mkdir -p "$LOG_DIR"
fi

LOG_FILE="$LOG_DIR/StopServer.log"

# Entspricht Write-Log mit Timestamp
write_log() {
    local message="$1"
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    local log_entry="[$timestamp] $message"
    echo "$log_entry" | tee -a "$LOG_FILE"
}

write_log "== Stop Server =="

BASE_URL="http://$HOST_ADDR:$PORT"

# ─── 1) Graceful Shutdown via API ───────────────────────────
# Entspricht dem try-Block:
#   Invoke-RestMethod GET /health -TimeoutSec 2
#   if ($health.ok -eq $true) → POST /command {"command":"quit"}
#   Start-Sleep -Milliseconds 800
#
# curl --fail gibt exit code != 0 wenn HTTP-Fehler → || true verhindert Script-Abbruch
HEALTH_RESPONSE="$(curl --silent --fail --max-time 2 "$BASE_URL/health" 2>/dev/null || true)"

if [[ -n "$HEALTH_RESPONSE" ]]; then
    # Entspricht: $health.ok -eq $true
    # Python/Flask gibt typischerweise {"ok": true} zurück — mit python3 parsen
    IS_OK="$(echo "$HEALTH_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('true' if data.get('ok') == True else 'false')
except:
    print('false')
")"

    if [[ "$IS_OK" == "true" ]]; then
        write_log "Server reachable. Sending quit command..."

        # Entspricht: Invoke-RestMethod POST /command -Body '{"command":"quit"}'
        curl --silent --fail --max-time 2 \
             --request POST \
             --header "Content-Type: application/json" \
             --data '{"command":"quit"}' \
             "$BASE_URL/command" > /dev/null 2>&1 || true

        # Entspricht: Start-Sleep -Milliseconds 800
        sleep 0.8
    fi
else
    write_log "Server not reachable via API (or already down). Falling back to port-kill..."
fi

# ─── 2) Fallback: Prozess auf dem Port killen ───────────────
# Entspricht:
#   $connection = Get-NetTCPConnection -LocalPort $Port
#   $pidNum = $connection.OwningProcess
#   Stop-Process -Id $pidNum -Force

# ss (socket statistics) ist das Linux-Äquivalent zu Get-NetTCPConnection
# -tlnp = TCP, listening, numeric, show PID
PID_ON_PORT="$(ss -tlnp "sport = :$PORT" 2>/dev/null \
    | awk 'NR>1 {match($0, /pid=([0-9]+)/, a); if (a[1]) print a[1]}' \
    | head -n 1 || true)"

if [[ -n "$PID_ON_PORT" ]]; then
    write_log "Killing process on port $PORT (PID $PID_ON_PORT)..."

    # Entspricht: Stop-Process -Id $pidNum -Force -ErrorAction SilentlyContinue
    kill -9 "$PID_ON_PORT" 2>/dev/null || true

    write_log "Process stopped."
else
    write_log "No process found listening on port $PORT."
fi
