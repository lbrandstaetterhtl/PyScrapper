param(
    [string]$HostAddr = "127.0.0.1",
    [int]$Port = 8765
)

$ErrorActionPreference = "SilentlyContinue"

# Logging setup
$ServerRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $ServerRoot "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}
$LogFile = Join-Path $LogDir "StopServer.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] $Message"
    Add-Content -Path $LogFile -Value $logEntry -Encoding utf8
    Write-Output $logEntry
}

Write-Log "== Stop Server =="

$baseUrl = "http://$HostAddr`:$Port"

# 1) Graceful shutdown via API (wenn erreichbar)
try {
    $health = Invoke-RestMethod -Method GET -Uri "$baseUrl/health" -TimeoutSec 2
    if ($health.ok -eq $true) {
        Write-Log "Server reachable. Sending quit command..."
        Invoke-RestMethod -Method POST -Uri "$baseUrl/command" `
            -ContentType "application/json" `
            -Body '{"command":"quit"}' `
            -TimeoutSec 2 | Out-Null

        Start-Sleep -Milliseconds 800
    }
} catch {
    Write-Log "Server not reachable via API (or already down). Falling back to port-kill..."
}

# 2) Fallback: Prozess auf dem Port finden und killen
$connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($connection) {
    $pidNum = $connection.OwningProcess
    if ($pidNum) {
        Write-Log "Killing process on port $Port (PID $pidNum)..."
        Stop-Process -Id $pidNum -Force -ErrorAction SilentlyContinue
        Write-Log "Process stopped."
    } else {
        Write-Log "Found connection but no PID."
    }
} else {
    Write-Log "No process found listening on port $Port."
}