Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Common.ps1"
Initialize-Log -Name 'VirtualEnvironmentActivation.log' -Prefix 'ActivateVirtualEnvironment'

$paths = Get-ProjectPaths
$python = Ensure-Venv
Write-Log "Using python: $python"

if (-not (Test-Path -LiteralPath $paths.ActivatePs1)) {
    throw "Activate.ps1 not found: $($paths.ActivatePs1)"
}

Write-Log 'Activating virtual environment in current shell...'
. $paths.ActivatePs1
Write-Log 'Virtual environment activated.'
