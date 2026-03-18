#!/usr/bin/env bash
# ============================================================
# start_server.sh
# Bash-Equivalent zu: StartServer.ps1
# Läuft auf: Arch Linux (bash >= 4)
#
# Verzeichnisstruktur:
#   PyScrapper/
#   └── LocalServer/
#       ├── logs/
#       ├── server.py
#       └── scripts/
#           ├── .venv
#           └── LinuxScripts/   ← dieses Script liegt hier
#
# Usage:
#   bash ./start_server.sh
#   bash ./start_server.sh --host 0.0.0.0 --port 9000
#   bash ./start_server.sh --no-venv
# ============================================================

set -euo pipefail

# --- Parameter parsen ---------------------------------------
# Entspricht: param([string]$HostAddr = "127.0.0.1", [int]$Port = 8765, [switch]$NoVenv)
HOST_ADDR="127.0.0.1"
PORT=8765
NO_VENV=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --host)    HOST_ADDR="$2"; shift 2 ;;
        --port)    PORT="$2";      shift 2 ;;
        --no-venv) NO_VENV=true;   shift   ;;
        *) shift ;;
    esac
done

# --- Verzeichnisse berechnen --------------------------------
SCRIPT_DIR="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")" && pwd)"
# SCRIPT_DIR  = .../PyScrapper/LocalServer/scripts/LinuxScripts

SCRIPTS_DIR="$(dirname "$SCRIPT_DIR")"
# SCRIPTS_DIR = .../PyScrapper/LocalServer/scripts

LOCAL_SERVER="$(dirname "$SCRIPTS_DIR")"
# LOCAL_SERVER = .../PyScrapper/LocalServer

REPO_ROOT="$(dirname "$LOCAL_SERVER")"
# REPO_ROOT    = .../PyScrapper

# --- Logging Setup ------------------------------------------
LOG_DIR="$LOCAL_SERVER/logs"

if [[ ! -d "$LOG_DIR" ]]; then
    mkdir -p "$LOG_DIR"
fi

LOG_FILE="$LOG_DIR/StartServer.log"

# Entspricht Write-Log mit Timestamp:
#   $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
#   $logEntry  = "[$timestamp] $Message"
write_log() {
    local message="$1"
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    local log_entry="[$timestamp] $message"
    echo "$log_entry" | tee -a "$LOG_FILE"
}

write_log "== Start Server =="

# --- In RepoRoot wechseln -----------------------------------
# Muss RepoRoot sein, nicht LocalServer — sonst findet Python
# "PythonModule" nicht, da es auf RepoRoot-Ebene liegt.
cd "$REPO_ROOT" || {
    write_log "FEHLER: Konnte nicht nach $REPO_ROOT wechseln."
    exit 1
}

# ─── Virtual Environment ────────────────────────────────────
# Entspricht dem venv-Block in StartServer.ps1
# .venv liegt unter scripts/
VENV_DIR="$SCRIPTS_DIR/.venv"
PYTHON_EXE="$VENV_DIR/bin/python"
ACTIVATE_SCRIPT="$VENV_DIR/bin/activate"

if [[ ! -f "$PYTHON_EXE" ]]; then
    write_log "No venv found. Creating .venv..."
    python -m venv "$VENV_DIR"
fi

# Entspricht: . $activateScript  (dot-source → gilt für aktuelle Shell)
# shellcheck source=/dev/null
if [[ -f "$ACTIVATE_SCRIPT" ]]; then
    write_log "Activating virtual environment..."
    source "$ACTIVATE_SCRIPT"
    write_log "Virtual environment activated"
else
    write_log "WARNING: activate script not found at $ACTIVATE_SCRIPT"
fi

# ─── ffmpeg ─────────────────────────────────────────────────
# Entspricht dem ffmpeg-Block in StartServer.ps1:
#   1) Im Projektverzeichnis suchen (rekursiv)
#   2) Global prüfen
#   3) Wenn nirgends: InstallFFMPEG aufrufen

# Entspricht: Get-ChildItem -Path $AllRoot -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
# Auf Linux: ffmpeg heißt einfach "ffmpeg" ohne .exe
FFMPEG_IN_PROJECT="$(find "$REPO_ROOT" -name "ffmpeg" -type f -perm /u+x 2>/dev/null | head -n 1 || true)"

