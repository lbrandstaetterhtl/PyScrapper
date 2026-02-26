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
  Write-Output $logEntry
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

  Write-Log "Activating venv..."
  . (Join-Path $venvDir "Scripts\Activate.ps1")
  Write-Log "Virtual environment activated: $pythonExe"

  # Optional: requirements installieren, wenn vorhanden
  $req = Join-Path $ServerRoot "requirements.txt"
  if (Test-Path $req) {
    Write-Log "Installing requirements..."
    python -m pip install --upgrade pip 2>&1 | Out-File -Append -FilePath $LogFile -Encoding utf8
    pip install -r $req 2>&1 | Out-File -Append -FilePath $LogFile -Encoding utf8
    Write-Log "Requirements installation completed."
  } else {
    Write-Log "No requirements.txt found. Skipping pip install."
  }
} else {
  Write-Log "NoVenv enabled: using system python."
}

Write-Log "Starting uvicorn: server:app on $HostAddr`:$Port"
Start-Process -FilePath "python" -ArgumentList "-m uvicorn LocalServer.server:app --host $HostAddr --port $Port" -NoNewWindow -Wait