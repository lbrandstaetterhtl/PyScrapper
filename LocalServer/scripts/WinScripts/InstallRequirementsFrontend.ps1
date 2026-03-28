param(
    [switch]$SkipDotnetInstall,
    [switch]$SkipSqliteInstall,
    [switch]$SkipAvaloniaTemplates,
    [switch]$NoRestore,
    [string]$DotnetChannel = '9.0'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Optional shared helpers
$commonPath = Join-Path $PSScriptRoot 'Common.ps1'
if (Test-Path $commonPath) {
    . $commonPath
    if (Get-Command Initialize-Log -ErrorAction SilentlyContinue) {
        Initialize-Log -Name 'InstallRequirementsFrontend.log' -Prefix 'InstallRequirementsFrontend'
    }
}

if (-not (Get-Command Write-Log -ErrorAction SilentlyContinue)) {
    $localServer = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    $logDir = Join-Path $localServer 'logs'
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    $script:LogFile = Join-Path $logDir 'InstallRequirementsFrontend.log'

    function Write-Log {
        param([Parameter(Mandatory)][string]$Message)
        $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        $line = "[$ts] [InstallRequirementsFrontend] $Message"
        Add-Content -Path $script:LogFile -Value $line -Encoding utf8
        Write-Host $line
    }
}

function Refresh-SessionPath {
    $machinePath = [System.Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath = [System.Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machinePath;$userPath"
}

function Get-ProjectContext {
    if (Get-Command Get-ProjectPaths -ErrorAction SilentlyContinue) {
        return Get-ProjectPaths
    }

    $scriptsRoot = Split-Path -Parent $PSScriptRoot
    $localServer = Split-Path -Parent $scriptsRoot
    $repoRoot = Split-Path -Parent $localServer

    return [pscustomobject]@{
        ScriptsRoot = $scriptsRoot
        LocalServer = $localServer
        RepoRoot    = $repoRoot
        LogsDir     = Join-Path $localServer 'logs'
    }
}

function Test-CommandWorks {
    param(
        [Parameter(Mandatory)][string]$CommandPath,
        [string[]]$ArgumentList = @('--version')
    )

    try {
        & $CommandPath @ArgumentList *> $null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

function Get-UsableCommand {
    param(
        [Parameter(Mandatory)][string]$Name,
        [string[]]$ArgumentList = @('--version'),
        [string[]]$RejectPathPatterns = @()
    )

    $candidates = @(Get-Command $Name -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
    foreach ($candidate in $candidates) {
        if (-not $candidate) { continue }

        $reject = $false
        foreach ($pattern in $RejectPathPatterns) {
            if ($candidate -like $pattern) {
                $reject = $true
                break
            }
        }
        if ($reject) { continue }

        if (Test-CommandWorks -CommandPath $candidate -ArgumentList $ArgumentList) {
            return $candidate
        }
    }

    return $null
}

function Ensure-Winget {
    $winget = Get-UsableCommand -Name 'winget' -ArgumentList @('--version')
    if (-not $winget) {
        throw 'winget wurde nicht gefunden. Installiere App Installer / winget oder installiere die Abhaengigkeiten manuell.'
    }
    return $winget
}

function Ensure-Dotnet {
    param([string]$Channel = '9.0')

    $dotnet = Get-UsableCommand -Name 'dotnet' -ArgumentList @('--version')
    if ($dotnet) {
        $version = (& $dotnet --version | Out-String).Trim()
        Write-Log ".NET SDK detected: $version"
        return $dotnet
    }

    if ($SkipDotnetInstall) {
        throw '.NET SDK wurde nicht gefunden und -SkipDotnetInstall wurde gesetzt.'
    }

    $winget = Ensure-Winget
    Write-Log ".NET SDK not found. Installing via winget..."
    & $winget install --id Microsoft.DotNet.SDK.9 -e --accept-source-agreements --accept-package-agreements
    if ($LASTEXITCODE -ne 0) {
        throw ("winget konnte .NET SDK nicht installieren. ExitCode: {0}" -f $LASTEXITCODE)
    }

    Refresh-SessionPath
    $dotnet = Get-UsableCommand -Name 'dotnet' -ArgumentList @('--version')
    if (-not $dotnet) {
        throw '.NET SDK scheint installiert worden zu sein, ist aber in dieser Session nicht verfuegbar.'
    }

    $version = (& $dotnet --version | Out-String).Trim()
    Write-Log ".NET SDK installed: $version"
    return $dotnet
}

function Ensure-Sqlite {
    $sqlite = Get-UsableCommand -Name 'sqlite3' -ArgumentList @('--version')
    if ($sqlite) {
        $version = (& $sqlite --version | Out-String).Trim()
        Write-Log "SQLite detected: $version"
        return $sqlite
    }

    if ($SkipSqliteInstall) {
        throw 'sqlite3 wurde nicht gefunden und -SkipSqliteInstall wurde gesetzt.'
    }

    $winget = Ensure-Winget
    Write-Log 'SQLite not found. Installing via winget...'

    & $winget install --id SQLite.SQLite -e --accept-source-agreements --accept-package-agreements
    $wingetExit = $LASTEXITCODE

    Refresh-SessionPath
    $sqlite = Get-UsableCommand -Name 'sqlite3' -ArgumentList @('--version')

    if ($sqlite) {
        $version = (& $sqlite --version | Out-String).Trim()
        Write-Log "SQLite available after winget: $version"
        return $sqlite
    }

    if ($wingetExit -eq -1978335189) {
        throw "winget meldet 'No applicable update found' und sqlite3 ist weiterhin nicht verfuegbar."
    }

    if ($wingetExit -ne 0) {
        throw ("winget konnte SQLite nicht installieren. ExitCode: {0}" -f $wingetExit)
    }

    throw 'winget lief ohne harten Fehler, aber sqlite3 wurde danach nicht gefunden.'
}

function Ensure-AvaloniaTemplates {
    param([Parameter(Mandatory)][string]$Dotnet)

    if ($SkipAvaloniaTemplates) {
        Write-Log 'Skipping Avalonia templates check.'
        return
    }

    $templateList = (& $Dotnet new list 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0) {
        throw 'dotnet new list ist fehlgeschlagen.'
    }

    if ($templateList -match '(?i)avalonia') {
        Write-Log 'Avalonia templates already installed.'
        return
    }

    Write-Log 'Avalonia templates not found. Installing Avalonia.Templates...'
    & $Dotnet new install Avalonia.Templates
    if ($LASTEXITCODE -ne 0) {
        throw 'dotnet new install Avalonia.Templates ist fehlgeschlagen.'
    }

    Write-Log 'Avalonia templates installed.'
}

function Get-CsprojFiles {
    param([Parameter(Mandatory)][string]$RepoRoot)

    $files = Get-ChildItem -Path $RepoRoot -Recurse -Filter '*.csproj' -File |
            Where-Object { $_.FullName -notmatch '[\\/](bin|obj)[\\/]' }

    if (-not $files) {
        throw "Keine .csproj-Dateien unter '$RepoRoot' gefunden."
    }

    return @($files)
}

function Invoke-DotnetRestore {
    param(
        [Parameter(Mandatory)][string]$Dotnet,
        [Parameter(Mandatory)][System.IO.FileInfo[]]$ProjectFiles
    )

    $restored = 0
    foreach ($project in $ProjectFiles) {
        Write-Log "Restoring $($project.FullName)"
        & $Dotnet restore $project.FullName
        if ($LASTEXITCODE -ne 0) {
            throw ("dotnet restore failed for '{0}' with exit code {1}." -f $project.FullName, $LASTEXITCODE)
        }
        $restored++
    }

    Write-Log "dotnet restore finished for $restored project(s)."
}

$ctx = Get-ProjectContext
Write-Log '== Install Frontend Requirements =='
Write-Log "Repo root: $($ctx.RepoRoot)"

$dotnet = Ensure-Dotnet -Channel $DotnetChannel
Ensure-AvaloniaTemplates -Dotnet $dotnet
$sqlite = Ensure-Sqlite
$csprojFiles = Get-CsprojFiles -RepoRoot $ctx.RepoRoot
Write-Log ("Found {0} .csproj file(s)." -f $csprojFiles.Count)

if (-not $NoRestore) {
    Invoke-DotnetRestore -Dotnet $dotnet -ProjectFiles $csprojFiles
}
else {
    Write-Log 'Skipping dotnet restore.'
}

Write-Log 'Frontend requirements are ready.'