if [[ -n "$FFMPEG_IN_PROJECT" ]]; then
    FFMPEG_BIN_DIR="$(dirname "$FFMPEG_IN_PROJECT")"
    write_log "ffmpeg found in project: $FFMPEG_IN_PROJECT"

    # Session-PATH
    # Entspricht: if ($env:Path -notmatch [regex]::Escape($ffmpegBinDir))
    if [[ ":$PATH:" != *":$FFMPEG_BIN_DIR:"* ]]; then
        export PATH="$FFMPEG_BIN_DIR:$PATH"
        write_log "Added ffmpeg project path to session PATH: $FFMPEG_BIN_DIR"
    else
        write_log "Session PATH already contains ffmpeg project path: $FFMPEG_BIN_DIR"
    fi

    # Persistent in ~/.bashrc
    # Entspricht: [Environment]::SetEnvironmentVariable("Path", ..., "User")
    if ! grep -qF "$FFMPEG_BIN_DIR" "$HOME/.bashrc" 2>/dev/null; then
        echo "" >> "$HOME/.bashrc"
        echo "# Added by start_server.sh (ffmpeg project path)" >> "$HOME/.bashrc"
        echo "export PATH=\"$FFMPEG_BIN_DIR:\$PATH\"" >> "$HOME/.bashrc"
        write_log "Added ffmpeg project path to ~/.bashrc (persistent): $FFMPEG_BIN_DIR"
    else
        write_log "~/.bashrc already contains ffmpeg project path: $FFMPEG_BIN_DIR"
    fi

else
    # Entspricht: $ffCmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
    FFMPEG_GLOBAL="$(command -v ffmpeg 2>/dev/null || true)"

    if [[ -z "$FFMPEG_GLOBAL" ]]; then
        # Entspricht: & $installScript -PersistUserPath
        write_log "ffmpeg not found (neither in project nor in PATH). Running install_ffmpeg.sh..."
        INSTALL_FFMPEG="$SCRIPT_DIR/install_ffmpeg.sh"
        if [[ ! -f "$INSTALL_FFMPEG" ]]; then
            write_log "FEHLER: install_ffmpeg.sh nicht gefunden: $INSTALL_FFMPEG"
            exit 1
        fi
        bash "$INSTALL_FFMPEG" --persist >> "$LOG_FILE" 2>&1
    else
        FFMPEG_BIN_DIR="$(dirname "$FFMPEG_GLOBAL")"
        write_log "ffmpeg not in project but available globally: $FFMPEG_GLOBAL"

        # Session-PATH
        if [[ ":$PATH:" != *":$FFMPEG_BIN_DIR:"* ]]; then
            export PATH="$FFMPEG_BIN_DIR:$PATH"
            write_log "Added global ffmpeg path to session PATH: $FFMPEG_BIN_DIR"
        fi

        # Persistent in ~/.bashrc
        if ! grep -qF "$FFMPEG_BIN_DIR" "$HOME/.bashrc" 2>/dev/null; then
            echo "" >> "$HOME/.bashrc"
            echo "# Added by start_server.sh (ffmpeg global path)" >> "$HOME/.bashrc"
            echo "export PATH=\"$FFMPEG_BIN_DIR:\$PATH\"" >> "$HOME/.bashrc"
            write_log "Added global ffmpeg path to ~/.bashrc (persistent): $FFMPEG_BIN_DIR"
        else
            write_log "~/.bashrc already contains global ffmpeg path: $FFMPEG_BIN_DIR"
        fi
    fi
fi

# ─── Backend Requirements ───────────────────────────────────
# Entspricht: & (Join-Path $PSScriptRoot "InstallRequirementsBackend.ps1")
INSTALL_BACKEND="$SCRIPT_DIR/install_backend_requirements.sh"
if [[ ! -f "$INSTALL_BACKEND" ]]; then
    write_log "FEHLER: install_backend_requirements.sh nicht gefunden: $INSTALL_BACKEND"
    exit 1
fi

write_log "Running install_backend_requirements.sh..."
bash "$INSTALL_BACKEND" >> "$LOG_FILE" 2>&1

# ─── uvicorn starten ────────────────────────────────────────
# Entspricht:
#   Start-Process -FilePath "python" -ArgumentList "-m uvicorn LocalServer.server:app --host ... --port ..."
write_log "Starting uvicorn: server:app on $HOST_ADDR:$PORT"
python -m uvicorn LocalServer.server:app --host "$HOST_ADDR" --port "$PORT"
