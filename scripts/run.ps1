# Signal Desk - Run locally
# Run from project root: powershell -File scripts\run.ps1

$ErrorActionPreference = "Stop"

Write-Host "Starting Signal Desk..." -ForegroundColor Cyan

# Start backend
$backendJob = Start-Job -ScriptBlock {
    Set-Location -LiteralPath "$using:PSScriptRoot\..\backend"
    $env:PYTHONPATH = "$using:PSScriptRoot\..\backend"
    uvicorn app.main:app --reload --port 8000
}

# Start frontend
$frontendJob = Start-Job -ScriptBlock {
    Set-Location -LiteralPath "$using:PSScriptRoot\..\frontend"
    npm run dev
}

Write-Host "Backend: http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow

try {
    Receive-Job -Job $backendJob -Wait
} finally {
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $frontendJob -ErrorAction SilentlyContinue
}
