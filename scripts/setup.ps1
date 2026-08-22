# ============================================================
# Sahayak AI — One-shot dev environment setup (Windows PowerShell)
# Usage: .\scripts\setup.ps1
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host "`n🚀 Setting up Sahayak AI..." -ForegroundColor Cyan

# ── Frontend ─────────────────────────────────────────────────────────────
Write-Host "`n[1/4] Installing frontend dependencies..." -ForegroundColor Green
Set-Location frontend
npm install
if (-not (Test-Path .env.local)) {
    Copy-Item .env.example .env.local
    Write-Host "  ✓ Created frontend/.env.local" -ForegroundColor Yellow
}
Set-Location ..

# ── Backend ───────────────────────────────────────────────────────────────
Write-Host "`n[2/4] Creating Python virtual environment..." -ForegroundColor Green
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "  ✓ Created backend/.env" -ForegroundColor Yellow
}
Set-Location ..

Write-Host "`n[3/4] Setup complete!" -ForegroundColor Green

Write-Host "`n[4/4] Commands to start:" -ForegroundColor Cyan
Write-Host "  Frontend : cd frontend; npm run dev"
Write-Host "  Backend  : cd backend; uvicorn app.main:app --reload"
Write-Host "  Docker   : docker compose up --build`n"
