Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Common.ps1"
Initialize-Log -Name 'RequirementsBackendInstallation.log' -Prefix 'InstallRequirementsBackend'

$paths = Get-ProjectPaths
$python = Ensure-Venv
$requirementsFile = Join-Path $paths.LocalServer 'requirements.txt'

if (-not (Test-Path -LiteralPath $requirementsFile)) {
    throw "requirements.txt not found: $requirementsFile"
}

Push-Location $paths.LocalServer
try {
    Write-Log 'Upgrading pip...'
    Invoke-LoggedCommand -FilePath $python -ArgumentList @('-m','pip','install','--upgrade','pip')

    Write-Log 'Installing backend requirements...'
    Invoke-LoggedCommand -FilePath $python -ArgumentList @('-m','pip','install','-r',$requirementsFile)

    Write-Log 'Installing Playwright browsers...'
    $env:NODE_NO_WARNINGS = '1'
    try {
        Invoke-LoggedCommand -FilePath $python -ArgumentList @('-m','playwright','install')
    } finally {
        Remove-Item Env:\NODE_NO_WARNINGS -ErrorAction SilentlyContinue
    }

    Write-Log 'Backend requirements installed successfully.'
}
finally {
    Pop-Location
}
