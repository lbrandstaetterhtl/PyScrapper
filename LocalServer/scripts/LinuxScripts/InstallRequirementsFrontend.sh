#!/usr/bin/env bash
# ============================================================
# install_frontend_requirements.sh
# Bash-Equivalent zu: RequirementsFrontendInstallation.ps1
# Läuft auf: Arch Linux (bash >= 4)
#
# Verzeichnisstruktur:
#   PyScrapper/                    ← REPO_ROOT (.csproj-Suche)
#   └── LocalServer/
#       ├── logs/
#       └── scripts/
#           └── LinuxScripts/      ← dieses Script liegt hier
#
# Usage:
#   bash ./install_frontend_requirements.sh
# ============================================================

# --- Verzeichnisse berechnen --------------------------------
SCRIPT_DIR="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")" && pwd)"
SCRIPTS_DIR="$(dirname "$SCRIPT_DIR")"
LOCAL_SERVER="$(dirname "$SCRIPTS_DIR")"
REPO_ROOT="$(dirname "$LOCAL_SERVER")"

# --- Logging Setup ------------------------------------------
LOG_DIR="$LOCAL_SERVER/logs"

if [[ ! -d "$LOG_DIR" ]]; then
    mkdir -p "$LOG_DIR"
fi

LOG_FILE="$LOG_DIR/RequirementsFrontendInstallation.log"

write_log() {
    local message="$1"
    local log_entry="[RequirementsFrontendInstallation] $message"
    echo "$log_entry" | tee -a "$LOG_FILE"
}

write_log "== Install Frontend Requirements =="

# ─── dotnet PATH fix ─────────────────────────────────────────────
# Bevorzuge ~/.dotnet gegenüber /run/host (Flatpak-Sandbox liefert
# sonst .NET 10 das wegen zu alter glibc crasht)
if [[ -x "$HOME/.dotnet/dotnet" ]]; then
    export DOTNET_ROOT="$HOME/.dotnet"
    export PATH="$HOME/.dotnet:$HOME/.dotnet/tools:$PATH"
    write_log "Using ~/.dotnet/dotnet (DOTNET_ROOT=$DOTNET_ROOT)"
fi

# ─── dotnet funktionsfähig prüfen ────────────────────────────────
is_dotnet_functional() {
    local version_output
    version_output="$(dotnet --version 2>&1)"
    if echo "$version_output" | grep -qiE "Failed|Error|HRESULT|not found"; then
        return 1
    fi
    echo "$version_output"
    return 0
}

# ─── .NET SDK ────────────────────────────────────────────────────
write_log "Checking .NET SDK..."

if command -v dotnet &>/dev/null; then
    SDK_VERSION="$(is_dotnet_functional)"
    if [[ $? -eq 0 ]]; then
        write_log ".NET SDK $SDK_VERSION detected ✓"
    else
        write_log "dotnet found but not functional (likely wrong version or glibc mismatch)."
        write_log "Attempting installation of .NET 9 via dotnet-install.sh..."
        command -v dotnet > /dev/null && unset -f dotnet 2>/dev/null || true
        DOTNET_FUNCTIONAL=0
    fi
else
    DOTNET_FUNCTIONAL=0
fi

if [[ "${DOTNET_FUNCTIONAL:-1}" -eq 0 ]]; then
    write_log "Installing .NET SDK via pacman..."
    if sudo pacman -S dotnet-sdk-9.0 --noconfirm >> "$LOG_FILE" 2>&1; then
        write_log "pacman install succeeded."
    else
        write_log "WARNING: pacman install failed, trying dotnet-install.sh..."

        INSTALL_SCRIPT="/tmp/dotnet-install.sh"
        if curl -fsSL "https://dot.net/v1/dotnet-install.sh" -o "$INSTALL_SCRIPT"; then
            chmod +x "$INSTALL_SCRIPT"
            "$INSTALL_SCRIPT" --channel 9.0 2>&1 | while IFS= read -r line; do
                write_log "  $line"
            done

            if [[ -x "$HOME/.dotnet/dotnet" ]]; then
                export DOTNET_ROOT="$HOME/.dotnet"
                export PATH="$HOME/.dotnet:$HOME/.dotnet/tools:$PATH"
                write_log "Added $HOME/.dotnet to PATH"
            fi
        else
            write_log "ERROR: Failed to download dotnet-install.sh"
        fi
    fi

    SDK_VERSION="$(is_dotnet_functional 2>/dev/null)"
    if [[ $? -eq 0 ]]; then
        write_log ".NET SDK $SDK_VERSION installed ✓"
    else
        write_log "ERROR: .NET SDK could not be installed or is not functional."
        write_log "Please install manually: https://dot.net"
        exit 1
    fi
