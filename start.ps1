# Sahayak AI — Start Development Servers
# Run this from the project root: .\start.ps1

$root = $PSScriptRoot

Write-Host "Starting Sahayak AI backend (FastAPI on :8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "`$env:PYTHONUTF8='1'; Set-Location '$root\backend'; .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
)

Write-Host "Starting Sahayak AI frontend (Next.js on :3000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root\frontend'; npm run dev"
)

Write-Host ""
Write-Host "Both servers started!" -ForegroundColor Yellow
Write-Host "  Backend: http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
