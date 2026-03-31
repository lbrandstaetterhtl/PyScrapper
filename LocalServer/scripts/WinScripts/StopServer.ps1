param(
    [string]$HostAddr = '127.0.0.1',
    [int]$Port = 8765
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'SilentlyContinue'

. "$PSScriptRoot\Common.ps1"
Initialize-Log -Name 'StopServer.log' -Prefix 'StopServer'

$baseUrl = "http://$HostAddr`:$Port"
Write-Log "Stopping server at $baseUrl"

try {
    $health = Invoke-RestMethod -Method Get -Uri "$baseUrl/health" -TimeoutSec 2
    if ($health.ok -eq $true) {
        Write-Log 'Server is reachable. Sending quit command...'
        Invoke-RestMethod -Method Post -Uri "$baseUrl/command" -ContentType 'application/json' -Body '{"command":"quit"}' -TimeoutSec 2 | Out-Null
        Start-Sleep -Milliseconds 1000
    }
}
catch {
    Write-Log 'Graceful shutdown failed or server is already down. Falling back to process kill.'
}

$connections = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
if (-not $connections) {
    Write-Log "No listening process found on port $Port."
    exit 0
}

foreach ($connection in $connections) {
    if ($connection.OwningProcess) {
        Write-Log "Stopping PID $($connection.OwningProcess) on port $Port"
        Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

Write-Log 'Stop sequence finished.'
