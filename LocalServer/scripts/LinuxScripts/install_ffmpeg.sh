#!/usr/bin/env bash
# ============================================================
# install_ffmpeg.sh
# Bash-Equivalent zu: FFMPEGInstallation.ps1
# Läuft auf: Arch Linux (bash >= 4)
#
# Verzeichnisstruktur:
#   PyScrapper/
#   └── LocalServer/
#       ├── logs/
#       └── scripts/
#           └── LinuxScripts/  ← dieses Script liegt hier
#
# Usage:
#   source ./install_ffmpeg.sh
#   source ./install_ffmpeg.sh --persist
# ============================================================

set -euo pipefail

# --- Optionalen Flag parsen ---------------------------------
PERSIST_USER_PATH=false
for arg in "$@"; do
    case "$arg" in
        --persist|-p)
            PERSIST_USER_PATH=true
            ;;
    esac
done

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

LOG_FILE="$LOG_DIR/FFMPEGInstallation.log"

write_log() {
    local message="$1"
    local log_entry="[InstallFFMPEG] $message"
    echo "$log_entry" | tee -a "$LOG_FILE"
}

# --- find_ffmpeg_exe ----------------------------------------
find_ffmpeg_exe() {
    local cmd
    cmd="$(command -v ffmpeg 2>/dev/null || true)"
    if [[ -n "$cmd" ]]; then
        echo "$cmd"
        return
    fi
    if [[ -x "/usr/bin/ffmpeg" ]]; then
        echo "/usr/bin/ffmpeg"
        return
    fi
    echo ""
}

# --- Hauptlogik ---------------------------------------------
write_log "Checking for ffmpeg..."

FFMPEG_EXE="$(find_ffmpeg_exe)"

if [[ -z "$FFMPEG_EXE" ]]; then
    write_log "ffmpeg not found. Installing via pacman..."
    sudo pacman -S ffmpeg --noconfirm 2>&1 | tee -a "$LOG_FILE"
    FFMPEG_EXE="$(find_ffmpeg_exe)"
fi

if [[ -z "$FFMPEG_EXE" ]]; then
    write_log "FEHLER: Installation ran, but ffmpeg still not found."
    exit 1
fi

FFMPEG_BIN="$(dirname "$FFMPEG_EXE")"

# --- Session-PATH -------------------------------------------
if [[ ":$PATH:" != *":$FFMPEG_BIN:"* ]]; then
    export PATH="$FFMPEG_BIN:$PATH"
    write_log "Added to Session PATH: $FFMPEG_BIN"
else
    write_log "Session PATH already contains: $FFMPEG_BIN"
fi

write_log "ffmpeg installed at: $FFMPEG_EXE"

write_log "Testing ffmpeg version..."
VERSION_LINE="$("$FFMPEG_EXE" -version 2>&1 | head -n 1)"
write_log "$VERSION_LINE"

# --- Optional: persistent in ~/.bashrc ----------------------
if [[ "$PERSIST_USER_PATH" == true ]]; then
    BASHRC="$HOME/.bashrc"
    if ! grep -qF "$FFMPEG_BIN" "$BASHRC" 2>/dev/null; then
        echo "" >> "$BASHRC"
        echo "# Added by install_ffmpeg.sh" >> "$BASHRC"
        echo "export PATH=\"$FFMPEG_BIN:\$PATH\"" >> "$BASHRC"
        write_log "Added to User PATH: $FFMPEG_BIN (will take effect in new terminals)"
    else
        write_log "User PATH already contains: $FFMPEG_BIN"
    fi
fi
