# Sahayak AI

**A multilingual AI assistant that helps rural citizens discover Indian government schemes, check eligibility, and understand their benefits — in their own language.**

---

## Project Overview

Sahayak AI bridges the information gap between India's welfare programmes and the citizens who need them most.

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Complete | Project foundation — Next.js + FastAPI scaffold |
| Phase 2 | ✅ Complete | PostgreSQL database layer — models, repos, schemas, migration |
| Phase 3 | ⏳ Planned | Auth, scheme CRUD, eligibility engine |
| Phase 4 | ⏳ Planned | AI/RAG pipeline, multilingual chat |
| Phase 5 | ⏳ Planned | Admin panel, analytics |

---

## Technology Stack

### Frontend
| Tool | Version | Purpose |
|------|---------|---------|
| Next.js | 15.1.0 | App Router, SSR |
| React | 19.0.0 | UI library |
| TypeScript | 5.x strict | Type safety |
| Tailwind CSS | 3.x | Styling |
| shadcn/ui | latest | Accessible components |
| Zustand | 5.x | State management |
| TanStack Query | 5.x | Server state |
| Axios | 1.x | HTTP client |
| React Hook Form + Zod | latest | Forms & validation |
| Framer Motion | 11.x | Animations |

### Backend
| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12 | Runtime |
| FastAPI | 0.115.5 | ASGI web framework |
| SQLAlchemy | 2.0.36 | Async ORM |
| asyncpg | 0.30.0 | Async PostgreSQL driver |
| Alembic | 1.14.0 | Database migrations |
| Pydantic v2 | 2.10.3 | Validation & settings |
| Uvicorn | 0.32.1 | ASGI server |

---

## Folder Structure

```
sahayak-ai/
├── frontend/                    # Next.js 15 application
│   └── src/
│       ├── app/                 # App Router pages
│       ├── components/          # UI + layout components
│       ├── hooks/               # TanStack Query hooks
│       ├── services/            # Axios API service modules
│       ├── store/               # Zustand slices
│       ├── lib/                 # Utilities, constants, axios config
│       └── types/               # TypeScript interfaces
│
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── main.py              # App factory, middleware, exception handlers
│   │   ├── api/v1/
│   │   │   ├── router.py        # Central v1 router
│   │   │   └── endpoints/
│   │   │       └── database.py  # GET /api/v1/database/health
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic Settings (env-driven)
│   │   │   ├── exceptions.py    # Custom exception hierarchy
│   │   │   ├── exception_handlers.py  # FastAPI exception → JSON
│   │   │   └── logging.py       # Structured logging
│   │   ├── database/
│   │   │   └── database.py      # Async engine, session, check_db_connection()
│   │   ├── models/
│   │   │   ├── enums.py         # All SQLAlchemy / Pydantic enums
│   │   │   ├── user.py          # User ORM model
│   │   │   ├── profile.py       # Profile ORM model (1:1 with User)
│   │   │   ├── scheme.py        # Scheme ORM model
│   │   │   ├── eligibility_rule.py  # EligibilityRule (many per Scheme)
│   │   │   └── chat_history.py  # ChatHistory ORM model
│   │   ├── repositories/
│   │   │   ├── base.py          # BaseRepository[T] — generic CRUD
│   │   │   ├── user_repository.py
│   │   │   ├── profile_repository.py
│   │   │   ├── scheme_repository.py
│   │   │   ├── eligibility_repository.py
│   │   │   └── chat_repository.py
│   │   ├── schemas/             # Pydantic v2 request/response contracts
│   │   ├── services/            # Business logic (populated Phase 3+)
│   │   ├── middleware/          # Request logger
│   │   └── utils/               # Response helpers
│   ├── alembic/
│   │   ├── env.py               # Async Alembic config
│   │   ├── script.py.mako       # Migration template
│   │   └── versions/
│   │       └── 0001_initial_schema.py  # First migration
│   ├── tests/
│   │   └── test_database.py     # 26 tests — all passing
│   ├── pytest.ini
│   ├── requirements.txt
│   └── .env.example
│
├── docker/
│   ├── Dockerfile.frontend
│   └── Dockerfile.backend
├── docker-compose.yml
├── docs/
│   └── ARCHITECTURE.md
└── scripts/
    ├── setup.ps1
    ├── setup.sh
    └── validate_app.py
```

---

## Installation

### Prerequisites
- Node.js 22+
- Python 3.12+
- PostgreSQL 15 or 16
- Git

---

## PostgreSQL Setup

### Option A — Install locally (Windows)
```
1. Download from https://www.postgresql.org/download/windows/
2. Install with default settings, remember the postgres superuser password
3. Open pgAdmin or psql
```

### Option B — Docker (recommended)
```bash
docker run -d \
  --name sahayak_postgres \
  -e POSTGRES_USER=sahayak \
  -e POSTGRES_PASSWORD=sahayak_password \
  -e POSTGRES_DB=sahayak_db \
  -p 5432:5432 \
  postgres:16-alpine
```

### Create the database (if installing locally)
```sql
-- Run in psql as superuser
CREATE USER sahayak WITH PASSWORD 'sahayak_password';
CREATE DATABASE sahayak_db OWNER sahayak;
GRANT ALL PRIVILEGES ON DATABASE sahayak_db TO sahayak;
```

---

## Running the Backend

```bash
cd backend

# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate        # Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL to your PostgreSQL connection

# 4. Run migrations (requires PostgreSQL to be running)
alembic upgrade head

# 5. Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API is available at:
| URL | Purpose |
|-----|---------|
| http://localhost:8000/ | Root — welcome JSON |
| http://localhost:8000/health | App health check |
| http://localhost:8000/api/v1/database/health | DB connectivity check |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc |

---

## Database Migrations

```bash
cd backend

# Apply all pending migrations
alembic upgrade head

# Check current migration version
alembic current

# Show migration history
alembic history --verbose

# Generate a new migration after model changes
alembic revision --autogenerate -m "describe your change here"

# Rollback one migration
alembic downgrade -1

# Rollback ALL migrations (wipes schema)
alembic downgrade base
```

### Migration workflow for new models
```
1. Edit or create a file in app/models/
2. Import it in app/models/__init__.py
3. Run: alembic revision --autogenerate -m "add my_model"
4. Review the generated file in alembic/versions/
5. Run: alembic upgrade head
```

---

## Running the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
copy .env.example .env.local
# Edit .env.local — set NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Start development server
npm run dev
```

Open http://localhost:3000

---

## Running Tests

```bash
cd backend
.venv\Scripts\pytest tests/ -v
```

Expected output: **26 passed**

---

## Running with Docker (full stack)

```bash
# From sahayak-ai/ root
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| PostgreSQL | localhost:5432 |

---

## Environment Variables

### Backend (`backend/.env`)
```env
APP_NAME=Sahayak AI
APP_ENV=development
DATABASE_URL=postgresql+asyncpg://sahayak:sahayak_password@localhost:5432/sahayak_db
DATABASE_ECHO=false
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
SECRET_KEY=generate-with-python-secrets-module
```

### Frontend (`frontend/.env.local`)
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Sahayak AI
```

---

## Future Phases

| Phase | Features |
|-------|---------|
| **Phase 3** | JWT auth, user registration/login, scheme CRUD API, eligibility check |
| **Phase 4** | RAG pipeline (pgvector), multilingual LLM chat (Hindi, Tamil, Telugu…) |
| **Phase 5** | Admin panel, analytics, scheme data ingestion |
| **Phase 6** | PWA, offline support, voice input, SMS fallback |

---

## License

MIT © Sahayak AI Team
"# craftncode2" 
