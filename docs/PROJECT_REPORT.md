# Sahayak AI — Project Foundation Report

**Date:** July 29, 2026
**Status:** Phase 1 Complete — Foundation Running
**Prepared for:** Handoff to AI assistant (ChatGPT) for continued development

---

## 1. What This Project Is

**Sahayak AI** is a multilingual AI-powered web application designed to help rural Indian citizens:
- Discover central and state government schemes and subsidies
- Check their personal eligibility for those schemes
- Get plain-language explanations via an AI chat assistant
- Interact in Hindi, Tamil, Telugu, Bengali, Marathi, and other Indian languages

The application has two parts: a **Next.js frontend** and a **FastAPI backend**, communicating over a REST API, with **PostgreSQL** as the database.

---

## 2. What Has Been Built (Phase 1)

Phase 1 is **architecture and foundation only**. No authentication, no AI, no business logic has been implemented yet. Everything below is scaffolding, configuration, and wiring that future phases build on top of.

### 2.1 What is running right now

| Service | URL | Status |
|---------|-----|--------|
| Frontend (Next.js 15) | http://localhost:3001 | ✅ Running |
| Backend (FastAPI) | http://localhost:8000 | ✅ Running |
| `GET /` | http://localhost:8000/ | ✅ Returns JSON welcome |
| `GET /health` | http://localhost:8000/health | ✅ Returns `"status":"healthy"` |
| Swagger UI | http://localhost:8000/docs | ✅ Live |
| ReDoc | http://localhost:8000/redoc | ✅ Live |
| PostgreSQL | Not started | ⏳ Configured but not connected |

The backend starts without a database connection — the engine is created but deferred. No crash on boot.

---

## 3. Full Directory Structure

