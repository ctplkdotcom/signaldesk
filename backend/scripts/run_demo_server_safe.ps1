#!/usr/bin/env pwsh
# run_demo_server_safe.ps1 — Start demo server, test endpoints, auto-cleanup.
# Never prints success unless all endpoint tests pass.

[CmdletBinding()]
param(
    [int]$Port = 8000,
    [int]$TimeoutSec = 20
)

$ErrorActionPreference = "Stop"
$BackendDir = "C:\ct_prototype\fp\backend"
$ModulePath = Join-Path $BackendDir "scripts\ProcessManager.psm1"

Import-Module $ModulePath -Force -DisableNameChecking

function Write-Step { Write-Output "$(Get-Date -Format 'HH:mm:ss')  $args" }

$proc = $null

try {
    Write-Step "=== Demo Server Test ==="

    # D5: Kill any old python processes
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 1

    # --- Start server ---
    Write-Step "Starting demo server on port $Port..."
    $proc = Start-ManagedProcess -Tag "demo" -FilePath "python" `
        -ArgumentList @("_demo_server.py") `
        -WorkingDirectory $BackendDir -Port $Port `
        -HealthUrl "http://localhost:${Port}/" `
        -HealthTimeoutSec $TimeoutSec

    Assert-ProcessStarted -Process $proc -Label "demo server"
    Write-Step "Server PID $($proc.Id) is ready."

    # --- Test endpoints ---
    $base = "http://localhost:$Port"

    Write-Step "Testing /api/v1/tickers/MU/verification..."
    $muV = Invoke-RestMethod -Uri "${base}/api/v1/tickers/MU/verification" -ErrorAction Stop
    if ($muV.ticker -ne "MU") { throw "Verification: expected ticker MU, got $($muV.ticker)" }
    Write-Step "  OK — $($muV.verification_links.Count) links"

    Write-Step "Testing /api/v1/tickers/MU/decision-summary..."
    $muD = Invoke-RestMethod -Uri "${base}/api/v1/tickers/MU/decision-summary" -ErrorAction Stop
    if ($muD.overall_direction -notin @("bullish","bearish","neutral")) { throw "Decision-summary: invalid direction $($muD.overall_direction)" }
    Write-Step "  OK — direction=$($muD.overall_direction) confidence=$($muD.composite_confidence)"

    Write-Step "Testing /api/v1/tickers/SNDK/price..."
    $sndk = Invoke-RestMethod -Uri "${base}/api/v1/tickers/SNDK/price" -ErrorAction Stop
    Write-Step "  OK — price=$($sndk.price) session=$($sndk.session)"

    Write-Step "Testing /api/v1/dashboard..."
    $dash = Invoke-RestMethod -Uri "${base}/api/v1/dashboard" -ErrorAction Stop
    $count = $dash.watchlist.items.Count
    if ($count -lt 2) { throw "Dashboard: expected at least 2 watchlist items, got $count" }
    Write-Step "  OK — $count watchlist items"

    Write-Step "Testing /api/v1/news..."
    $news = Invoke-RestMethod -Uri "${base}/api/v1/news" -ErrorAction Stop
    if ($news.total -lt 3) { throw "News: expected at least 3 articles, got $($news.total)" }
    Write-Step "  OK — $($news.total) articles"

    Write-Step "Testing /api/v1/health..."
    $hlth = Invoke-RestMethod -Uri "${base}/api/v1/health" -ErrorAction Stop
    if ($hlth.tickers -lt 2) { throw "Health: expected at least 2 tickers, got $($hlth.tickers)" }
    Write-Step "  OK — $($hlth.tickers) tickers tracked"

    Write-Step ""
    Write-Step "SUCCESS: All 6 endpoint tests passed."
}
catch {
    Write-Step "FAILED: $_"
    Write-Output ""
    Write-ProcessLogs -Tag "demo"
    Write-Output ""
    Write-Step "Cleanup completed."
    exit 1
}
finally {
    Write-Step "Cleaning up..."
    Stop-ManagedProcess -Tag "demo"
    Write-Step "Done."
}
