#!/usr/bin/env bash
# ============================================================
# install_backend_requirements.sh
# Bash-Equivalent zu: RequirementsBackendInstallation.ps1
# Läuft auf: Arch Linux (bash >= 4)
#
# Verzeichnisstruktur:
#   PyScrapper/
#   └── LocalServer/
#       ├── logs/
#       ├── requirements.txt   ← wird hier gesucht
#       └── scripts/
#           └── LinuxScripts/  ← dieses Script liegt hier
#
# Usage:
#   source ./install_backend_requirements.sh
# ============================================================

# --- Verzeichnisse berechnen --------------------------------
SCRIPT_DIR="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")" && pwd)"
# SCRIPT_DIR  = .../PyScrapper/LocalServer/scripts/LinuxScripts

SCRIPTS_DIR="$(dirname "$SCRIPT_DIR")"
# SCRIPTS_DIR = .../PyScrapper/LocalServer/scripts

LOCAL_SERVER="$(dirname "$SCRIPTS_DIR")"
# LOCAL_SERVER = .../PyScrapper/LocalServer

# --- Logging Setup ------------------------------------------
LOG_DIR="$LOCAL_SERVER/logs"

if [[ ! -d "$LOG_DIR" ]]; then
    mkdir -p "$LOG_DIR"
fi

LOG_FILE="$LOG_DIR/RequirementsBackendInstallation.log"

write_log() {
    local message="$1"
    local log_entry="[RequirementsBackendInstallation] $message"
    echo "$log_entry" | tee -a "$LOG_FILE"
}

# --- Hauptlogik ---------------------------------------------
write_log "== Install Backend Requirements =="

cd "$LOCAL_SERVER" || {
    write_log "FEHLER: Konnte nicht nach $LOCAL_SERVER wechseln."
    exit 1
}

# --- pip upgrade --------------------------------------------
write_log "Upgrading pip..."

python -m pip install --upgrade pip >> "$LOG_FILE" 2>&1
PIP_UPGRADE_EXIT=$?

if [[ $PIP_UPGRADE_EXIT -ne 0 ]]; then
    write_log "Error upgrading pip. Please check the log file for details."
    exit $PIP_UPGRADE_EXIT
else
    write_log "Pip upgraded successfully."
fi

# --- requirements.txt installieren -------------------------
# requirements.txt liegt direkt unter LocalServer/
REQUIREMENTS_FILE="$LOCAL_SERVER/requirements.txt"

write_log "Installing requirements..."

pip install -r "$REQUIREMENTS_FILE" >> "$LOG_FILE" 2>&1
PIP_INSTALL_EXIT=$?

if [[ $PIP_INSTALL_EXIT -ne 0 ]]; then
    write_log "Error installing requirements. Please check the log file for details."
    exit $PIP_INSTALL_EXIT
else
    # NODE_NO_WARNINGS nur für diesen einen Aufruf setzen
    write_log "Installing Playwright browsers..."

    NODE_NO_WARNINGS=1 playwright install >> "$LOG_FILE" 2>&1
    PLAYWRIGHT_EXIT=$?

    if [[ $PLAYWRIGHT_EXIT -ne 0 ]]; then
        write_log "Error running playwright install. Please check the log file for details."
        exit $PLAYWRIGHT_EXIT
    fi

    write_log "Requirements installed successfully."
fi
