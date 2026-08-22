# Sahayak AI — Complete Project Report
**Date:** July 31, 2026
**Status:** Phase 1 + Phase 2 Complete — Both Services Running
**Purpose:** Full handoff document covering everything built so far

---

## 1. What Is Sahayak AI

Sahayak AI is a **multilingual AI-powered web application** built for rural Indian citizens.
Its goal is to help people:
- Discover central and state government schemes and subsidies
- Check personal eligibility for those schemes
- Get plain-language explanations via an AI chat assistant
- Interact in Hindi, Tamil, Telugu, Bengali, Marathi, and other Indian languages

The application is split into two independent services:
- **Frontend** — Next.js 15 (React 19, TypeScript)
- **Backend** — FastAPI (Python 3.12, SQLAlchemy 2.0, PostgreSQL)

---

## 2. Overall Progress Summary

| Phase | Work Done | Status |
|-------|-----------|--------|
| Phase 1 | Full project scaffold — frontend + backend structure, routing, config, Docker | ✅ Complete |
| Phase 2 | Complete database layer — models, repositories, schemas, migration, tests | ✅ Complete |
| Phase 3 | JWT auth, scheme CRUD, eligibility engine | ⏳ Next |
| Phase 4 | RAG pipeline, AI chat, multilingual support | ⏳ Planned |
| Phase 5 | Admin panel, analytics, data ingestion | ⏳ Planned |


---

## 3. Live Services Right Now

| Service | URL | Status |
|---------|-----|--------|
| Frontend (Next.js 15) | http://localhost:3001 | ✅ Running |
| Backend (FastAPI) | http://localhost:8000 | ✅ Running |
| App root `GET /` | http://localhost:8000/ | ✅ 200 OK |
| App health `GET /health` | http://localhost:8000/health | ✅ `"status":"healthy"` |
| DB health `GET /api/v1/database/health` | http://localhost:8000/api/v1/database/health | ✅ 503 when DB off / 200 when on |
| Swagger UI | http://localhost:8000/docs | ✅ Live |
| ReDoc | http://localhost:8000/redoc | ✅ Live |

---

## 4. Technology Stack — Full List

### Frontend
| Package | Version | Role |
|---------|---------|------|
| next | 15.1.0 | Framework, App Router, SSR |
| react | 19.0.0 | UI library |
| typescript | 5.7.2 | Strict-mode type safety |
| tailwindcss | 3.4.17 | Utility-first CSS |
| shadcn/ui (Radix) | latest | Accessible UI components |
| @tanstack/react-query | 5.62.7 | Server state, caching |
| zustand | 5.0.2 | Global client state |
| axios | 1.7.9 | HTTP client |
| react-hook-form | 7.54.2 | Form management |
| zod | 3.24.1 | Schema validation |
| @hookform/resolvers | 3.9.1 | Zod ↔ RHF bridge |
| framer-motion | 11.15.0 | Animations |
| next-themes | 0.4.4 | Dark/light/system theme |
| lucide-react | 0.468.0 | Icon library |
| class-variance-authority | 0.7.1 | Component variant styling |
| clsx + tailwind-merge | latest | Safe class merging |


### Backend
| Package | Version | Role |
|---------|---------|------|
| fastapi | 0.115.5 | ASGI web framework |
| uvicorn[standard] | 0.32.1 | ASGI server with hot reload |
| sqlalchemy | 2.0.36 | Async ORM |
| asyncpg | 0.30.0 | Async PostgreSQL driver |
| alembic | 1.14.0 | Database migrations |
| pydantic | 2.10.3 | Data validation |
| pydantic-settings | 2.6.1 | Env-driven Settings class |
| python-dotenv | 1.0.1 | .env file loading |
| passlib[bcrypt] | 1.7.4 | Password hashing (Phase 3) |
| python-jose[cryptography] | 3.3.0 | JWT tokens (Phase 3) |
| httpx | 0.28.1 | Async HTTP client |
| pytest | 8.3.4 | Test framework |
| pytest-asyncio | 0.24.0 | Async test support |

