param(
    [string]$HostAddr = "127.0.0.1",
    [int]$Port = 8765,
    [switch]$NoVenv
)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force

$ErrorActionPreference = "Stop"

# --- Verzeichnisse berechnen --------------------------------
# $PSScriptRoot = ...\PyScrapper\LocalServer\scripts\WinScripts
$ScriptsDir  = Split-Path -Parent $PSScriptRoot
# $ScriptsDir  = ...\PyScrapper\LocalServer\scripts
$LocalServer = Split-Path -Parent $ScriptsDir
# $LocalServer = ...\PyScrapper\LocalServer
$RepoRoot    = Split-Path -Parent $LocalServer
# $RepoRoot    = ...\PyScrapper

# --- Logging Setup ------------------------------------------
$LogDir = Join-Path $LocalServer "logs"
if (-not (Test-Path $LogDir)) {
  New-Item -ItemType Directory -Path $LogDir | Out-Null
}
$LogFile = Join-Path $LogDir "StartServer.log"

function Write-Log {
  param([string]$Message)
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $logEntry = "[$timestamp] $Message"
  Add-Content -Path $LogFile -Value $logEntry -Encoding utf8
  Write-Host $logEntry
}

Write-Log "== Start Server =="

# In LocalServer wechseln (damit server.py sicher gefunden wird)
Set-Location -Path $LocalServer

# ─── Virtual Environment ────────────────────────────────────
# .venv liegt unter scripts\
$venvDir       = Join-Path $ScriptsDir ".venv"
$pythonExe     = Join-Path $venvDir "Scripts\python.exe"
$activateScript = Join-Path $venvDir "Scripts\Activate.ps1"

if (-not (Test-Path $pythonExe)) {
  Write-Log "No venv found. Creating .venv..."
  python -m venv $venvDir
}

if (Test-Path $activateScript) {
  Write-Log "Activating virtual environment..."
  . $activateScript
  Write-Log "Virtual environment activated"
} else {
  Write-Log "WARNING: Activate.ps1 not found at $activateScript"
}

# ─── ffmpeg ─────────────────────────────────────────────────
$ffmpegInProject = Get-ChildItem -Path $RepoRoot -Recurse -Filter "ffmpeg.exe" -ErrorAction SilentlyContinue |
                   Select-Object -First 1

if ($ffmpegInProject) {
  $ffmpegBinDir = Split-Path $ffmpegInProject.FullName -Parent
  Write-Log "ffmpeg found in project: $($ffmpegInProject.FullName)"

  if ($env:Path -notmatch [regex]::Escape($ffmpegBinDir)) {
    $env:Path = "$ffmpegBinDir;$env:Path"
    Write-Log "Added ffmpeg project path to session PATH: $ffmpegBinDir"
  } else {
    Write-Log "Session PATH already contains ffmpeg project path: $ffmpegBinDir"
  }

  $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
  if ($userPath -notmatch [regex]::Escape($ffmpegBinDir)) {
    [Environment]::SetEnvironmentVariable("Path", ($userPath + ";" + $ffmpegBinDir), "User")
    Write-Log "Added ffmpeg project path to User PATH (persistent): $ffmpegBinDir"
  } else {
    Write-Log "User PATH already contains ffmpeg project path: $ffmpegBinDir"
  }
} else {
  $ffCmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
  if (-not $ffCmd) {
    Write-Log "ffmpeg not found (neither in project nor in PATH). Running InstallFFMPEG.ps1..."
    $installScript = Join-Path $PSScriptRoot "InstallFFMPEG.ps1"
    if (-not (Test-Path $installScript)) { throw "Missing script: $installScript" }
    & $installScript -PersistUserPath 2>&1 | Out-File -Append -FilePath $LogFile -Encoding utf8
  } else {
    $ffmpegBinDir = Split-Path $ffCmd.Source -Parent
    Write-Log "ffmpeg not in project but available globally: $($ffCmd.Source)"

    if ($env:Path -notmatch [regex]::Escape($ffmpegBinDir)) {
      $env:Path = "$ffmpegBinDir;$env:Path"
      Write-Log "Added global ffmpeg path to session PATH: $ffmpegBinDir"
    }

    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notmatch [regex]::Escape($ffmpegBinDir)) {
      [Environment]::SetEnvironmentVariable("Path", ($userPath + ";" + $ffmpegBinDir), "User")
      Write-Log "Added global ffmpeg path to User PATH (persistent): $ffmpegBinDir"
    } else {
      Write-Log "User PATH already contains global ffmpeg path: $ffmpegBinDir"
    }
  }
}

# ─── Backend Requirements ───────────────────────────────────
& (Join-Path $PSScriptRoot "InstallRequirementsBackend.ps1") 2>&1 | Out-File -Append -FilePath $LogFile -Encoding utf8

# ─── uvicorn starten ────────────────────────────────────────
Write-Log "Starting uvicorn: server:app on $HostAddr`:$Port"
Start-Process -FilePath "python" `
              -ArgumentList "-m uvicorn LocalServer.server:app --host $HostAddr --port $Port" `
              -NoNewWindow -Wait
