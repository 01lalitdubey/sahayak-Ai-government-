#!/usr/bin/env bash
# ============================================================
# Sahayak AI — One-shot dev environment setup script
# Usage: bash scripts/setup.sh
# ============================================================
set -e

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RESET="\033[0m"

echo -e "${BOLD}🚀 Setting up Sahayak AI development environment...${RESET}\n"

# ── Frontend ─────────────────────────────────────────────────────────────
echo -e "${GREEN}[1/4] Installing frontend dependencies...${RESET}"
cd frontend
npm install
if [ ! -f .env.local ]; then
  cp .env.example .env.local
  echo -e "${YELLOW}  ✓ Created frontend/.env.local from .env.example${RESET}"
fi
cd ..

# ── Backend ───────────────────────────────────────────────────────────────
echo -e "${GREEN}[2/4] Creating Python virtual environment...${RESET}"
cd backend
python3 -m venv .venv
source .venv/bin/activate || source .venv/Scripts/activate 2>/dev/null
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if [ ! -f .env ]; then
  cp .env.example .env
  echo -e "${YELLOW}  ✓ Created backend/.env from .env.example${RESET}"
fi
cd ..

echo -e "${GREEN}[3/4] Done! Virtual environment ready at backend/.venv${RESET}"

echo -e "\n${BOLD}[4/4] Next steps:${RESET}"
echo -e "  Frontend:  cd frontend && npm run dev"
echo -e "  Backend:   cd backend && uvicorn app.main:app --reload"
echo -e "  Docker:    docker compose up --build\n"
