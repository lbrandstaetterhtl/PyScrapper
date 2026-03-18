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
$LogFile = Join-Path $LogDir "RequirementsBackendInstallation.log"

function Write-Log {
  param([string]$Message)
  $logEntry = "[RequirementsBackendInstallation] $Message"
  Add-Content -Path $LogFile -Value $logEntry -Encoding utf8
  Write-Host $logEntry
}

Write-Log "== Install Backend Requirements =="

# requirements.txt liegt direkt unter LocalServer\
Set-Location -Path $LocalServer

Write-Log "Upgrading pip..."
python -m pip install --upgrade pip 2>&1 | Out-File -Append -FilePath $LogFile -Encoding utf8
if ($LASTEXITCODE -ne 0) {
  Write-Log "Error upgrading pip. Please check the log file for details."
  exit $LASTEXITCODE
} else {
  Write-Log "Pip upgraded successfully."
}

Write-Log "Installing requirements..."
$RequirementsFile = Join-Path $LocalServer "requirements.txt"
pip install -r $RequirementsFile 2>&1 | Out-File -Append -FilePath $LogFile -Encoding utf8
if ($LASTEXITCODE -ne 0) {
  Write-Log "Error installing requirements. Please check the log file for details."
  exit $LASTEXITCODE
} else {
  $env:NODE_NO_WARNINGS = "1"
  playwright install 2>&1 | Out-File -Append -FilePath $LogFile -Encoding UTF8
  Remove-Item Env:\NODE_NO_WARNINGS
  Write-Log "Requirements installed successfully."
}