### Infrastructure
| Tool | Role |
|------|------|
| PostgreSQL 16 | Primary relational database |
| Docker + Compose | Containerisation (3 services) |
| Git | Version control |

---

## 5. Complete Directory Tree

```
sahayak-ai/
├── .gitignore
├── README.md
├── docker-compose.yml
│
├── backend/
│   ├── .env
│   ├── .env.example
│   ├── alembic.ini
│   ├── pytest.ini
│   ├── requirements.txt
│   │
│   ├── alembic/
│   │   ├── env.py                        ← Async Alembic runner
│   │   ├── script.py.mako                ← Migration template
│   │   └── versions/
│   │       └── 0001_initial_schema.py    ← First migration (all 5 tables)
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                       ← App factory, middleware, exception handlers
│   │   │
│   │   ├── api/v1/
│   │   │   ├── router.py                 ← Central v1 router
│   │   │   └── endpoints/
│   │   │       └── database.py           ← GET /api/v1/database/health
│   │   │
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   └── dependencies.py           ← Placeholder (Phase 3)
│   │   │
│   │   ├── core/
│   │   │   ├── config.py                 ← Pydantic Settings (all env vars)
│   │   │   ├── exception_handlers.py     ← SQLAlchemy + custom → JSON
│   │   │   ├── exceptions.py             ← Custom exception hierarchy
│   │   │   └── logging.py                ← Structured logging
│   │   │
│   │   ├── database/
│   │   │   └── database.py               ← Engine, session factory, get_db(), check_db_connection()
│   │   │
│   │   ├── middleware/
│   │   │   └── request_logger.py         ← Logs method/path/status/duration
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py               ← Imports all models for Alembic
│   │   │   ├── base.py                   ← UUIDMixin, TimestampMixin
│   │   │   ├── enums.py                  ← All 6 enum types
│   │   │   ├── user.py                   ← User ORM model
│   │   │   ├── profile.py                ← Profile ORM model
│   │   │   ├── scheme.py                 ← Scheme ORM model
│   │   │   ├── eligibility_rule.py       ← EligibilityRule ORM model
│   │   │   └── chat_history.py           ← ChatHistory ORM model
│   │   │
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                   ← BaseRepository[T] generic CRUD
│   │   │   ├── user_repository.py
│   │   │   ├── profile_repository.py
│   │   │   ├── scheme_repository.py
│   │   │   ├── eligibility_repository.py
│   │   │   └── chat_repository.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── common.py                 ← SuccessResponse, ErrorResponse, PaginatedResponse
│   │   │   ├── user.py
│   │   │   ├── profile.py
│   │   │   ├── scheme.py
│   │   │   ├── eligibility_rule.py
│   │   │   └── chat_history.py
│   │   │
│   │   ├── services/
│   │   │   └── __init__.py               ← Placeholder (Phase 3)
│   │   │
│   │   └── utils/
│   │       └── response.py               ← ok() / error() helpers
│   │
│   └── tests/
│       ├── __init__.py
│       └── test_database.py              ← 26 tests, all passing
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.mjs
│   ├── components.json                   ← shadcn/ui config
│   ├── .eslintrc.json
│   ├── .prettierrc
│   ├── .env.example
│   │
│   └── src/
│       ├── app/
│       │   ├── layout.tsx                ← Root HTML, Inter font, metadata, Providers
│       │   ├── page.tsx                  ← Landing page (Hero + Features)
│       │   ├── providers.tsx             ← QueryClient + ThemeProvider
│       │   ├── not-found.tsx             ← Custom 404
│       │   ├── login/page.tsx
│       │   ├── register/page.tsx
│       │   ├── dashboard/page.tsx
│       │   ├── chat/page.tsx
│       │   ├── schemes/page.tsx
│       │   ├── eligibility/page.tsx
│       │   ├── profile/page.tsx
│       │   └── admin/page.tsx
│       │
│       ├── components/
│       │   ├── ui/                       ← Button, Card, Badge, Separator
│       │   ├── layout/                   ← Navbar, Footer, MainLayout
│       │   └── common/                   ← PageHeader, PlaceholderPage
│       │
│       ├── hooks/use-health.ts
│       ├── lib/                          ← utils, constants, axios, queryClient
│       ├── services/                     ← api.service, health.service
│       ├── store/                        ← ui-store, auth-store (Zustand)
│       ├── types/index.ts
│       └── styles/globals.css
│
├── docker/
│   ├── Dockerfile.frontend               ← Multi-stage Next.js build
│   └── Dockerfile.backend                ← Multi-stage FastAPI build
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PROJECT_REPORT.md                 ← Phase 1 report
│   └── FULL_PROJECT_REPORT.md            ← This file
│
└── scripts/
    ├── setup.ps1
    ├── setup.sh
    ├── validate_app.py                   ← Syntax checker (app files only)
    └── validate_syntax.py                ← Full syntax checker
```


