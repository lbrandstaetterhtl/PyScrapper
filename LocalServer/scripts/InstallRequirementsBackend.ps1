Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Logging setup
$ServerRoot = Split-Path -Parent $PSScriptRoot
$AllRoot = Split-Path -Parent $ServerRoot
$LogDir = Join-Path $ServerRoot "logs"
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

$ServerRoot = Split-Path -Parent $PSScriptRoot
$AllRoot = Split-Path -Parent $ServerRoot
Set-Location -Path $AllRoot

Write-Log "Upgrading pip..."
python -m pip install --upgrade pip 2>&1 | Out-File -Append -FilePath $LogFile -Encoding utf8

if ($LASTEXITCODE -ne 0) {
  Write-Log "Error upgrading pip. Please check the log file for details."
  exit $LASTEXITCODE
}
else {
  Write-Log "Pip upgraded successfully."
}

Write-Log "Installing requirements..."
pip install -r .\LocalServer\requirements.txt 2>&1 | Out-File -Append -FilePath $LogFile -Encoding utf8

if ($LASTEXITCODE -ne 0) {
  Write-Log "Error installing requirements. Please check the log file for details."
  exit $LASTEXITCODE
}
else {
  Write-Log "Requirements installed successfully."
}