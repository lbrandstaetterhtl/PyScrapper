param(
    [switch]$PersistUserPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Common.ps1"
Initialize-Log -Name 'FFMPEGInstallation.log' -Prefix 'InstallFFMPEG'

function Find-FFmpegExe {
    $cmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $pkgRoot = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages'
    if (Test-Path -LiteralPath $pkgRoot) {
        $hit = Get-ChildItem -Path $pkgRoot -Recurse -Filter 'ffmpeg.exe' -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match 'yt-dlp\.FFmpeg' } |
            Select-Object -First 1
        if ($hit) { return $hit.FullName }
    }

    return $null
}

Write-Log 'Checking ffmpeg...'
$ffmpegExe = Find-FFmpegExe
if (-not $ffmpegExe) {
    Ensure-Winget
    Write-Log 'ffmpeg not found. Installing via winget...'
    Invoke-LoggedCommand -FilePath 'winget' -ArgumentList @('install','-e','--id','yt-dlp.FFmpeg','--accept-package-agreements','--accept-source-agreements')
    Refresh-Path
    $ffmpegExe = Find-FFmpegExe
}

if (-not $ffmpegExe) {
    throw 'ffmpeg installation finished but ffmpeg.exe was not found.'
}

$ffmpegDir = Split-Path -Parent $ffmpegExe
Ensure-CommandInPath -Directory $ffmpegDir -PersistUserPath:$PersistUserPath
Write-Log "ffmpeg ready: $ffmpegExe"
Invoke-LoggedCommand -FilePath $ffmpegExe -ArgumentList @('-version') -AllowFailure | Select-Object -First 1 | ForEach-Object { Write-Log $_ }
