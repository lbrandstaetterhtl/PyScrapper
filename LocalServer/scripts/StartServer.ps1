param(
    [string]$HostAddr = "127.0.0.1",
    [int]$Port = 8765,
    [switch]$NoVenv
)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force

$ErrorActionPreference = "Stop"

Write-Host "== Start Server =="

# In Script-Ordner wechseln (damit server.py sicher gefunden wird)
$ServerRoot = Split-Path -Parent $PSScriptRoot
$AllRoot = Split-Path -Parent $ServerRoot
Set-Location -Path $AllRoot

if (-not $NoVenv) {
    $venvDir = Join-Path $PSScriptRoot ".venv"
    $pythonExe = Join-Path $venvDir "Scripts\python.exe"

    if (-not (Test-Path $pythonExe)) {
        Write-Host "No venv found. Creating .venv..."
        python -m venv $venvDir
    }

    Write-Host "Activating venv..."
    . (Join-Path $venvDir "Scripts\Activate.ps1")

    # Optional: requirements installieren, wenn vorhanden
    $req = Join-Path $PSScriptRoot "requirements.txt"
    if (Test-Path $req) {
        Write-Host "Installing requirements..."
        python -m pip install --upgrade pip
        pip install -r $req
    } else {
        Write-Host "No requirements.txt found. Skipping pip install."
    }
} else {
    Write-Host "NoVenv enabled: using system python."
}

Write-Host "Current Directory: $(Get-Location)"
Write-Host "Starting uvicorn: server:app on $HostAddr`:$Port"
python -m uvicorn LocalServer.server:app --host $HostAddr --port $Port