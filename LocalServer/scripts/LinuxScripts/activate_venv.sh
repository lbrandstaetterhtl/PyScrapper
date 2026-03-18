#!/usr/bin/env bash
# ============================================================
# activate_venv.sh
# Bash-Equivalent zu: VirtualEnvironmentActivation.ps1
# Läuft auf: Arch Linux (bash >= 4)
#
# Verzeichnisstruktur:
#   PyScrapper/
#   └── LocalServer/
#       ├── logs/
#       └── scripts/
#           ├── .venv          ← wird hier erstellt/aktiviert
#           └── LinuxScripts/  ← dieses Script liegt hier
#
# Usage:
#   source ./activate_venv.sh
# ============================================================

# --- Verzeichnisse berechnen --------------------------------
SCRIPT_DIR="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")" && pwd)"
# SCRIPT_DIR  = .../PyScrapper/LocalServer/scripts/LinuxScripts

SCRIPTS_DIR="$(dirname "$SCRIPT_DIR")"
# SCRIPTS_DIR = .../PyScrapper/LocalServer/scripts

LOCAL_SERVER="$(dirname "$SCRIPTS_DIR")"
# LOCAL_SERVER = .../PyScrapper/LocalServer

# --- Logging Setup ------------------------------------------
# logs/ liegt direkt unter LocalServer/
LOG_DIR="$LOCAL_SERVER/logs"

if [[ ! -d "$LOG_DIR" ]]; then
    mkdir -p "$LOG_DIR"
fi

LOG_FILE="$LOG_DIR/VirtualEnvironmentActivation.log"

write_log() {
    local message="$1"
    local log_entry="[VirtualEnvironmentActivation] $message"
    echo "$log_entry" | tee -a "$LOG_FILE"
}

# --- Hauptlogik ---------------------------------------------
write_log "== Activate Virtual Environment =="

# .venv liegt unter scripts/ (sichtbar im Projektbaum)
VENV_PATH="$SCRIPTS_DIR/.venv"

cd "$SCRIPTS_DIR" || {
    write_log "FEHLER: Konnte nicht nach $SCRIPTS_DIR wechseln."
    exit 1
}

if [[ ! -d "$VENV_PATH" ]]; then
    write_log "Creating virtual environment..."
    python -m venv "$VENV_PATH" >> "$LOG_FILE" 2>&1
else
    write_log "Virtual environment already exists."
fi

write_log "Activating virtual environment..."

# Entspricht: & "\.venv\Scripts\Activate.ps1"
# shellcheck source=/dev/null
source "$VENV_PATH/bin/activate" >> "$LOG_FILE" 2>&1

write_log "Virtual environment activated."