---

## 6. Phase 1 — What Was Built (Project Foundation)

### 6.1 Root Structure
- `sahayak-ai/` root with `frontend/`, `backend/`, `docs/`, `docker/`, `scripts/`
- `.gitignore` covering Node, Python, Docker, IDE, env files
- `README.md` with full setup instructions

### 6.2 Backend — FastAPI Foundation
**`app/main.py`** — App factory pattern:
- FastAPI instance with title, version, Swagger/ReDoc URLs
- CORS middleware (origins from env)
- `RequestLoggerMiddleware` (logs every request + duration)
- Lifespan handler (startup/shutdown events)
- `GET /` and `GET /health` endpoints

**`app/core/config.py`** — Pydantic v2 `BaseSettings`:
- Reads from `.env` file and environment variables
- Fields: `APP_NAME`, `APP_VERSION`, `APP_ENV`, `SECRET_KEY`, `DATABASE_URL`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, `DB_POOL_RECYCLE`, `ALLOWED_ORIGINS`, `LOG_LEVEL`
- `@lru_cache` singleton so settings are loaded once

**`app/core/logging.py`** — Structured logging:
- JSON format in production, readable format in development
- Suppresses noisy third-party loggers in production

**`app/database/database.py`** — SQLAlchemy 2.0 async setup:
- `AsyncEngine` with full pool configuration
- `AsyncSessionLocal` session factory
- `get_db()` FastAPI dependency (commit on success, rollback on exception)
- `check_db_connection()` — runs `SELECT 1`
- `init_db()` / `close_db()` lifespan helpers

**`app/middleware/request_logger.py`** — Logs every HTTP request with method, path, status code, duration in ms

**`app/repositories/base.py`** (Phase 1 version) — Placeholder generic repository

**`app/schemas/common.py`** — Response envelopes:
- `SuccessResponse[T]` — wraps all success responses
- `ErrorResponse` — wraps all error responses (RFC 7807 style)
- `PaginationMeta` and `PaginatedResponse[T]`

**`app/utils/response.py`** — `ok()` and `error()` factory helpers

### 6.3 Frontend — Next.js 15 Foundation

**Configuration files:**
- `tsconfig.json` — TypeScript strict mode, path aliases (`@/*`)
- `tailwind.config.ts` — Dark mode via class, Sahayak brand palette, shadcn/ui CSS variable tokens
- `next.config.ts` — React strict mode, image domains, env vars, redirects
- `postcss.config.mjs` — Tailwind + autoprefixer
- `components.json` — shadcn/ui configuration
- `.eslintrc.json` — ESLint with Next.js + TypeScript rules
- `.prettierrc` — Prettier with tailwindcss plugin

**App Router pages (all 9):**
- `/` — Full landing page with Hero section and 3 feature cards
- `/login`, `/register`, `/profile` — Auth placeholders (Phase 3)
- `/dashboard` — Dashboard placeholder (Phase 3)
- `/schemes`, `/eligibility` — Core feature placeholders (Phase 3)
- `/chat` — AI chat placeholder (Phase 4)
- `/admin` — Admin panel placeholder (Phase 5)
- `not-found.tsx` — Custom 404 page

**Layout components:**
- `Navbar.tsx` — Responsive top navigation, dark/light toggle, mobile drawer, auth buttons
- `Footer.tsx` — Site-wide footer with links and branding
- `MainLayout.tsx` — Navbar + main + Footer shell