```
sahayak-ai/
│
├── .gitignore                          # Ignores node_modules, .venv, .env, __pycache__, etc.
├── README.md                           # Full project documentation
├── docker-compose.yml                  # Orchestrates frontend + backend + postgres
│
├── backend/
│   ├── .env                            # Active env file (copied from .env.example)
│   ├── .env.example                    # Template for all env variables
│   ├── alembic.ini                     # Alembic migration config
│   ├── requirements.txt                # Pinned Python dependencies
│   ├── .venv/                          # Python 3.12 virtual environment (local, not committed)
│   │
│   ├── alembic/
│   │   ├── env.py                      # Async Alembic runner, loads settings from app
│   │   └── versions/                   # Migration files go here (empty for now)
│   │
│   └── app/
│       ├── __init__.py
│       ├── main.py                     # FastAPI app factory, middleware, root endpoints
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── router.py           # Central v1 router — registers all endpoint modules
│       │       └── endpoints/
│       │           └── __init__.py     # Placeholder — domain routers added here per phase
│       │
│       ├── auth/
│       │   ├── __init__.py
│       │   └── dependencies.py        # Placeholder — JWT + current_user deps (Phase 2)
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py               # Pydantic v2 Settings — reads from .env
│       │   └── logging.py              # Structured logging setup (JSON in prod, readable in dev)
│       │
│       ├── database/
│       │   ├── __init__.py
│       │   └── database.py             # SQLAlchemy 2.0 async engine, session factory, Base, get_db()
│       │
│       ├── middleware/
│       │   ├── __init__.py
│       │   └── request_logger.py       # Logs every request: method, path, status, duration
│       │
│       ├── models/
│       │   ├── __init__.py             # Import all models here so Alembic finds them
│       │   └── base.py                 # UUIDMixin + TimestampMixin for all ORM models
│       │
│       ├── repositories/
│       │   ├── __init__.py
│       │   └── base.py                 # Generic BaseRepository[T] with get_by_id, get_all, create, delete
│       │
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── common.py               # SuccessResponse, ErrorResponse, PaginatedResponse envelopes
│       │
│       ├── services/
│       │   └── __init__.py             # Placeholder — business logic modules added per phase
│       │
│       └── utils/
│           ├── __init__.py
│           └── response.py             # ok() / error() factory helpers
│
├── frontend/
│   ├── package.json                    # All npm dependencies pinned
│   ├── tsconfig.json                   # TypeScript strict mode + path aliases
│   ├── next.config.ts                  # Next.js 15 config (images, env, redirects)
│   ├── tailwind.config.ts              # Tailwind + dark mode + Sahayak brand tokens
│   ├── postcss.config.mjs
│   ├── components.json                 # shadcn/ui configuration
│   ├── .eslintrc.json                  # ESLint rules
│   ├── .prettierrc                     # Prettier config with tailwindcss plugin
│   ├── .env.example                    # Frontend env template
│   ├── node_modules/                   # Installed (not committed)
│   │
│   └── src/
│       ├── app/                        # Next.js 15 App Router
│       │   ├── layout.tsx              # Root HTML shell, Inter font, metadata, Providers
│       │   ├── page.tsx                # Landing page (Hero + Features)
│       │   ├── providers.tsx           # QueryClientProvider + ThemeProvider
│       │   ├── not-found.tsx           # Custom 404 page
│       │   ├── login/page.tsx          # Placeholder
│       │   ├── register/page.tsx       # Placeholder
│       │   ├── dashboard/page.tsx      # Placeholder
│       │   ├── chat/page.tsx           # Placeholder
│       │   ├── schemes/page.tsx        # Placeholder
│       │   ├── eligibility/page.tsx    # Placeholder
│       │   ├── profile/page.tsx        # Placeholder
│       │   └── admin/page.tsx          # Placeholder
│       │
│       ├── components/
│       │   ├── ui/
│       │   │   ├── button.tsx          # shadcn/ui Button (CVA variants)
│       │   │   ├── card.tsx            # shadcn/ui Card family
│       │   │   ├── badge.tsx           # shadcn/ui Badge
│       │   │   └── separator.tsx       # Radix Separator
│       │   ├── layout/
│       │   │   ├── Navbar.tsx          # Responsive navbar, dark/light toggle, mobile drawer
│       │   │   ├── Footer.tsx          # Site footer with links
│       │   │   └── MainLayout.tsx      # Navbar + children + Footer shell
│       │   └── common/
│       │       ├── PageHeader.tsx      # Title + description block
│       │       └── PlaceholderPage.tsx # "Under construction" card used by all placeholder pages
│       │
│       ├── hooks/
│       │   └── use-health.ts           # TanStack Query hook — polls /health endpoint
│       │
│       ├── lib/
│       │   ├── utils.ts                # cn(), formatDate(), capitalize(), sleep()
│       │   ├── constants.ts            # APP_NAME, API_URL, ROUTES
│       │   ├── axios.ts                # Pre-configured Axios instance with interceptors
│       │   └── query-client.ts         # TanStack QueryClient singleton
│       │
│       ├── services/
│       │   ├── api.service.ts          # Base get/post/put/patch/delete wrappers
│       │   └── health.service.ts       # Calls GET /health
│       │
│       ├── store/
│       │   ├── ui-store.ts             # Zustand: sidebar, mobile menu, loading state
│       │   └── auth-store.ts           # Zustand: user, accessToken, isAuthenticated (placeholder)
│       │
│       ├── types/
│       │   └── index.ts                # ApiSuccessResponse, ApiErrorResponse, NavItem, etc.
│       │
│       └── styles/
│           └── globals.css             # Tailwind base + CSS variables for light/dark themes
│
├── docker/
│   ├── Dockerfile.frontend             # Multi-stage: deps → build → runner (non-root user)
│   └── Dockerfile.backend              # Multi-stage: builder → runner (non-root user)
│
├── docs/
│   ├── ARCHITECTURE.md                 # Layer diagrams, data flow, communication explanation
│   └── PROJECT_REPORT.md              # This file
│
└── scripts/
    ├── setup.sh                        # Linux/macOS one-shot setup
    ├── setup.ps1                       # Windows PowerShell one-shot setup
    └── validate_syntax.py              # Python AST syntax checker (all 25 files passed)
```

---

## 4. Technology Stack

### Frontend
| Package | Version | Role |
|---------|---------|------|
| next | 15.1.0 | Framework — App Router, SSR, image optimization |
| react | 19.0.0 | UI library |
| typescript | 5.7.2 | Type safety (strict mode enabled) |
| tailwindcss | 3.4.17 | Utility-first CSS |
| shadcn/ui components | latest | Accessible UI primitives via Radix |
| @tanstack/react-query | 5.62.7 | Server state, caching, background refetch |
| zustand | 5.0.2 | Global client state (auth, UI) |
| axios | 1.7.9 | HTTP client |
| react-hook-form | 7.54.2 | Form state management |
| zod | 3.24.1 | Schema validation |
| @hookform/resolvers | 3.9.1 | Connects Zod to React Hook Form |
| framer-motion | 11.15.0 | Animations |
| next-themes | 0.4.4 | Dark/light/system theme |
| lucide-react | 0.468.0 | Icon library |
| class-variance-authority | 0.7.1 | Variant-based component styling |
| clsx + tailwind-merge | latest | Safe class merging (cn()) |

