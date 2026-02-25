﻿Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Logging setup
$ServerRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $ServerRoot "logs"
if (-not (Test-Path $LogDir)) {
  New-Item -ItemType Directory -Path $LogDir | Out-Null
}
$LogFile = Join-Path $LogDir "ActivateVirtualEnvironment.log"

function Write-Log {
  param([string]$Message)
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $logEntry = "[$timestamp] $Message"
  Add-Content -Path $LogFile -Value $logEntry -Encoding utf8
  Write-Output $logEntry
}

Write-Log "== Activate Virtual Enviroment =="

$ServerRoot = Split-Path -Parent $PSScriptRoot
$AllRoot = Split-Path -Parent $ServerRoot
Set-Location -Path $AllRoot

if (!(Test-Path "\.venv")) {
  Write-Log "Creating virtual environment..."
  python -m venv "\.venv" 2>&1 | Out-File -Append -FilePath $LogFile -Encoding utf8
} else {
  Write-Log "Virtual environment already exists."
}

Write-Log "Activating virtual environment..."
& "\.venv\Scripts\Activate.ps1" 2>&1 | Out-File -Append -FilePath $LogFile -Encoding utf8

Write-Log "Virtual environment activated."