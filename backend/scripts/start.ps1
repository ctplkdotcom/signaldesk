#!/usr/bin/env pwsh
# start.ps1 — One-step full-stack launch with strict failure handling.
# Never prints success unless both services pass health checks.

[CmdletBinding()]
param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000,
    [int]$TimeoutSec = 30
)

$ErrorActionPreference = "Stop"
$BackendDir = "C:\ct_prototype\fp\backend"
$FrontendDir = "C:\ct_prototype\fp\frontend"
$ModulePath = Join-Path $BackendDir "scripts\ProcessManager.psm1"

Import-Module $ModulePath -Force -DisableNameChecking

function Write-Step { Write-Output "$(Get-Date -Format 'HH:mm:ss')  $args" }

$backendProc = $null
$frontendProc = $null

try {
    Write-Step "=== Signal Desk Launcher ==="

    # D5: Kill any old processes
    Get-Process -Name "python","node" -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 1

    # --- Start backend ---
    Write-Step "Starting backend on port $BackendPort..."
    $backendProc = Start-ManagedProcess -Tag "backend" -FilePath "python" `
        -ArgumentList @("_demo_server.py") `
        -WorkingDirectory $BackendDir -Port $BackendPort `
        -HealthUrl "http://localhost:${BackendPort}/" `
        -HealthTimeoutSec $TimeoutSec

    Assert-ProcessStarted -Process $backendProc -Label "backend"
    Write-Step "Backend PID $($backendProc.Id) is ready."

    # --- Start frontend ---
    Write-Step "Starting frontend on port $FrontendPort..."
    $npxPath = (Get-Command "npx.cmd" -ErrorAction Stop).Source
    $frontendProc = Start-ManagedProcess -Tag "frontend" -FilePath $npxPath `
        -ArgumentList @("next", "dev", "-p", $FrontendPort) `
        -WorkingDirectory $FrontendDir -Port $FrontendPort `
        -HealthUrl "http://localhost:${FrontendPort}" `
        -HealthTimeoutSec 45

    Assert-ProcessStarted -Process $frontendProc -Label "frontend"
    Write-Step "Frontend PID $($frontendProc.Id) is ready."

    # --- Success ---
    Write-Step ""
    Write-Step "SUCCESS: Signal Desk is running."
    Write-Step "  Frontend: http://localhost:$FrontendPort"
    Write-Step "  Backend:  http://localhost:$BackendPort"
    Write-Step "  API Docs: http://localhost:$BackendPort/docs"
    Write-Step "  Backend PID: $($backendProc.Id)"
    Write-Step "  Frontend PID: $($frontendProc.Id)"
    Write-Step ""

    Write-Step "Opening browser..."
    try { Start-Process "http://localhost:$FrontendPort" } catch {}

    Write-Step "Press Ctrl+C to stop both servers."
    while ($true) { Start-Sleep -Seconds 10 }
}
catch {
    Write-Step "FAILED: $_"
    Write-Output ""
    Write-ProcessLogs -Tag "backend"
    Write-Output ""
    Write-ProcessLogs -Tag "frontend"
    Write-Output ""
    Write-Step "Cleanup completed."
    exit 1
}
finally {
    Write-Step "Shutting down..."
    Stop-AllProcesses
    Write-Step "Done."
}