**UI components (shadcn/ui):**
- `Button` (CVA variants: default, outline, ghost, destructive, secondary, link)
- `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`
- `Badge` (CVA variants)
- `Separator` (Radix primitive)

**State & services:**
- `ui-store.ts` (Zustand) — sidebar, mobile menu, loading overlay
- `auth-store.ts` (Zustand) — user, accessToken, isAuthenticated (placeholder)
- `api.service.ts` — Base GET/POST/PUT/PATCH/DELETE wrappers
- `health.service.ts` — Calls `GET /health`
- `use-health.ts` — TanStack Query hook

**Library files:**
- `utils.ts` — `cn()`, `formatDate()`, `capitalize()`, `sleep()`
- `constants.ts` — `APP_NAME`, `API_URL`, `ROUTES` object
- `axios.ts` — Pre-configured Axios instance with request/response interceptors
- `query-client.ts` — TanStack QueryClient singleton (5min stale, 2 retries)
- `globals.css` — Tailwind base + CSS variables for full light/dark theming

### 6.4 Docker
- `Dockerfile.frontend` — 3-stage build: deps → builder → runner (non-root user, standalone output)
- `Dockerfile.backend` — 2-stage build: builder → runner (non-root user)
- `docker-compose.yml` — 3 services: `frontend`, `backend`, `postgres` with health checks and named volumes

### 6.5 Scripts
- `scripts/setup.ps1` — Windows one-shot setup (installs npm deps + Python venv)
- `scripts/setup.sh` — Linux/macOS equivalent
- `scripts/validate_syntax.py` — AST syntax checker


---

## 7. Phase 2 — What Was Built (Database Layer)

### 7.1 Config Upgrades
Added 4 new fields to `Settings` in `app/core/config.py`:
- `DATABASE_ECHO` — toggle SQL logging independently of APP_ENV
- `DB_POOL_SIZE` — number of persistent connections (default 10)
- `DB_MAX_OVERFLOW` — extra connections above pool_size (default 20)
- `DB_POOL_TIMEOUT` — seconds to wait for a free connection (default 30)
- `DB_POOL_RECYCLE` — recycle connections after N seconds (default 1800)

Updated `.env.example` and `.env` with all new fields.

### 7.2 Database Engine Upgrade (`app/database/database.py`)
Replaced the Phase 1 placeholder with production-ready implementation:
- Engine built from all 5 pool config settings
- `pool_pre_ping=True` — detects stale connections before checkout
- `expire_on_commit=False` — safe for async, objects stay accessible after commit
- `check_db_connection()` — live `SELECT 1` probe, returns `True`/`False`
- `init_db()` — calls `check_db_connection()` at startup, logs warning instead of crashing if DB is down
- `close_db()` — cleanly disposes engine and all pooled connections at shutdown

### 7.3 Enums (`app/models/enums.py`)
6 enum types, all inherit from `str, enum.Enum` (JSON-serializable automatically):

| Enum | Values |
|------|--------|
| `GenderEnum` | male, female, other, prefer_not_to_say |
| `OccupationEnum` | farmer, agricultural_labourer, self_employed, salaried, daily_wage, unemployed, student, homemaker, retired, other |
| `EducationEnum` | no_formal_education, primary, middle, secondary, higher_secondary, graduate, post_graduate, doctorate, other |
| `CategoryEnum` | general, obc, sc, st, ews, other |
| `SchemeCategoryEnum` | agriculture, education, health, housing, women_and_child, social_welfare, financial_inclusion, skill_development, rural_development, pension, insurance, employment, disability, minority, other |
| `LanguageEnum` | en, hi, ta, te, bn, mr, gu, kn, ml, pa, or, as, ur |

### 7.4 ORM Models (SQLAlchemy 2.0 Declarative Mapping)

All models inherit `UUIDMixin` (UUID primary key) + `TimestampMixin` (created_at, updated_at) + `Base`.

**`User` (`users` table)**
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | Auto-generated |
| email | String(255) | Unique, indexed |
| full_name | String(255) | |
| password_hash | String(255) | Nullable (Phase 3) |
| is_active | Boolean | Default true |
| is_verified | Boolean | Default false |
| created_at / updated_at | DateTime(tz) | Auto-managed |

