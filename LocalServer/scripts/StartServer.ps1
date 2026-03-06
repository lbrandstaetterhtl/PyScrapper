param(
[string]$HostAddr = "127.0.0.1",
[int]$Port = 8765,
[switch]$NoVenv
)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force

$ErrorActionPreference = "Stop"

# Pfad-Setup für Logging
$ServerRoot = Split-Path -Parent $PSScriptRoot
$AllRoot = Split-Path -Parent $ServerRoot
$LogDir = Join-Path $ServerRoot "logs"
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

# In Script-Ordner wechseln (damit server.py sicher gefunden wird)
Set-Location -Path $AllRoot

if (-not $NoVenv) {
  $venvDir = Join-Path $PSScriptRoot ".venv"
  $pythonExe = Join-Path $venvDir "Scripts\python.exe"

  if (-not (Test-Path $pythonExe)) {
    Write-Log "No venv found. Creating .venv..."
    python -m venv $venvDir
  }
  . (Join-Path $venvDir "Scripts\Activate.ps1")
  
  $ffCmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
  if (-not $ffCmd) {
    Write-Log "ffmpeg not found. Running InstallFFMPEG.ps1..."
    $installScript = Join-Path $PSScriptRoot "InstallFFMPEG.ps1"
    if (-not (Test-Path $installScript)) { throw "Missing script: $installScript" }

    # -PersistUserPath optional: nimmt dir das PATH-Thema in neuen Terminals ab
    . $installScript -PersistUserPath 2>&1 | Out-File -Append -FilePath $LogFile -Encoding utf8
  } else {
    Write-Log "ffmpeg already available: $($ffCmd.Source)"
  }

  # Optional: requirements installieren, wenn vorhanden
  . (Join-Path $PSScriptRoot "InstallRequirements.ps1") 2>&1 | Out-File -Append -FilePath $LogFile -Encoding utf8
} else {
  Write-Log "NoVenv enabled: using system python."
}

Write-Log "Starting uvicorn: server:app on $HostAddr`:$Port"
Start-Process -FilePath "python" -ArgumentList "-m uvicorn LocalServer.server:app --host $HostAddr --port $Port" -NoNewWindow -Wait