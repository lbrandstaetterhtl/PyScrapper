Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Logging setup
$ServerRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $ServerRoot "logs"
if (-not (Test-Path $LogDir)) {
  New-Item -ItemType Directory -Path $LogDir | Out-Null
}
$LogFile = Join-Path $LogDir "InstallRequirements.log"

function Write-Log {
  param([string]$Message)
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $logEntry = "[$timestamp] $Message"
  Add-Content -Path $LogFile -Value $logEntry -Encoding utf8
  Write-Output $logEntry
}

Write-Log "== Install Requirements =="

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

Write-Log "----------------------------------"
Write-Log "Current Directory: $(Get-Location)"
Write-Log "Installing requirements..."
pip install -r .\LocalServer\requirements.txt 2>&1 | Out-File -Append -FilePath $LogFile -Encoding utf8

if ($LASTEXITCODE -ne 0) {
  Write-Log "Error installing requirements. Please check the log file for details."
  exit $LASTEXITCODE
}
else {
  Write-Log "Requirements installed successfully."
}