# Sahayak AI (सहायक AI)

**A Multilingual AI Assistant that helps rural Indian citizens discover government welfare schemes, evaluate eligibility, and understand their benefits — in their own language.**

---

## 📌 Project Overview

**Sahayak AI** bridges the information gap between India's welfare programmes and the citizens who need them most. It provides automated scheme discovery, deterministic rule-based eligibility evaluation, personalized AI recommendations, and multilingual support across Indian regional languages.

| Milestone / Component | Status | Description |
|-----------------------|--------|-------------|
| **Core Architecture & Scaffolding** | ✅ Complete | Next.js 15 App Router + FastAPI async backend |
| **PostgreSQL & Database Layer** | ✅ Complete | Async SQLAlchemy 2.0, asyncpg, Alembic migrations, Repositories |
| **Auth & Profile Management** | ✅ Complete | JWT Auth, RBAC, User Profiles with strict validation |
| **Scheme Ingestion & Management** | ✅ Complete | Government data import pipeline (data.gov.in / myScheme), Admin CRUD |
| **Eligibility & Recommendation Engine** | ✅ Complete | Deterministic rule matching engine + smart profile-based recommendations |
| **Translation & Localization (TMS)** | ✅ Complete | Translation Management System + IndicTransToolkit support |
| **RAG Voice Assistant** | ✅ Complete | Whisper → language resolution → gpt-oss-20b → all-MiniLM-L6-v2 → ChromaDB → eligibility rules → gpt-oss-120b → gTTS, across 13 languages + auto-detect. See [`docs/RAG.md`](docs/RAG.md) |
| **Citizen & Admin Portals** | ✅ Complete | Localized citizen web app & administrative analytics dashboard |

---

## 🏗️ Technology Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 15.1.0 | React Framework (App Router, Server Components) |
| **React** | 19.0.0 | Component UI library |
| **TypeScript** | 5.x | Strict type safety |
| **Tailwind CSS** | 3.x | Utility-first styling & responsiveness |
| **shadcn/ui & Radix** | Latest | Accessible UI components |
| **Zustand** | 5.x | Client state management |
| **TanStack Query** | 5.x | Server state & API data caching |
| **Axios** | 1.x | HTTP client with interceptors |
| **Framer Motion** | 11.x | Smooth UI animations |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.12+ | Core runtime |
| **FastAPI** | 0.115.5 | High-performance async ASGI web framework |
| **Pydantic v2** | 2.10.3 | Strict data validation & schema contracts |
| **SQLAlchemy** | 2.0.36 | Async ORM (AsyncSession, select, DeclarativeBase) |
| **asyncpg** | 0.30.0 | High-speed async PostgreSQL driver |
| **Alembic** | 1.14.0 | Database migration manager |
| **httpx** | 0.28.1 | Async & sync HTTP client for API ingestion |
| **Uvicorn** | 0.32.1 | ASGI server |

---

## 📂 Repository Structure

```
sahayak-ai/
├── frontend/                          # Next.js 15 Web Application
│   └── src/
│       ├── app/[locale]/              # Localized App Router pages
│       │   ├── login/ & register/     # Authentication pages
│       │   ├── dashboard/             # Citizen dashboard
│       │   ├── profile/               # Citizen demographic profile
│       │   ├── schemes/               # Scheme catalog & details
│       │   ├── eligibility/           # Interactive eligibility check
│       │   ├── recommendations/       # AI scheme recommendations
│       │   ├── chat/                  # Multilingual assistant chat
│       │   └── admin/                 # Admin suite (schemes, users, TMS, analytics)
│       ├── components/                # Reusable UI & layout components
│       ├── hooks/                     # Custom TanStack Query hooks
│       ├── services/                  # Axios API services
│       ├── store/                     # Zustand store slices
│       └── types/                     # TypeScript interfaces
│
├── backend/                           # FastAPI Application & Services
│   ├── app/
│   │   ├── main.py                    # App factory, middleware, CORS & error handlers
│   │   ├── api/v1/endpoints/          # API route controllers
│   │   │   ├── auth.py                # Authentication & JWT tokens
│   │   │   ├── schemes.py             # Scheme discovery & filtering
│   │   │   ├── eligibility.py         # Eligibility evaluation endpoints
│   │   │   ├── recommendations.py     # Scheme recommendations
│   │   │   ├── government_import.py   # data.gov.in ingestion API
│   │   │   ├── admin_*.py             # Admin users, schemes, TMS & analytics
│   │   │   └── database.py            # DB health checks
│   │   ├── models/                    # SQLAlchemy ORM models & enums
│   │   ├── repositories/              # Async database repository pattern
│   │   ├── schemas/                   # Pydantic v2 request & response schemas
│   │   ├── government_data/           # data.gov.in / HuggingFace import clients
│   │   └── services/                  # Business logic
│   │       ├── rag/                   # RAG voice assistant pipeline (Groq + vector store)
│   │       └── translation/           # IndicTrans2 translation provider + toolkit
│   ├── alembic/                       # Database migrations
│   └── requirements.txt               # Backend dependencies
│
├── docker/                            # Dockerfiles & container assets
├── docs/                              # Architecture specs & project reports
├── scripts/                           # Setup and validation scripts
├── start.ps1                          # One-click startup script (PowerShell)
└── docker-compose.yml                 # Full-stack container orchestration
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.12+**
- **Node.js 20+**
- **PostgreSQL 15+** (or Docker)

---

### 1. Backend Setup

```bash
cd backend

# Create & activate virtual environment
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive API documentation will be available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

### 2. Frontend Setup

```bash
cd frontend

# Install packages
npm install

# Configure environment
cp .env.example .env.local

# Run Next.js development server
npm run dev
```

Visit the citizen portal at **[http://localhost:3000](http://localhost:3000)**.

---

### 3. Running with Docker Compose

To start the full stack (PostgreSQL, FastAPI Backend, Next.js Frontend) with a single command:

```bash
docker compose up --build
```

---

## 🧪 Testing

### Backend & Unit Tests
```bash
cd backend
pytest -v
```

### Frontend
```bash
cd frontend
npm run lint && npm run type-check && npm test
```

---

## 🔒 Environment Configuration

### Backend (`backend/.env`)
```env
APP_NAME=Sahayak AI
APP_ENV=development
DATABASE_URL=postgresql+asyncpg://sahayak:sahayak_password@localhost:5432/sahayak_db
DATABASE_ECHO=false
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
SECRET_KEY=your-secure-random-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Frontend (`frontend/.env.local`)
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Sahayak AI
```

---

## 📄 Documentation

For in-depth documentation, see the [`docs/`](docs/) folder:
- [**ARCHITECTURE.md**](docs/ARCHITECTURE.md): System architecture and data flow.
- [**RAG.md**](docs/RAG.md): RAG voice-assistant pipeline.
- [**FULL_PROJECT_REPORT.md**](docs/FULL_PROJECT_REPORT.md): Comprehensive project implementation report.
- [**MASTER_PROJECT_REPORT.md**](docs/MASTER_PROJECT_REPORT.md): Master technical specifications and evaluation metrics.

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.
