Write-Host "== Stop Server (Port Search) =="

$port = 8765
Write-Host "Looking for process listening on port $port..."

# Finde die Verbindung auf dem Port
$connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue

if ($connection) {
    # Hol die Prozess-ID (PID)
    $pidNum = $connection.OwningProcess

    Write-Host "Found process ID: $pidNum"

    # Prozess beenden
    $proc = Get-Process -Id $pidNum -ErrorAction SilentlyContinue

    if ($proc) {
        Stop-Process -Id $pidNum -Force
        Write-Host "Process on port $port stopped successfully."
    } else {
        Write-Host "Process detected but could not be accessed."
    }
} else {
    Write-Host "No process found listening on port $port."
}

# Zur Sicherheit: Suche nach verwaisten Python-Prozessen mit passenden Argumenten
# (Falls der Port belegt ist, aber der Prozess hängt)
$wmiQuery = "SELECT * FROM Win32_Process WHERE Name LIKE 'python%' AND CommandLine LIKE '%uvicorn server:app%'"
$orphans = Get-CimInstance -Query $wmiQuery -ErrorAction SilentlyContinue

if ($orphans) {
    foreach ($orphan in $orphans) {
        Write-Host "Killing orphaned python process: $($orphan.ProcessId)"
        Stop-Process -Id $orphan.ProcessId -Force -ErrorAction SilentlyContinue
    }
}
