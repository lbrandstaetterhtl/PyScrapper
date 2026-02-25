Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Write-Host "== Start Server =="

$activateScript = "C:\Users\p50232\RiderProjects\PyScrapper\LocalServer\scripts\ActivateVirtualEnvironment.ps1"  

if (!(Test-Path $activateScript)) {
    throw "Activate script not found: $activateScript"
}

. $activateScript

$installScript = "C:\Users\p50232\RiderProjects\PyScrapper\LocalServer\scripts\InstallRequirements.ps1"

if (!(Test-Path $activateScript)) {
    throw "Install script not found: $installScript"
}

. $installScript

Write-Host "Starting server..."
python -m uvicorn LocalServer.server:app --host 127.0.0.1 --port 8765