Relationships: `profile` (one-to-one, cascade delete), `chats` (one-to-many, cascade delete)
Indexes: `ix_users_email`, `ix_users_email_is_active`

**`Profile` (`profiles` table)**
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK | → users.id, CASCADE, UNIQUE |
| age | Integer | Nullable |
| gender | GenderEnum | Nullable |
| occupation | OccupationEnum | Nullable |
| annual_income | Integer | Nullable, INR |
| state | String(100) | Nullable, indexed |
| district | String(100) | Nullable |
| education | EducationEnum | Nullable |
| category | CategoryEnum | Nullable, indexed |
| is_farmer | Boolean | Default false |
| is_disabled | Boolean | Default false |

Indexes: `ix_profiles_state_category`, `ix_profiles_income_category`

**`Scheme` (`schemes` table)**
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | String(500) | Indexed |
| description | Text | Nullable |
| benefits | Text | Nullable |
| category | SchemeCategoryEnum | Nullable, indexed |
| state | String(100) | Nullable — NULL = central scheme |
| official_url | String(1000) | Nullable |
| is_active | Boolean | Default true, indexed |

Indexes: `ix_schemes_category_state`, `ix_schemes_name_state`
Relationships: `eligibility_rules` (one-to-many, cascade delete)

**`EligibilityRule` (`eligibility_rules` table)**
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| scheme_id | UUID FK | → schemes.id, CASCADE |
| minimum_age | Integer | Nullable |
| maximum_age | Integer | Nullable |
| maximum_income | Integer | Nullable, INR |
| gender | GenderEnum | Nullable |
| occupation | OccupationEnum | Nullable |
| state | String(100) | Nullable |
| category | CategoryEnum | Nullable |

Indexes: `ix_eligibility_rules_scheme_id`, `ix_eligibility_rules_state_category`

**`ChatHistory` (`chat_history` table)**
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK | → users.id, CASCADE |
| question | Text | User message |
| answer | Text | AI response |
| language | LanguageEnum | Default "en" |

Indexes: `ix_chat_history_user_id`, `ix_chat_history_user_created`


### 7.5 Repository Layer (`app/repositories/`)

**`BaseRepository[T]`** — Generic async CRUD used by all domain repositories:

| Method | Description |
|--------|-------------|
| `get_by_id(uuid)` | Single record by UUID PK |
| `get_by_field(field, value)` | Single record by any column |
| `get_all(skip, limit, filters, order_by)` | Paginated list with optional equality filters |
| `count(filters)` | Row count with optional filters |
| `create(instance)` | Add + flush + refresh — returns DB-generated values |
| `update(instance, data_dict)` | Apply dict of changes + flush + refresh |
| `delete(instance)` | Delete + flush |
| `exists(uuid)` | Boolean existence check |

All methods catch `IntegrityError` and `SQLAlchemyError`, rollback, log, and re-raise.

**`UserRepository`** extends BaseRepository[User]:
- `get_by_email(email)` — case-insensitive lookup
- `email_exists(email)` — boolean check
- `get_active_users(skip, limit)` — only `is_active=True`

**`ProfileRepository`** extends BaseRepository[Profile]:
- `get_by_user_id(user_id)` — one-to-one lookup
- `get_with_user(user_id)` — eager loads User relationship
- `profile_exists_for_user(user_id)` — boolean check

**`SchemeRepository`** extends BaseRepository[Scheme]:
- `get_active_schemes(skip, limit)` — only `is_active=True`, ordered by name
- `get_by_category(category, skip, limit)` — filter by SchemeCategoryEnum
- `get_by_state(state, skip, limit)` — returns state-specific + central (NULL state) schemes
- `get_with_rules(scheme_id)` — eager loads EligibilityRules

**`EligibilityRepository`** extends BaseRepository[EligibilityRule]:
- `get_rules_for_scheme(scheme_id)` — all rules for one scheme
- `delete_rules_for_scheme(scheme_id)` — bulk delete, returns count

