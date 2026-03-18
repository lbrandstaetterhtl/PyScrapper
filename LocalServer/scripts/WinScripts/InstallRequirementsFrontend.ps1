Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# --- Verzeichnisse berechnen --------------------------------
# $PSScriptRoot = ...\PyScrapper\LocalServer\scripts\WinScripts
$ScriptsDir  = Split-Path -Parent $PSScriptRoot
# $ScriptsDir  = ...\PyScrapper\LocalServer\scripts
$LocalServer = Split-Path -Parent $ScriptsDir
# $LocalServer = ...\PyScrapper\LocalServer
$RepoRoot    = Split-Path -Parent $LocalServer
# $RepoRoot    = ...\PyScrapper  ← .csproj-Suche hier

# --- Logging Setup ------------------------------------------
$LogDir = Join-Path $LocalServer "logs"
if (-not (Test-Path $LogDir)) {
  New-Item -ItemType Directory -Path $LogDir | Out-Null
}
$LogFile = Join-Path $LogDir "RequirementsFrontendInstallation.log"

function Write-Log {
  param([string]$Message)
  $logEntry = "[RequirementsFrontendInstallation] $Message"
  Add-Content -Path $LogFile -Value $logEntry -Encoding utf8
  Write-Host $logEntry
}

Write-Log "== Install Frontend Requirements =="

# ─── .NET SDK ─────────────────────────────────────────────────────
Write-Log "Checking .NET SDK..."

$dotnetCmd = Get-Command dotnet -ErrorAction SilentlyContinue
if ($dotnetCmd) {
  $sdkVersion = dotnet --version 2>&1
  Write-Log ".NET SDK $sdkVersion detected ✓"
} else {
  Write-Log ".NET SDK not found — attempting automatic installation..."

  $wingetCmd = Get-Command winget -ErrorAction SilentlyContinue
  if ($wingetCmd) {
    Write-Log "Installing .NET SDK via winget..."
    try {
      $wingetOutput = winget install --id Microsoft.DotNet.SDK.9 -e --accept-source-agreements --accept-package-agreements 2>&1
      Write-Log "winget output: $wingetOutput"

      $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
      $userPath    = [Environment]::GetEnvironmentVariable("Path", "User")
      $env:Path    = "$machinePath;$userPath"
    } catch {
      Write-Log "WARNING: winget install failed: $_"
    }
  }

  $dotnetCmd = Get-Command dotnet -ErrorAction SilentlyContinue
  if (-not $dotnetCmd) {
    Write-Log "Falling back to dotnet-install.ps1..."
    try {
      $installScript = Join-Path $env:TEMP "dotnet-install.ps1"
      Invoke-WebRequest -Uri "https://dot.net/v1/dotnet-install.ps1" -OutFile $installScript -UseBasicParsing
      & $installScript -Channel 9.0 2>&1 | ForEach-Object { Write-Log "  $_" }

      $dotnetDir = Join-Path $env:LOCALAPPDATA "Microsoft\dotnet"
      if (Test-Path $dotnetDir) {
        $env:Path = "$dotnetDir;$env:Path"
        Write-Log "Added $dotnetDir to session PATH"
      }
    } catch {
      Write-Log "ERROR: Failed to download/run dotnet-install.ps1: $_"
    }
  }

  $dotnetCmd = Get-Command dotnet -ErrorAction SilentlyContinue
  if ($dotnetCmd) {
    $sdkVersion = dotnet --version 2>&1
    Write-Log ".NET SDK $sdkVersion installed ✓"
  } else {
    Write-Log "ERROR: .NET SDK could not be installed. Please install manually from https://dot.net"
    exit 1
  }
}

# ─── Avalonia Templates ───────────────────────────────────────────
Write-Log "Checking Avalonia templates..."

$avaloniaTemplates = dotnet new list 2>&1 | Select-String -Pattern "avalonia" -SimpleMatch
if ($avaloniaTemplates) {
  Write-Log "Avalonia templates already installed ✓"
} else {
  Write-Log "Avalonia templates not found, installing Avalonia.Templates..."
  try {
    $templateOutput = dotnet new install Avalonia.Templates 2>&1
    if ($LASTEXITCODE -ne 0) {
      Write-Log "WARNING: Failed to install Avalonia.Templates: $templateOutput"
    } else {
      Write-Log "Avalonia.Templates installed ✓"
    }
  } catch {
    Write-Log "WARNING: Failed to install Avalonia.Templates: $_"
  }
}

# ─── SQLite ───────────────────────────────────────────────────────
Write-Log "Checking SQLite..."

