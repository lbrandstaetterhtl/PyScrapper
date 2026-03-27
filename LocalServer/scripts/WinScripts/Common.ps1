Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-ProjectPaths {
    $scriptsDir = Split-Path -Parent $PSScriptRoot
    $localServer = Split-Path -Parent $scriptsDir
    $repoRoot = Split-Path -Parent $localServer

    [pscustomobject]@{
        ScriptsDir = $scriptsDir
        LocalServer = $localServer
        RepoRoot    = $repoRoot
        LogDir      = Join-Path $localServer 'logs'
        WinScripts  = $PSScriptRoot
        VenvDir     = Join-Path $scriptsDir '.venv'
        VenvPython  = Join-Path $scriptsDir '.venv\Scripts\python.exe'
        ActivatePs1 = Join-Path $scriptsDir '.venv\Scripts\Activate.ps1'
    }
}

function Initialize-Log {
    param(
        [Parameter(Mandatory)] [string]$Name,
        [Parameter(Mandatory)] [string]$Prefix
    )

    $paths = Get-ProjectPaths
    if (-not (Test-Path -LiteralPath $paths.LogDir)) {
        New-Item -ItemType Directory -Path $paths.LogDir -Force | Out-Null
    }

    $script:LogPrefix = $Prefix
    $script:LogFile = Join-Path $paths.LogDir $Name
}

function Write-Log {
    param([Parameter(Mandatory)][string]$Message)

    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $line = "[$timestamp] [$script:LogPrefix] $Message"
    Add-Content -Path $script:LogFile -Value $line -Encoding utf8
    Write-Host $line
}

function Invoke-LoggedCommand {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [string[]]$ArgumentList = @(),
        [string]$WorkingDirectory,
        [switch]$AllowFailure
    )

    $resolvedWorkingDirectory = if ($WorkingDirectory) { $WorkingDirectory } else { (Get-Location).Path }
    Write-Log ("RUN: {0} {1}" -f $FilePath, ($ArgumentList -join ' '))

    $output = & $FilePath @ArgumentList 2>&1
    if ($null -ne $output) {
        foreach ($line in @($output)) {
            Add-Content -Path $script:LogFile -Value $line -Encoding utf8
        }
    }

    if (-not $AllowFailure -and $LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${OSTEOCLASTIC}: $FilePath ($ArgumentList -join ' ')"
    }

    return $output
}

function Refresh-Path {
    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machinePath;$userPath"
}

function Test-CommandExists {
    param([Parameter(Mandatory)][string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-PythonCommand {
    $venvPython = (Get-ProjectPaths).VenvPython
    if (Test-Path -LiteralPath $venvPython) {
        return $venvPython
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { return $py.Source }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) { return $python.Source }

    return $null
}

function Ensure-Winget {
    if (-not (Test-CommandExists 'winget')) {
        throw 'winget not found. Install App Installer from Microsoft Store or install dependencies manually.'
    }
}

function Ensure-Python {
    param([string]$WingetId = 'Python.Python.3.12')

    $python = Get-PythonCommand
    if ($python) {
        Write-Log "Python found: $python"
        return $python
    }

    Ensure-Winget
    Write-Log "Python not found. Installing via winget ($WingetId)..."
    Invoke-LoggedCommand -FilePath 'winget' -ArgumentList @('install','-e','--id',$WingetId,'--accept-package-agreements','--accept-source-agreements')
    Refresh-Path

    $python = Get-PythonCommand
    if (-not $python) {
        throw 'Python installation finished but python/py is still not available in PATH.'
    }

    Write-Log "Python installed successfully: $python"
    return $python
}

function Ensure-Venv {
    $paths = Get-ProjectPaths
    $python = Ensure-Python

    if (-not (Test-Path -LiteralPath $paths.VenvPython)) {
        Write-Log "Creating virtual environment at $($paths.VenvDir)"
        if ((Split-Path -Leaf $python) -ieq 'py.exe') {
            Invoke-LoggedCommand -FilePath $python -ArgumentList @('-3.12','-m','venv',$paths.VenvDir)
        } else {
            Invoke-LoggedCommand -FilePath $python -ArgumentList @('-m','venv',$paths.VenvDir)
        }
    } else {
        Write-Log 'Virtual environment already exists.'
    }

    if (-not (Test-Path -LiteralPath $paths.VenvPython)) {
        throw "Virtual environment python missing: $($paths.VenvPython)"
    }

    return $paths.VenvPython
}

function Ensure-CommandInPath {
    param(
        [Parameter(Mandatory)][string]$Directory,
        [switch]$PersistUserPath
    )

    if ($env:Path -notmatch [regex]::Escape($Directory)) {
        $env:Path = "$Directory;$env:Path"
        Write-Log "Added to session PATH: $Directory"
    }

    if ($PersistUserPath) {
        $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
        if ([string]::IsNullOrWhiteSpace($userPath)) {
            $newUserPath = $Directory
        } elseif ($userPath -notmatch [regex]::Escape($Directory)) {
            $newUserPath = "$userPath;$Directory"
        } else {
            $newUserPath = $null
        }

        if ($newUserPath) {
            [Environment]::SetEnvironmentVariable('Path', $newUserPath, 'User')
            Write-Log "Added to user PATH: $Directory"
        }
    }
}
