Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Write-Host "== Activate Virtual Enviroment =="

if (!(Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
} else {
    Write-Host "Virtual environment already exists."
}

Write-Host "Activating virtual environment..."
. .\.venv\Scripts\Activate.ps1

Write-Host "Virtual environment activated."