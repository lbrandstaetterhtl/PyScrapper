Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Write-Host "== Start Server =="

$activateScript = Join-Path $PSScriptRoot "ActivateVirtualEnvironment.ps1"  

if (!(Test-Path $activateScript)) {
    throw "Activate script not found: $activateScript"
}

. $activateScript

$installScript = Join-Path $PSScriptRoot "InstallRequirements.ps1"

if (!(Test-Path $activateScript)) {
    throw "Install script not found: $activateScript"
}

. $installScript

Write-Host "Starting server..."
python -m uvicorn LocalServer.server:app --host 127.0.0.1 --port 8765