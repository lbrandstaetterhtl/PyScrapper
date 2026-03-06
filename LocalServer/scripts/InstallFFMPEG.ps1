param(
    [switch]$PersistUserPath
)

$ErrorActionPreference = "Stop"

$ServerRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $ServerRoot "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}
$LogFile = Join-Path $LogDir "FFMPEGInstallation.log"

function Write-Log {
    param([string]$Message)
    $logEntry = "[InstallFFMPEG] $Message"
    Add-Content -Path $LogFile -Value $logEntry -Encoding utf8
    Write-Host $logEntry
}

function Find-FFmpegExe {
    # 1) schon im PATH?
    $cmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    # 2) WinGet packages durchsuchen (yt-dlp.FFmpeg)
    $pkgRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    if (Test-Path $pkgRoot) {
        $hit = Get-ChildItem $pkgRoot -Recurse -Filter ffmpeg.exe -ErrorAction SilentlyContinue |
                Where-Object { $_.FullName -match "yt-dlp\.FFmpeg" } |
                Select-Object -First 1
        if ($hit) { return $hit.FullName }
    }

    return $null
}

Write-Log "Checking for ffmpeg..."

$ffmpegExe = Find-FFmpegExe
if (-not $ffmpegExe) {
    Write-Log "ffmpeg not found. Installing via WinGet..."
    winget install --id=yt-dlp.FFmpeg -e --source=winget
    $ffmpegExe = Find-FFmpegExe
}

if (-not $ffmpegExe) {
    throw "[InstallFFMPEG] Installation ran, but ffmpeg.exe still not found."
}

$ffbin = Split-Path $ffmpegExe -Parent

# Für aktuelle Session (und alle Kind-Prozesse) sofort nutzbar
if ($env:Path -notmatch [regex]::Escape($ffbin)) {
    $env:Path = "$ffbin;$env:Path"
    Write-Log "Added to Session PATH: $ffbin"
} else {
    Write-Log "Session PATH already contains: $ffbin"
}

Write-Log "ffmpeg installed at: $ffmpegExe"
Write-Log "Testing ffmpeg version..."
& $ffmpegExe -version | Select-Object -First 1 | Write-Log

# Optional dauerhaft im User-PATH
if ($PersistUserPath) {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notmatch [regex]::Escape($ffbin)) {
        [Environment]::SetEnvironmentVariable("Path", ($userPath + ";" + $ffbin), "User")
        Write-Log "Added to User PATH: $ffbin (will take effect in new terminals)"
    } else {
        Write-Log "User PATH already contains: $ffbin"
    }
}
