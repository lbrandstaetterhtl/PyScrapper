Write-Host "----------------------"
Write-Host "starting server...   |"
Write-Host "----------------------"

# Skript liegt in: LocalServer\scripts\
# ServerPath ist eine Ebene hoeher: LocalServer\
$ScriptDir  = $PSScriptRoot
$ServerPath = Split-Path -Parent $ScriptDir

# Python: venv im Server-Ordner bevorzugen, sonst PATH
$Python = Join-Path $ServerPath ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    $Python = (Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1).Source
}

if (-not $Python) {
    Write-Host "Python nicht gefunden - weder im venv noch im PATH." -ForegroundColor Red
    exit 1
}

Write-Host "Python:  $Python"
Write-Host "Server:  $ServerPath"

Set-Location $ServerPath
& $Python -m uvicorn server:app --host 127.0.0.1 --port 8765

Write-Host "-----------------------------"
Write-Host "server stopped.             |"
Write-Host "-----------------------------"