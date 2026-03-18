Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# --- Verzeichnisse berechnen --------------------------------
# $PSScriptRoot = ...\PyScrapper\LocalServer\scripts\WinScripts
$ScriptsDir  = Split-Path -Parent $PSScriptRoot
# $ScriptsDir  = ...\PyScrapper\LocalServer\scripts
$LocalServer = Split-Path -Parent $ScriptsDir
# $LocalServer = ...\PyScrapper\LocalServer

# --- Logging Setup ------------------------------------------
$LogDir = Join-Path $LocalServer "logs"
if (-not (Test-Path $LogDir)) {
  New-Item -ItemType Directory -Path $LogDir | Out-Null
}
$LogFile = Join-Path $LogDir "VirtualEnvironmentActivation.log"

function Write-Log {
  param([string]$Message)
  $logEntry = "[VirtualEnvironmentActivation] $Message"
  Add-Content -Path $LogFile -Value $logEntry -Encoding utf8
  Write-Host $logEntry
}

Write-Log "== Activate Virtual Environment =="

# .venv liegt unter scripts\
$VenvPath = Join-Path $ScriptsDir ".venv"

Set-Location -Path $ScriptsDir

if (!(Test-Path $VenvPath)) {
  Write-Log "Creating virtual environment..."
  python -m venv $VenvPath 2>&1 | Out-File -Append -FilePath $LogFile -Encoding utf8
} else {
  Write-Log "Virtual environment already exists."
}

Write-Log "Activating virtual environment..."
& "$VenvPath\Scripts\Activate.ps1" 2>&1 | Out-File -Append -FilePath $LogFile -Encoding utf8
Write-Log "Virtual environment activated."