**`ChatRepository`** extends BaseRepository[ChatHistory]:
- `get_user_history(user_id, skip, limit)` — newest first, default limit 50
- `count_user_messages(user_id)` — total message count
- `delete_user_history(user_id)` — hard delete all, returns count

### 7.6 Pydantic v2 Schemas (`app/schemas/`)

Each domain has 4 schema classes: `Base`, `Create`, `Update`, `Read` + a `Response` envelope.

**`common.py`** — Reusable wrappers:
- `SuccessResponse[T]` — `{success, message, data}`
- `ErrorResponse` — `{success, message, status_code, errors[]}`
- `ErrorDetail` — `{field?, message}`
- `PaginationMeta` — `{total, page, page_size, total_pages}`
- `PaginatedResponse[T]` — `{success, data[], meta}`

**`user.py`** — `UserCreate` requires email (regex validated), full_name, password (min 8 chars). `UserRead` never exposes password_hash.

**`profile.py`** — Validates Indian state names against full list of 36 states/UTs. Age 0–150. Income ≥ 0.

**`scheme.py`** — Name min 3 chars. URL max 1000 chars.

**`eligibility_rule.py`** — Cross-field validator: `minimum_age` cannot exceed `maximum_age`.

**`chat_history.py`** — question and answer required, language defaults to English.

### 7.7 Exception System (`app/core/`)

**`exceptions.py`** — Custom hierarchy:
```
SahayakBaseException (500)
├── ValidationException (400)
├── DuplicateEmailException (409)
├── DuplicateResourceException (409)
├── IntegrityException (409)
├── NotFoundException (404)
│   ├── UserNotFoundException (404)
│   ├── ProfileNotFoundException (404)
│   └── SchemeNotFoundException (404)
├── DatabaseUnavailableException (503)
└── ConnectionTimeoutException (504)
```

**`exception_handlers.py`** — Registered in `main.py`, converts every exception type to clean JSON:
- `SahayakBaseException` → uses `exc.status_code` and `exc.message`
- `sqlalchemy.exc.IntegrityError` → inspects error text, returns 409 with specific message (email duplicate, FK violation, not-null)
- `sqlalchemy.exc.OperationalError` → 503 database unavailable
- `sqlalchemy.exc.TimeoutError` → 504 connection timeout
- `Exception` (catch-all) → 500 unexpected error

### 7.8 Database Health Endpoint (`app/api/v1/endpoints/database.py`)

`GET /api/v1/database/health`
- Calls `check_db_connection()` (live `SELECT 1`)
- Returns `200 {"success":true, "database":"connected"}` when PostgreSQL is reachable
- Returns `503 {"success":false, "database":"unavailable"}` when not reachable
- Used by load balancers, Docker healthchecks, monitoring dashboards

### 7.9 Alembic Migration Setup

**`alembic/env.py`** (updated):
- Imports all models via `import app.models` before running
- Injects `DATABASE_URL` from settings at runtime
- `compare_type=True` — detects column type changes
- `compare_server_default=True` — detects default value changes
- Uses `NullPool` for migrations (no connection reuse)

**`alembic/script.py.mako`** — Migration file template

**`alembic/versions/0001_initial_schema.py`** — First migration:
- Creates 6 PostgreSQL ENUM types (with `checkfirst=True`)
- Creates all 5 tables in dependency order: `users` → `profiles` → `schemes` → `eligibility_rules` → `chat_history`
- Creates all indexes defined in the ORM models
- `downgrade()` drops tables in reverse order, then drops all ENUM types

### 7.10 Tests (`tests/test_database.py`)

**26 tests, all passing, 0.77 seconds:**

| Category | Tests | Count |
|----------|-------|-------|
| Model instantiation | User, Profile, Scheme, EligibilityRule, ChatHistory | 5 |
| Schema validation — valid | UserCreate, SchemeCreate | 2 |
| Schema validation — invalid | bad email, short password, negative age, fake state, age range | 5 |
| Enum | All 6 enums importable and correct values | 1 |
| Config | Settings load, DB URL format | 2 |
| DB connectivity | Mocked success, mocked OperationalError | 2 |
| Repository methods | BaseRepo 8 methods, User 2, Profile 2, Scheme 4, Chat 3 | 5 |
| Exception hierarchy | Inheritance chain, status codes, message override | 2 |
| API structure | Database router path, v1 router includes database | 2 |


