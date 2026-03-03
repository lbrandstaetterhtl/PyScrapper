param(
    [switch]$PersistUserPath
)

$ErrorActionPreference = "Stop"

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

Write-Host "[InstallFFMPEG] Checking for ffmpeg..."

$ffmpegExe = Find-FFmpegExe
if (-not $ffmpegExe) {
    Write-Host "[InstallFFMPEG] ffmpeg not found -> installing via winget (yt-dlp.FFmpeg)..."
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
    Write-Host "[InstallFFMPEG] Added to session PATH: $ffbin"
} else {
    Write-Host "[InstallFFMPEG] Session PATH already contains: $ffbin"
}

Write-Host "[InstallFFMPEG] ffmpeg found at: $ffmpegExe"
Write-Host "[InstallFFMPEG] Testing: ffmpeg -version"
& $ffmpegExe -version | Select-Object -First 1 | Write-Host

# Optional dauerhaft im User-PATH
if ($PersistUserPath) {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notmatch [regex]::Escape($ffbin)) {
        [Environment]::SetEnvironmentVariable("Path", ($userPath + ";" + $ffbin), "User")
        Write-Host "[InstallFFMPEG] Added to User PATH: $ffbin (effective in NEW terminals)"
    } else {
        Write-Host "[InstallFFMPEG] User PATH already contains: $ffbin"
    }
}
