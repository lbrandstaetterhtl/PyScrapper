param(
    [string]$HostAddr = "127.0.0.1",
    [int]$Port = 8765
)

$ErrorActionPreference = "SilentlyContinue"

Write-Host "== Stop Server =="

$baseUrl = "http://$HostAddr`:$Port"

# 1) Graceful shutdown via API (wenn erreichbar)
try {
    $health = Invoke-RestMethod -Method GET -Uri "$baseUrl/health" -TimeoutSec 2
    if ($health.ok -eq $true) {
        Write-Host "Server reachable. Sending quit command..."
        Invoke-RestMethod -Method POST -Uri "$baseUrl/command" `
            -ContentType "application/json" `
            -Body '{"command":"quit"}' `
            -TimeoutSec 2 | Out-Null

        Start-Sleep -Milliseconds 800
    }
} catch {
    Write-Host "Server not reachable via API (or already down). Falling back to port-kill..."
}

# 2) Fallback: Prozess auf dem Port finden und killen
$connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($connection) {
    $pidNum = $connection.OwningProcess
    if ($pidNum) {
        Write-Host "Killing process on port $Port (PID $pidNum)..."
        Stop-Process -Id $pidNum -Force -ErrorAction SilentlyContinue
        Write-Host "Process stopped."
    } else {
        Write-Host "Found connection but no PID."
    }
} else {
    Write-Host "No process found listening on port $Port."
}