---

## 8. Architecture — How Everything Connects

### 8.1 Request Flow
```
Browser
  └── Next.js Page
        └── TanStack Query (useQuery/useMutation)
              └── Service module (e.g. health.service.ts)
                    └── Axios instance (src/lib/axios.ts)
                          └── HTTP → FastAPI (port 8000)
                                ├── CORSMiddleware
                                ├── RequestLoggerMiddleware
                                └── Route Handler (thin)
                                      └── Service Layer (Phase 3)
                                            └── Repository Layer
                                                  └── AsyncSession → PostgreSQL
```

### 8.2 Backend Layer Responsibilities

| Layer | Location | What it does |
|-------|----------|-------------|
| Routes | `api/v1/endpoints/` | HTTP in/out — validation, status codes only |
| Services | `services/` | Business logic, orchestration (Phase 3+) |
| Repositories | `repositories/` | All SQL — zero business logic |
| Models | `models/` | Table definitions, relationships |
| Schemas | `schemas/` | Request/response contracts |
| Core | `core/` | Config, logging, exceptions |
| Database | `database/` | Engine, session, connectivity |

### 8.3 How PostgreSQL Connects (when you run it)

1. Set `DATABASE_URL` in `backend/.env`
2. `Settings` reads it via Pydantic Settings
3. `_build_engine()` creates `AsyncEngine` — no connection opened yet
4. `init_db()` runs `check_db_connection()` → logs status
5. On first real request, engine opens connection from pool
6. `Depends(get_db)` injects `AsyncSession` per HTTP request
7. Session commits on success, rolls back on any exception, always closes
8. `alembic upgrade head` creates all tables before first boot

### 8.4 Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| Repository Pattern | `repositories/` | Isolates SQL — services never write queries |
| Generic Repository | `BaseRepository[T]` | DRY CRUD — domain repos inherit and extend |
| Dependency Injection | FastAPI `Depends()` | DB session, auth injected into routes |
| Settings Singleton | `@lru_cache` | Env loaded once, shared everywhere |
| Response Envelope | `SuccessResponse[T]` | Frontend always knows response shape |
| App Factory | `create_application()` | Testable — app creation separated from running |
| Provider Pattern | `providers.tsx` | All React context in one place |
| Zustand Slices | `ui-store`, `auth-store` | Separate concerns, no god store |
| CVA Variants | `button.tsx` | Type-safe component variants |

---

## 9. Environment Variables — Full Reference

### Backend (`backend/.env`)
| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | Sahayak AI | Application name |
| `APP_VERSION` | 0.1.0 | Semantic version |
| `APP_ENV` | development | development / staging / production |
| `LOG_LEVEL` | INFO | DEBUG / INFO / WARNING / ERROR |
| `SECRET_KEY` | change-me | JWT signing secret (Phase 3) |
| `ALGORITHM` | HS256 | JWT algorithm (Phase 3) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | JWT TTL (Phase 3) |
| `DATABASE_URL` | postgresql+asyncpg://... | Full asyncpg connection string |
| `DATABASE_ECHO` | false | Log every SQL statement |
| `DB_POOL_SIZE` | 10 | Persistent connection pool size |
| `DB_MAX_OVERFLOW` | 20 | Extra connections above pool_size |
| `DB_POOL_TIMEOUT` | 30 | Seconds to wait for free connection |
| `DB_POOL_RECYCLE` | 1800 | Recycle connections after 30 min |
| `ALLOWED_ORIGINS` | ["http://localhost:3000"] | CORS allowed origins |

### Frontend (`frontend/.env.local`)
| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | http://localhost:8000 | Backend URL |
| `NEXT_PUBLIC_API_VERSION` | v1 | API version prefix |
| `NEXT_PUBLIC_APP_NAME` | Sahayak AI | App display name |
| `NEXT_PUBLIC_APP_VERSION` | 0.1.0 | Version shown in footer |
| `NEXT_PUBLIC_ENABLE_CHAT` | false | Feature flag for chat |
| `NEXT_PUBLIC_ENABLE_VOICE` | false | Feature flag for voice |

