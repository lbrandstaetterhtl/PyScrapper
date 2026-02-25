Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Write-Host "== Install Requirements =="

$ServerRoot = Split-Path -Parent $PSScriptRoot
$AllRoot = Split-Path -Parent $ServerRoot
Set-Location -Path $AllRoot

Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error upgrading pip. Please check the output above for details."
    exit $LASTEXITCODE
}
else {
    Write-Host "Pip upgraded successfully."
}

Write-Host "----------------------------------"
Write-Host "Installing requirements..."
pip install -r .\LocalServer\requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error installing requirements. Please check the output above for details."
    exit $LASTEXITCODE
}
else {
    Write-Host "Requirements installed successfully."
}