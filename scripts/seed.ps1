# Signal Desk - Seed Database
# Run from project root: powershell -File scripts\seed.ps1

Write-Host "Seeding Signal Desk database..." -ForegroundColor Cyan
Set-Location -LiteralPath "$PSScriptRoot\..\backend"
python -m app.seed
Write-Host "Seed complete!" -ForegroundColor Green