---

## 10. Verification Results

| Check | Result |
|-------|--------|
| Python AST syntax check — 45 app files | ✅ ALL PASSED |
| Backend startup — no errors | ✅ Application startup complete |
| DB missing at startup — graceful warning | ✅ Warning logged, app still runs |
| `GET /` | ✅ 200 `{"success":true}` |
| `GET /health` | ✅ 200 `{"status":"healthy"}` |
| `GET /api/v1/database/health` (no DB) | ✅ 503 `{"database":"unavailable"}` |
| `GET /api/v1/database/health` (with DB) | ✅ 200 `{"database":"connected"}` |
| 26 pytest tests | ✅ 26 passed, 0 failed, 0.77s |
| Frontend `npm install` | ✅ 453 packages |
| Frontend Next.js 15 startup | ✅ Ready in 1738ms |
| Frontend `GET http://localhost:3001` | ✅ 200 OK |

---

## 11. What Is NOT Implemented Yet

| Feature | Phase |
|---------|-------|
| JWT authentication | Phase 3 |
| User registration / login API | Phase 3 |
| Password hashing | Phase 3 |
| Protected routes / role-based access | Phase 3 |
| Scheme CRUD API endpoints | Phase 3 |
| Eligibility engine | Phase 3 |
| User dashboard data | Phase 3 |
| AI / LLM integration | Phase 4 |
| RAG pipeline (pgvector + embeddings) | Phase 4 |
| Multilingual support (i18n) | Phase 4 |
| AI chat interface | Phase 4 |
| Voice input | Phase 4 |
| Admin panel logic | Phase 5 |
| Analytics dashboard | Phase 5 |
| Scheme data ingestion pipeline | Phase 5 |
| PWA / offline support | Phase 6 |

---

## 12. Commands to Resume Development

### Start backend (dev)
```bash
cd backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start frontend (dev)
```bash
cd frontend
npm run dev
```

### Set up PostgreSQL then run migrations
```bash
# Start PostgreSQL (Docker)
docker run -d --name sahayak_postgres \
  -e POSTGRES_USER=sahayak \
  -e POSTGRES_PASSWORD=sahayak_password \
  -e POSTGRES_DB=sahayak_db \
  -p 5432:5432 postgres:16-alpine

# Apply migration
cd backend
alembic upgrade head

# Verify DB health endpoint returns connected
curl http://localhost:8000/api/v1/database/health
```

### Run tests
```bash
cd backend
.venv\Scripts\pytest tests/ -v
```

### Add a new model (Phase 3 workflow)
```bash
# 1. Create app/models/your_model.py
# 2. Import in app/models/__init__.py
# 3. Generate migration
alembic revision --autogenerate -m "add your_model"
# 4. Review alembic/versions/<id>_add_your_model.py
# 5. Apply
alembic upgrade head
```

### Full stack with Docker
```bash
docker compose up --build
```

---

## 13. Key File Locations Quick Reference

| Task | File |
|------|------|
| Add a new API route | `backend/app/api/v1/router.py` + new file in `endpoints/` |
| Change any config | `backend/app/core/config.py` + `backend/.env` |
| Add a new ORM model | `backend/app/models/new_model.py` + register in `__init__.py` |
| Add Pydantic schema | `backend/app/schemas/new_schema.py` + register in `__init__.py` |
| Add business logic | `backend/app/services/` |
| Add DB queries | `backend/app/repositories/` |
| Add a new exception type | `backend/app/core/exceptions.py` |
| Add a new page | `frontend/src/app/<route>/page.tsx` |
| Add a UI component | `frontend/src/components/` |
| Add an API service | `frontend/src/services/` |
| Add global state | `frontend/src/store/` |
| Change theme colours | `frontend/src/styles/globals.css` |
| Change brand tokens | `frontend/tailwind.config.ts` |

---

*End of Report — Phase 1 + Phase 2 Complete*
*Next: Phase 3 — JWT Authentication + Scheme CRUD API*