fi

# ─── VLC ─────────────────────────────────────────────────────────
write_log "Checking VLC / libvlc..."

VLC_OK=0
if pacman -Q vlc &>/dev/null; then
    VLC_VERSION="$(pacman -Q vlc 2>/dev/null | awk '{print $2}')"
    write_log "VLC $VLC_VERSION detected ✓"
    VLC_OK=1
fi

if [[ $VLC_OK -eq 0 ]]; then
    write_log "VLC not found — installing via pacman..."
    if sudo pacman -S vlc --noconfirm >> "$LOG_FILE" 2>&1; then
        VLC_VERSION="$(pacman -Q vlc 2>/dev/null | awk '{print $2}')"
        write_log "VLC $VLC_VERSION installed ✓"
        VLC_OK=1
    else
        write_log "ERROR: Failed to install VLC."
        exit 1
    fi
fi

# ldconfig aktualisieren damit libvlc.so gefunden wird
sudo ldconfig >> "$LOG_FILE" 2>&1
write_log "ldconfig updated ✓"

# ─── Avalonia Templates ──────────────────────────────────────────
write_log "Checking Avalonia templates..."

if dotnet new list 2>&1 | grep -qi "avalonia"; then
    write_log "Avalonia templates already installed ✓"
else
    write_log "Avalonia templates not found, installing Avalonia.Templates..."

    TEMPLATE_OUTPUT="$(dotnet new install Avalonia.Templates 2>&1)"
    TEMPLATE_EXIT=$?

    if [[ $TEMPLATE_EXIT -ne 0 ]]; then
        write_log "WARNING: Failed to install Avalonia.Templates: $TEMPLATE_OUTPUT"
    else
        write_log "Avalonia.Templates installed ✓"
    fi
fi

# ─── SQLite ──────────────────────────────────────────────────────
write_log "Checking SQLite..."

if command -v sqlite3 &>/dev/null; then
    SQLITE_VERSION="$(sqlite3 --version 2>&1 | awk '{print $1}')"
    write_log "SQLite $SQLITE_VERSION detected ✓"
else
    write_log "SQLite not found — installing via pacman..."
    if sudo pacman -S sqlite --noconfirm >> "$LOG_FILE" 2>&1; then
        SQLITE_VERSION="$(sqlite3 --version 2>&1 | awk '{print $1}')"
        write_log "SQLite $SQLITE_VERSION installed ✓"
    else
        write_log "ERROR: Failed to install SQLite."
        exit 1
    fi
fi

# ─── NuGet Packages aus .csproj ──────────────────────────────────
write_log "Repo root: $REPO_ROOT"

mapfile -t CSPROJ_FILES < <(
    find "$REPO_ROOT" -name "*.csproj" \
        -not -path "*/bin/*" \
        -not -path "*/obj/*"
)