$sqliteCmd = Get-Command sqlite3 -ErrorAction SilentlyContinue
if ($sqliteCmd) {
  $sqliteVersion = sqlite3 --version 2>&1
  Write-Log "SQLite $sqliteVersion detected ✓"
} else {
  Write-Log "SQLite not found — installing via winget..."
  try {
    $sqliteOutput = winget install --id SQLite.SQLite -e --accept-source-agreements --accept-package-agreements 2>&1
    Write-Log "winget output: $sqliteOutput"

    # PATH für aktuelle Session aktualisieren
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath    = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path    = "$machinePath;$userPath"

    $sqliteCmd = Get-Command sqlite3 -ErrorAction SilentlyContinue
    if ($sqliteCmd) {
      Write-Log "SQLite installed ✓"
    } else {
      Write-Log "ERROR: SQLite could not be installed. Please install manually from https://sqlite.org"
      exit 1
    }
  } catch {
    Write-Log "ERROR: winget install for SQLite failed: $_"
    exit 1
  }
}

# ─── NuGet Packages aus .csproj ──────────────────────────────────
Write-Log "Repo root: $RepoRoot"

$csprojFiles = Get-ChildItem -Path $RepoRoot -Recurse -Filter "*.csproj" |
  Where-Object { $_.FullName -notmatch '\\bin\\|\\obj\\' }

if ($csprojFiles.Count -eq 0) {
  Write-Log "ERROR: No .csproj files found under $RepoRoot"
  exit 1
}

$requiredPackages = @()

foreach ($csproj in $csprojFiles) {
  Write-Log "Reading $($csproj.FullName)"
  [xml]$xml = Get-Content $csproj.FullName -Encoding utf8

  foreach ($itemGroup in $xml.Project.ItemGroup) {
    foreach ($pkg in $itemGroup.PackageReference) {
      if ($pkg -and $pkg.Include -and $pkg.Version) {
        $requiredPackages += [PSCustomObject]@{
          Name    = $pkg.Include
          Version = $pkg.Version
          Csproj  = $csproj.FullName
        }
      }
    }
  }
}

$requiredPackages = $requiredPackages | Sort-Object Name, Version -Unique

Write-Log "Found $($requiredPackages.Count) required package(s)"

# NuGet Cache Pfad
$nugetCache = $null
try {
  $rawOutput  = dotnet nuget locals global-packages --list 2>&1
  $cacheLine  = ($rawOutput | Out-String) -split "`n" |
    Where-Object { $_ -match 'global-packages' } |
    Select-Object -First 1
  if ($cacheLine) {
    $nugetCache = ($cacheLine -replace '.*global-packages:\s*', '').Trim()
  }
} catch {}

if (-not $nugetCache -or -not (Test-Path $nugetCache)) {
  $nugetCache = Join-Path $env:USERPROFILE ".nuget\packages"
}

Write-Log "NuGet cache: $nugetCache"

$alreadyInstalled = 0
$newlyInstalled   = 0
$failed           = 0

foreach ($pkg in $requiredPackages) {
  $pkgDir = Join-Path $nugetCache ($pkg.Name.ToLower()) | Join-Path -ChildPath $pkg.Version

  if (Test-Path $pkgDir) {
    Write-Log "$($pkg.Name) $($pkg.Version) — already installed ✓"
    $alreadyInstalled++
  } else {
    Write-Log "$($pkg.Name) $($pkg.Version) — not cached, installing..."
    try {
      $output = dotnet add $pkg.Csproj package $pkg.Name --version $pkg.Version 2>&1
      if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR installing $($pkg.Name) $($pkg.Version): $output"
        $failed++
      } else {
        Write-Log "$($pkg.Name) $($pkg.Version) — newly installed ✓"
        $newlyInstalled++
      }
    } catch {
      Write-Log "ERROR installing $($pkg.Name) $($pkg.Version): $_"
      $failed++
    }
  }
}

Write-Log "Running dotnet restore..."
foreach ($csproj in $csprojFiles) {
  $restoreOutput = dotnet restore $csproj.FullName 2>&1
  if ($LASTEXITCODE -ne 0) {
    Write-Log "WARNING: dotnet restore failed for $($csproj.Name): $restoreOutput"
  } else {
    Write-Log "dotnet restore succeeded for $($csproj.Name)"
  }
}

Write-Log "========================================="
Write-Log "  Summary"
Write-Log "========================================="
Write-Log "  Total required:      $($requiredPackages.Count)"
Write-Log "  Already installed:   $alreadyInstalled"
Write-Log "  Newly installed:     $newlyInstalled"
if ($failed -gt 0) {
  Write-Log "  Failed:              $failed"
}
Write-Log "========================================="
Write-Log "== Done =="
