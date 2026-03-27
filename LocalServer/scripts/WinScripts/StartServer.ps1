param(
    [string]$HostAddr = '127.0.0.1',
    [int]$Port = 8765,
    [switch]$SkipBackendInstall,
    [switch]$SkipFrontendInstall,
    [switch]$SkipFfmpegInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Common.ps1"
Initialize-Log -Name 'StartServer.log' -Prefix 'StartServer'

$paths = Get-ProjectPaths
$python = Ensure-Venv

Push-Location $paths.RepoRoot
try {
    if (-not $SkipFrontendInstall) {
        & (Join-Path $PSScriptRoot 'InstallRequirementsFrontend.ps1')
    }

    if (-not $SkipFfmpegInstall) {
        & (Join-Path $PSScriptRoot 'InstallFFMPEG.ps1')
    }

    if (-not $SkipBackendInstall) {
        & (Join-Path $PSScriptRoot 'InstallRequirementsBackend.ps1')
    }

    Write-Log "Starting uvicorn on $HostAddr`:$Port"
    & $python -m uvicorn LocalServer.server:app --host $HostAddr --port $Port
    if ($LASTEXITCODE -ne 0) {
        throw "uvicorn exited with code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