if [[ ${#CSPROJ_FILES[@]} -eq 0 ]]; then
    write_log "ERROR: No .csproj files found under $REPO_ROOT"
    exit 1
fi

# --- XML parsen mit Python ----------------------------------
parse_package_references() {
    local csproj_file="$1"
    python3 - "$csproj_file" <<'PYEOF'
import sys
import xml.etree.ElementTree as ET

csproj = sys.argv[1]
try:
    tree = ET.parse(csproj)
    root = tree.getroot()
    for pkg in root.iter():
        if pkg.tag.endswith("PackageReference"):
            name    = pkg.get("Include") or pkg.get("include") or ""
            version = pkg.get("Version") or pkg.get("version") or ""
            if name and version:
                print(f"{name}\t{version}\t{csproj}")
except Exception as e:
    print(f"PARSE_ERROR\t{e}\t{csproj}", file=sys.stderr)
PYEOF
}

declare -A SEEN_PACKAGES
declare -a PACKAGE_NAMES
declare -a PACKAGE_VERSIONS
declare -a PACKAGE_CSPROJPATHS

for CSPROJ in "${CSPROJ_FILES[@]}"; do
    write_log "Reading $CSPROJ"

    while IFS=$'\t' read -r PKG_NAME PKG_VERSION PKG_CSPROJ; do
        DEDUP_KEY="${PKG_NAME}	${PKG_VERSION}"
        if [[ -z "${SEEN_PACKAGES[$DEDUP_KEY]+_}" ]]; then
            SEEN_PACKAGES[$DEDUP_KEY]=1
            PACKAGE_NAMES+=("$PKG_NAME")
            PACKAGE_VERSIONS+=("$PKG_VERSION")
            PACKAGE_CSPROJPATHS+=("$PKG_CSPROJ")
        fi
    done < <(parse_package_references "$CSPROJ")
done

TOTAL_PACKAGES=${#PACKAGE_NAMES[@]}
write_log "Found $TOTAL_PACKAGES required package(s)"

# --- NuGet Cache Pfad ermitteln -----------------------------
NUGET_CACHE=""
RAW_OUTPUT="$(dotnet nuget locals global-packages --list 2>&1)"
CACHE_LINE="$(echo "$RAW_OUTPUT" | grep 'global-packages' | head -n 1)"
if [[ -n "$CACHE_LINE" ]]; then
    NUGET_CACHE="$(echo "$CACHE_LINE" | sed 's/.*global-packages:[[:space:]]*//' | tr -d '[:space:]')"
fi

if [[ -z "$NUGET_CACHE" ]] || [[ ! -d "$NUGET_CACHE" ]]; then
    NUGET_CACHE="$HOME/.nuget/packages"
fi

write_log "NuGet cache: $NUGET_CACHE"

# --- Pakete prüfen und installieren -------------------------
ALREADY_INSTALLED=0
NEWLY_INSTALLED=0
FAILED=0

for i in "${!PACKAGE_NAMES[@]}"; do
    PKG_NAME="${PACKAGE_NAMES[$i]}"
    PKG_VERSION="${PACKAGE_VERSIONS[$i]}"
    PKG_CSPROJ="${PACKAGE_CSPROJPATHS[$i]}"

    PKG_DIR="$NUGET_CACHE/${PKG_NAME,,}/$PKG_VERSION"

    if [[ -d "$PKG_DIR" ]]; then
        write_log "$PKG_NAME $PKG_VERSION — already installed ✓"
        (( ALREADY_INSTALLED++ )) || true
    else
        write_log "$PKG_NAME $PKG_VERSION — not cached, installing..."

        ADD_OUTPUT="$(dotnet add "$PKG_CSPROJ" package "$PKG_NAME" --version "$PKG_VERSION" 2>&1)"
        ADD_EXIT=$?

        if [[ $ADD_EXIT -ne 0 ]]; then
            write_log "ERROR installing $PKG_NAME $PKG_VERSION: $ADD_OUTPUT"
            (( FAILED++ )) || true
        else
            write_log "$PKG_NAME $PKG_VERSION — newly installed ✓"
            (( NEWLY_INSTALLED++ )) || true
        fi
    fi
done

# --- dotnet restore -----------------------------------------
write_log "Running dotnet restore..."

for CSPROJ in "${CSPROJ_FILES[@]}"; do
    CSPROJ_NAME="$(basename "$CSPROJ")"
    RESTORE_OUTPUT="$(dotnet restore "$CSPROJ" 2>&1)"
    RESTORE_EXIT=$?

    if [[ $RESTORE_EXIT -ne 0 ]]; then
        write_log "WARNING: dotnet restore failed for $CSPROJ_NAME: $RESTORE_OUTPUT"
    else
        write_log "dotnet restore succeeded for $CSPROJ_NAME"
    fi
done

# --- Summary ------------------------------------------------
write_log "========================================="
write_log "  Summary"
write_log "========================================="
write_log "  Total required:      $TOTAL_PACKAGES"
write_log "  Already installed:   $ALREADY_INSTALLED"
write_log "  Newly installed:     $NEWLY_INSTALLED"
if [[ $FAILED -gt 0 ]]; then
    write_log "  Failed:              $FAILED"
fi
write_log "========================================="
write_log "== Done =="