### Backend
| Package | Version | Role |
|---------|---------|------|
| fastapi | 0.115.5 | ASGI web framework |
| uvicorn[standard] | 0.32.1 | ASGI server |
| sqlalchemy | 2.0.36 | Async ORM |
| asyncpg | 0.30.0 | Async PostgreSQL driver |
| alembic | 1.14.0 | Database migrations |
| pydantic | 2.10.3 | Data validation |
| pydantic-settings | 2.6.1 | Env-driven Settings class |
| python-dotenv | 1.0.1 | .env file loading |
| passlib[bcrypt] | 1.7.4 | Password hashing (ready for Phase 2) |
| python-jose[cryptography] | 3.3.0 | JWT tokens (ready for Phase 2) |
| httpx | 0.28.1 | Async HTTP client |
| pytest + pytest-asyncio | 8.3.4 | Testing framework |

---

## 5. Architecture Explained

### How Frontend and Backend Communicate

```
Browser
  └── Next.js Page (React Server Component or Client Component)
        └── TanStack Query (useQuery / useMutation)
              └── Service Module (e.g. health.service.ts)
                    └── Axios instance (src/lib/axios.ts)
                          └── HTTP Request → FastAPI backend (localhost:8000)
                                └── Route Handler (app/api/v1/endpoints/)
                                      └── Service Layer (app/services/)
                                            └── Repository Layer (app/repositories/)
                                                  └── SQLAlchemy AsyncSession → PostgreSQL
```

Key details:
- All API calls use the Axios instance in `src/lib/axios.ts` — base URL is `NEXT_PUBLIC_API_BASE_URL`
- All backend endpoints are prefixed `/api/v1/`
- All responses follow a consistent envelope: `{ success, message, data }` or `{ success, message, errors, status_code }`
- Auth token (Phase 2) will be injected in the Axios request interceptor — one place, applies everywhere
- TanStack Query wraps all service calls, giving automatic caching, loading/error states, and background refetch

### How PostgreSQL Will Connect (Phase 3)

1. Set `DATABASE_URL` in `backend/.env` to your PostgreSQL connection string
2. The `Settings` class in `app/core/config.py` reads it via Pydantic Settings
3. `app/database/database.py` creates an `AsyncEngine` using `asyncpg` driver — no connection is opened at import time
4. On first actual database request, the engine opens a connection from its pool
5. Each request gets an `AsyncSession` injected via `Depends(get_db)` — it commits on success, rolls back on exception
6. Run `alembic upgrade head` once to apply all migrations before starting the server
7. When you add a new model to `app/models/`, run `alembic revision --autogenerate -m "description"` to generate the migration

---

## 6. Environment Variables

### Backend (`backend/.env`)
```
APP_NAME=Sahayak AI
APP_VERSION=0.1.0
APP_ENV=development
LOG_LEVEL=INFO
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=postgresql+asyncpg://sahayak:sahayak_password@localhost:5432/sahayak_db
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

### Frontend (`frontend/.env.local`)
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=v1
NEXT_PUBLIC_APP_NAME=Sahayak AI
NEXT_PUBLIC_APP_VERSION=0.1.0
NEXT_PUBLIC_ENABLE_CHAT=false
NEXT_PUBLIC_ENABLE_VOICE=false
```

---

## 7. Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| Repository Pattern | `app/repositories/base.py` | Isolates all SQL — services never write queries |
| Generic Repository | `BaseRepository[T]` | DRY CRUD — domain repos inherit and extend |
| Dependency Injection | FastAPI `Depends()` | DB session, auth, settings injected into routes |
| Settings Singleton | `@lru_cache` on `get_settings()` | Env loaded once, shared everywhere |
| Response Envelope | `SuccessResponse[T]`, `ErrorResponse` | Frontend always knows the response shape |
| Service Layer | `app/services/` | Business logic never lives in route handlers |
| Provider Pattern | `src/app/providers.tsx` | All React context wrapped in one place |
| Zustand Slices | `ui-store.ts`, `auth-store.ts` | Separate concerns, no single god store |
| CVA Variants | `button.tsx` | Type-safe component variants without if-chains |

---

## 8. Pages and Their Status

| Route | File | Status | Phase |
|-------|------|--------|-------|
| `/` | `app/page.tsx` | ✅ Full landing page | Phase 1 |
| `/login` | `app/login/page.tsx` | 🔲 Placeholder | Phase 2 |
| `/register` | `app/register/page.tsx` | 🔲 Placeholder | Phase 2 |
| `/dashboard` | `app/dashboard/page.tsx` | 🔲 Placeholder | Phase 3 |
| `/schemes` | `app/schemes/page.tsx` | 🔲 Placeholder | Phase 3 |
| `/eligibility` | `app/eligibility/page.tsx` | 🔲 Placeholder | Phase 3 |
| `/chat` | `app/chat/page.tsx` | 🔲 Placeholder | Phase 4 |
| `/profile` | `app/profile/page.tsx` | 🔲 Placeholder | Phase 2 |
| `/admin` | `app/admin/page.tsx` | 🔲 Placeholder | Phase 5 |

---

## 9. API Endpoints (Currently Live)

| Method | Path | Response |
|--------|------|----------|
| GET | `/` | `{ success, message, version, environment, docs, redoc }` |
| GET | `/health` | `{ success, status: "healthy", app, version, environment }` |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |
| GET | `/openapi.json` | OpenAPI schema |

Future endpoints (added per phase) are registered in `app/api/v1/router.py`.

---

## 10. What Is NOT Implemented Yet

The following are explicitly excluded from Phase 1 per the original spec:

- ❌ Authentication (JWT login, registration, password hashing, token refresh)
- ❌ User model and user management
- ❌ Scheme database and CRUD
- ❌ Eligibility engine
- ❌ AI / LLM integration
- ❌ RAG pipeline (vector search, embeddings)
- ❌ Multilingual support (i18n)
- ❌ Chat interface
- ❌ Voice input
- ❌ Admin panel logic
- ❌ Recommendation engine
- ❌ PostgreSQL connection (configured, not connected)

---

## 11. Roadmap — Future Phases

| Phase | Work |
|-------|------|
| **Phase 2** | JWT auth, bcrypt password hashing, login/register API + pages, protected routes, role-based access (user / admin) |
| **Phase 3** | PostgreSQL connection, User + Scheme + Eligibility models, Alembic migrations, CRUD APIs, Dashboard + Schemes + Eligibility pages |
| **Phase 4** | LLM integration (OpenAI / Gemini / local model), RAG pipeline with pgvector, multilingual chat (Hindi, Tamil, etc.), Chat page |
| **Phase 5** | Admin panel, analytics, scheme data ingestion pipeline, content moderation |
| **Phase 6** | PWA, offline support, voice input, SMS fallback for low-connectivity areas |

---

## 12. Commands to Continue Development

### Start Backend (development)
```bash
cd backend
.venv\Scripts\Activate.ps1          # Windows
# source .venv/bin/activate          # Linux/macOS
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend (development)
```bash
cd frontend
npm run dev
```

### Run with Docker (full stack)
```bash
docker compose up --build
```

### Add a new database model (after Phase 3 database is connected)
```bash
cd backend
# 1. Create model in app/models/your_model.py
# 2. Import it in app/models/__init__.py
# 3. Generate migration
alembic revision --autogenerate -m "add your_model table"
# 4. Apply migration
alembic upgrade head
```

### Install a new frontend package
```bash
cd frontend
npm install <package-name>
```

### Add a shadcn/ui component
```bash
cd frontend
npx shadcn@latest add <component-name>
# e.g: npx shadcn@latest add input
# e.g: npx shadcn@latest add dialog
```

### Run Python syntax validation
```bash
python scripts/validate_syntax.py
```

---

## 13. Key File Locations — Quick Reference

| What you need | File |
|---------------|------|
| Add a new API route | `backend/app/api/v1/router.py` + new file in `endpoints/` |
| Change backend config | `backend/app/core/config.py` + `backend/.env` |
| Add a new ORM model | `backend/app/models/` |
| Add a new Pydantic schema | `backend/app/schemas/` |
| Add business logic | `backend/app/services/` |
| Add DB queries | `backend/app/repositories/` |
| Add a new page | `frontend/src/app/<route>/page.tsx` |
| Add a new component | `frontend/src/components/` |
| Add a new API service | `frontend/src/services/` |
| Add a new global state | `frontend/src/store/` |
| Change theme colors | `frontend/src/styles/globals.css` (CSS variables) |
| Change brand tokens | `frontend/tailwind.config.ts` (sahayak palette) |

---

## 14. Verification Results

| Check | Result |
|-------|--------|
| All 25 Python files — AST syntax check | ✅ Passed |
| Backend uvicorn startup | ✅ No errors |
| Backend `GET /` response | ✅ `{"success":true}` |
| Backend `GET /health` response | ✅ `{"status":"healthy"}` |
| Frontend `npm install` | ✅ 453 packages installed |
| Frontend Next.js 15 Turbopack startup | ✅ Ready in 1738ms |
| Frontend `GET http://localhost:3001` | ✅ HTTP 200 OK |
| Docker Compose file | ✅ Created (not tested — Docker Desktop required) |

---

*End of Report — Phase 1 Foundation Complete*
