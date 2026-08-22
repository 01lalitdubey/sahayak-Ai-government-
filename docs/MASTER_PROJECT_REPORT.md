# Sahayak AI — Master Project Report
**Date:** August 2, 2026
**Status:** Phase 1 + Phase 2 + Phase 3.1 (Backend Auth) + Phase 3.2 (Frontend Auth) — ALL COMPLETE
**Purpose:** Complete handoff document for continued development

---

## 1. What Is Sahayak AI

A **multilingual AI-powered web application** for rural Indian citizens to:
- Discover central and state government schemes and subsidies
- Check personal eligibility for those schemes
- Get plain-language AI explanations
- Interact in Hindi, Tamil, Telugu, Bengali, Marathi, and more

**Two independent services:**
- **Frontend** — Next.js 15, React 19, TypeScript, Tailwind, shadcn/ui
- **Backend** — FastAPI, Python 3.12, SQLAlchemy 2.0, PostgreSQL, JWT

---

## 2. Overall Progress

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Full project scaffold — frontend + backend + Docker | ✅ Complete |
| Phase 2 | PostgreSQL database layer — 5 models, repositories, schemas, migration | ✅ Complete |
| Phase 3.1 | Backend JWT authentication — register, login, refresh, logout, /me | ✅ Complete |
| Phase 3.2 | Frontend authentication — login page, register page, auth store, protected routes | ✅ Complete |
| Phase 4 | Scheme CRUD API + Eligibility engine | ⏳ Next |
| Phase 5 | RAG pipeline + AI chat + multilingual | ⏳ Planned |
| Phase 6 | Admin panel + analytics | ⏳ Planned |

---

## 3. Live Services

| Service | URL | Status |
|---------|-----|--------|
| Frontend (Next.js 15) | http://localhost:3001 | ✅ Running |
| Backend (FastAPI) | http://localhost:8000 | ✅ Running |
| GET / | http://localhost:8000/ | ✅ 200 |
| GET /health | http://localhost:8000/health | ✅ healthy |
| GET /api/v1/database/health | http://localhost:8000/api/v1/database/health | ✅ 503 (no DB) → 200 (with DB) |
| POST /api/v1/auth/register | http://localhost:8000/api/v1/auth/register | ✅ Live |
| POST /api/v1/auth/login | http://localhost:8000/api/v1/auth/login | ✅ Live |
| POST /api/v1/auth/refresh | http://localhost:8000/api/v1/auth/refresh | ✅ Live |
| POST /api/v1/auth/logout | http://localhost:8000/api/v1/auth/logout | ✅ Live |
| GET /api/v1/auth/me | http://localhost:8000/api/v1/auth/me | ✅ Live |
| Swagger UI | http://localhost:8000/docs | ✅ Bearer auth button |
| Frontend /login | http://localhost:3001/login | ✅ Full form |
| Frontend /register | http://localhost:3001/register | ✅ Full form |
| Frontend /dashboard | http://localhost:3001/dashboard | ✅ Protected |
| Frontend /profile | http://localhost:3001/profile | ✅ Protected + /me |


---

## 4. Full Technology Stack

### Frontend
| Package | Version | Role |
|---------|---------|------|
| next | 15.1.0 | App Router, SSR, image optimization |
| react | 19.0.0 | UI library |
| typescript | 5.7.2 | Strict-mode type safety |
| tailwindcss | 3.4.17 | Utility-first CSS |
| shadcn/ui (Radix) | latest | Accessible UI components |
| @tanstack/react-query | 5.62.7 | Server state, caching |
| zustand | 5.0.2 | Global auth + UI state |
| axios | 1.7.9 | HTTP client with interceptors |
| react-hook-form | 7.54.2 | Form state management |
| zod | 3.24.1 | Schema validation |
| @hookform/resolvers | 3.9.1 | Zod ↔ RHF bridge |
| framer-motion | 11.15.0 | Animations |
| next-themes | 0.4.4 | Dark/light/system theme |
| lucide-react | 0.468.0 | Icons |
| @radix-ui/react-checkbox | 1.3.11 | Accessible checkbox |
| @radix-ui/react-label | 2.1.15 | Accessible label |

### Backend
| Package | Version | Role |
|---------|---------|------|
| fastapi | 0.115.5 | ASGI web framework |
| uvicorn[standard] | 0.32.1 | ASGI server |
| sqlalchemy | 2.0.36 | Async ORM |
| asyncpg | 0.30.0 | Async PostgreSQL driver |
| alembic | 1.14.0 | Database migrations |
| pydantic | 2.10.3 | Data validation |
| pydantic-settings | 2.6.1 | Env-driven settings |
| python-jose[cryptography] | 3.3.0 | JWT tokens |
| bcrypt | 5.0.0 | Password hashing |
| passlib | 1.7.4 | (installed, bcrypt used directly) |
| pytest | 8.3.4 | Test framework |
| pytest-asyncio | 0.24.0 | Async tests |

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
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       ├── 0001_initial_schema.py        ← All 5 tables + 6 enums
│   │       └── 0002_add_user_role_last_login.py  ← role + last_login_at
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                           ← App factory, all middleware + exception handlers
│   │   │
│   │   ├── api/v1/
│   │   │   ├── router.py                     ← database + auth routers registered
│   │   │   └── endpoints/
│   │   │       ├── database.py               ← GET /api/v1/database/health
│   │   │       └── auth.py                   ← 5 auth endpoints
│   │   │
│   │   ├── auth/
│   │   │   ├── token.py                      ← create/verify/decode access + refresh tokens
│   │   │   ├── password.py                   ← bcrypt hash/verify + strength validation
│   │   │   └── dependencies.py               ← get_current_user, get_current_active_user, require_role, require_admin
│   │   │
│   │   ├── core/
│   │   │   ├── config.py                     ← All settings + REFRESH_TOKEN_EXPIRE_DAYS
│   │   │   ├── exceptions.py                 ← Full hierarchy incl. auth exceptions
│   │   │   ├── exception_handlers.py         ← Global JSON error conversion
│   │   │   └── logging.py
│   │   │
│   │   ├── database/
│   │   │   └── database.py                   ← Async engine, session, check_db_connection()
│   │   │
│   │   ├── middleware/
│   │   │   └── request_logger.py
│   │   │
│   │   ├── models/
│   │   │   ├── enums.py                      ← GenderEnum, OccupationEnum, EducationEnum,
│   │   │   │                                    CategoryEnum, SchemeCategoryEnum,
│   │   │   │                                    LanguageEnum, UserRole
│   │   │   ├── user.py                       ← + role + last_login_at columns
│   │   │   ├── profile.py
│   │   │   ├── scheme.py
│   │   │   ├── eligibility_rule.py
│   │   │   └── chat_history.py
│   │   │
│   │   ├── repositories/
│   │   │   ├── base.py                       ← BaseRepository[T] — 8 CRUD methods
│   │   │   ├── user_repository.py            ← + create_user, authenticate_user, update_last_login
│   │   │   ├── profile_repository.py
│   │   │   ├── scheme_repository.py
│   │   │   ├── eligibility_repository.py
│   │   │   └── chat_repository.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── common.py
│   │   │   ├── auth.py                       ← RegisterRequest/Response, LoginRequest/Response,
│   │   │   │                                    RefreshRequest/Response, CurrentUserResponse,
│   │   │   │                                    LogoutResponse, AuthUserData
│   │   │   ├── user.py
│   │   │   ├── profile.py
│   │   │   ├── scheme.py
│   │   │   ├── eligibility_rule.py
│   │   │   └── chat_history.py
│   │   │
│   │   ├── services/
│   │   │   └── auth_service.py               ← AuthService: register, login, refresh, get_user_by_id
│   │   │
│   │   └── utils/
│   │       └── response.py
│   │
│   └── tests/
│       ├── test_database.py                  ← 26 tests
│       └── test_auth.py                      ← 42 tests
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── components.json
│   ├── .eslintrc.json
│   ├── .prettierrc
│   │
│   └── src/
│       ├── __tests__/
│       │   └── auth.test.ts                  ← Frontend auth tests
│       │
│       ├── app/
│       │   ├── layout.tsx                    ← Root HTML + Inter font + Providers
│       │   ├── page.tsx                      ← Landing page
│       │   ├── providers.tsx                 ← QueryClient + Theme + AuthProvider
│       │   ├── not-found.tsx
│       │   ├── login/page.tsx                ← Two-panel login with GuestRoute + LoginForm
│       │   ├── register/page.tsx             ← Two-panel register with GuestRoute + RegisterForm
│       │   ├── dashboard/page.tsx            ← Protected + personalised welcome
│       │   ├── profile/page.tsx              ← Protected + connected to GET /me
│       │   ├── chat/page.tsx
│       │   ├── schemes/page.tsx
│       │   ├── eligibility/page.tsx
│       │   └── admin/page.tsx
│       │
│       ├── components/
│       │   ├── auth/
│       │   │   ├── AuthProvider.tsx          ← Restores session on mount
│       │   │   ├── LoadingScreen.tsx         ← Animated full-screen loader
│       │   │   ├── LoginForm.tsx             ← RHF + Zod + show/hide + remember me
│       │   │   ├── RegisterForm.tsx          ← RHF + Zod + strength bar + success anim
│       │   │   ├── ProtectedRoute.tsx        ← Redirects unauthenticated to /login
│       │   │   └── GuestRoute.tsx            ← Redirects authenticated to /dashboard
│       │   ├── common/
│       │   │   ├── PageHeader.tsx
│       │   │   └── PlaceholderPage.tsx
│       │   ├── layout/
│       │   │   ├── Navbar.tsx                ← Auth-aware: guest vs logged-in vs admin
│       │   │   ├── Footer.tsx
│       │   │   └── MainLayout.tsx
│       │   └── ui/
│       │       ├── alert.tsx
│       │       ├── badge.tsx
│       │       ├── button.tsx
│       │       ├── card.tsx
│       │       ├── checkbox.tsx
│       │       ├── input.tsx
│       │       ├── label.tsx
│       │       ├── separator.tsx
│       │       └── skeleton.tsx
│       │
│       ├── hooks/
│       │   ├── use-auth.ts                   ← isAdmin, isSuperAdmin, hasRole(), hasAnyRole()
│       │   └── use-health.ts
│       │
│       ├── lib/
│       │   ├── axios.ts                      ← Bearer injection + 401→refresh→retry
│       │   ├── constants.ts
│       │   ├── query-client.ts
│       │   ├── token-storage.ts              ← localStorage read/write (SSR-safe)
│       │   └── utils.ts
│       │
│       ├── services/
│       │   ├── api.service.ts
│       │   ├── auth.service.ts               ← register, login, refresh, logout, me
│       │   └── health.service.ts
│       │
│       ├── store/
│       │   ├── auth-store.ts                 ← login, logout, refresh, restoreSession, clearSession, updateUser
│       │   └── ui-store.ts
│       │
│       ├── types/
│       │   ├── auth.ts                       ← AuthUser, UserRole, all request/response types, TOKEN_KEYS
│       │   └── index.ts
│       │
│       └── styles/
│           └── globals.css
│
├── docker/
│   ├── Dockerfile.frontend
│   └── Dockerfile.backend
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PROJECT_REPORT.md
│   ├── FULL_PROJECT_REPORT.md
│   └── MASTER_PROJECT_REPORT.md              ← This file
│
└── scripts/
    ├── setup.ps1
    ├── setup.sh
    ├── validate_app.py
    └── validate_syntax.py
```


---

## 6. Phase 1 — Project Foundation (What Was Built)

### Backend
- FastAPI app factory with CORS, request logger middleware, lifespan handler
- `GET /` and `GET /health` endpoints
- Pydantic v2 Settings — reads all env vars from `.env`, `@lru_cache` singleton
- Structured logging (JSON in prod, readable in dev)
- SQLAlchemy 2.0 async engine + session factory + `get_db()` dependency
- Repository pattern placeholder
- Response envelopes: `SuccessResponse[T]`, `ErrorResponse`, `PaginatedResponse[T]`
- Docker — multi-stage Dockerfiles for frontend and backend, docker-compose with 3 services

### Frontend
- 9 pages (/, /login, /register, /dashboard, /chat, /schemes, /eligibility, /profile, /admin)
- Navbar, Footer, MainLayout
- shadcn/ui: Button, Card, Badge, Separator
- Zustand UI store (sidebar, mobile menu)
- TanStack Query setup
- Axios instance (placeholder interceptors)
- Tailwind with dark/light CSS variable theming + Sahayak brand palette
- Inter font, full SEO metadata

---

## 7. Phase 2 — Database Layer (What Was Built)

### Config additions
- `DATABASE_ECHO`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, `DB_POOL_RECYCLE`

### Database engine
- Full pool config (size 10, overflow 20, timeout 30s, recycle 1800s, pre-ping)
- `check_db_connection()` — live SELECT 1
- `init_db()` — probes on startup, warns gracefully if DB is down

### Enums (6 total)
`GenderEnum`, `OccupationEnum`, `EducationEnum`, `CategoryEnum`, `SchemeCategoryEnum`, `LanguageEnum`

### ORM Models (5 tables)

| Model | Key columns | Relationships |
|-------|-------------|---------------|
| User | email (unique), full_name, password_hash, role, is_active, is_verified, last_login_at | → Profile (1:1), → ChatHistory (1:many) |
| Profile | user_id FK, age, gender, occupation, annual_income, state, district, education, category, is_farmer, is_disabled | → User |
| Scheme | name, description, benefits, category, state (NULL=central), official_url, is_active | → EligibilityRules |
| EligibilityRule | scheme_id FK, min_age, max_age, max_income, gender, occupation, state, category | → Scheme |
| ChatHistory | user_id FK, question, answer, language | → User |

### Repositories

**BaseRepository[T]** — 8 generic async methods: `get_by_id`, `get_by_field`, `get_all`, `count`, `create`, `update`, `delete`, `exists`

| Repository | Domain methods |
|-----------|---------------|
| UserRepository | `get_by_email`, `email_exists`, `get_active_users`, `create_user`, `authenticate_user`, `update_last_login` |
| ProfileRepository | `get_by_user_id`, `get_with_user`, `profile_exists_for_user` |
| SchemeRepository | `get_active_schemes`, `get_by_category`, `get_by_state`, `get_with_rules` |
| EligibilityRepository | `get_rules_for_scheme`, `delete_rules_for_scheme` |
| ChatRepository | `get_user_history`, `count_user_messages`, `delete_user_history` |

### Pydantic v2 Schemas
- Each domain: `Create`, `Update`, `Read`, `Response`
- `UserCreate` — email regex, min 8 char password, hash never exposed
- `ProfileCreate` — validates all 36 Indian states/UTs
- `EligibilityRuleCreate` — cross-field: min_age ≤ max_age

### Exception System
```
SahayakBaseException (500)
├── ValidationException (400)
├── DuplicateEmailException (409)
├── IntegrityException (409)
├── NotFoundException (404)
│   ├── UserNotFoundException
│   ├── ProfileNotFoundException
│   └── SchemeNotFoundException
├── DatabaseUnavailableException (503)
├── ConnectionTimeoutException (504)
├── UnauthorisedException (401)          ← Phase 3
├── InvalidCredentialsException (401)    ← Phase 3
├── InvalidTokenException (401)          ← Phase 3
├── ExpiredTokenException (401)          ← Phase 3
├── TokenMissingException (401)          ← Phase 3
├── ForbiddenException (403)             ← Phase 3
└── InactiveUserException (403)          ← Phase 3
```

### Migrations
- `0001_initial_schema.py` — all 6 ENUMs + all 5 tables + all indexes
- `0002_add_user_role_last_login.py` — role column + last_login_at + user_role_enum

### Database health endpoint
`GET /api/v1/database/health` — live SELECT 1 → 200 connected / 503 unavailable

### Tests: **26 passed**

---

## 8. Phase 3.1 — Backend Authentication (What Was Built)

### New files
| File | Purpose |
|------|---------|
| `app/auth/token.py` | `create_access_token()`, `create_refresh_token()`, `decode_token()`, `verify_access_token()`, `verify_refresh_token()`, `extract_user_id()` |
| `app/auth/password.py` | `hash_password()`, `verify_password()` via bcrypt directly, `validate_password_strength()` (8+ chars, upper, lower, digit, special) |
| `app/auth/dependencies.py` | `get_current_user()`, `get_current_active_user()`, `require_role()`, `require_admin` — FastAPI Depends() guards |
| `app/schemas/auth.py` | All auth request/response schemas |
| `app/services/auth_service.py` | `AuthService` — register, login, refresh, get_user_by_id |
| `app/api/v1/endpoints/auth.py` | 5 thin route handlers |

### Auth endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/auth/register | Register — validates strength, checks duplicate, hashes, issues tokens |
| POST | /api/v1/auth/login | Login — verifies credentials, records last_login_at, issues tokens |
| POST | /api/v1/auth/refresh | Exchange refresh token for new token pair (rotation) |
| POST | /api/v1/auth/logout | Stateless logout — client discards tokens |
| GET | /api/v1/auth/me | Return current user from Bearer token |

### JWT design
- Access token: 30 min, carries `sub` (user UUID) + `role` + `type=access`
- Refresh token: 7 days, carries `sub` + `type=refresh` only
- Both signed with `SECRET_KEY` using HS256
- `type` claim prevents token substitution attacks

### Password security
- bcrypt with 12 rounds (OWASP minimum)
- Rules: 8+ chars, uppercase, lowercase, digit, special character
- Plain text never stored, never logged, never returned in any response

### Role-based access
- `UserRole` enum: `user`, `admin`, `super_admin`
- `require_role(*roles)` factory — reusable for any protected endpoint
- `require_admin` = shortcut for admin + super_admin

### Swagger
- OAuth2PasswordBearer scheme registered
- Authorize button visible in /docs
- `persistAuthorization: true` — token survives page refresh in Swagger

### Tests: **42 passed** (68 total with Phase 2)

---

## 9. Phase 3.2 — Frontend Authentication (What Was Built)

### New files
| File | Purpose |
|------|---------|
| `types/auth.ts` | `AuthUser`, `UserRole`, all request/response types, `TOKEN_KEYS` |
| `lib/token-storage.ts` | SSR-safe localStorage for tokens + user — single source of truth |
| `services/auth.service.ts` | Typed HTTP calls to all 5 auth endpoints |
| `hooks/use-auth.ts` | `isAdmin`, `isSuperAdmin`, `hasRole()`, `hasAnyRole()` — components use this, not the store directly |
| `components/auth/AuthProvider.tsx` | Restores session on app mount, shows LoadingScreen while checking |
| `components/auth/LoadingScreen.tsx` | Animated full-screen loader with pulsing brand icon |
| `components/auth/LoginForm.tsx` | RHF + Zod, show/hide password, remember me, server error display, Framer Motion |
| `components/auth/RegisterForm.tsx` | RHF + Zod, password strength bar (5-level), success animation, terms checkbox |
| `components/auth/ProtectedRoute.tsx` | Redirects unauthenticated to `/login?redirect=<path>`, optional role enforcement |
| `components/auth/GuestRoute.tsx` | Redirects authenticated users to /dashboard from login/register |
| `components/ui/input.tsx` | shadcn Input |
| `components/ui/label.tsx` | Radix Label |
| `components/ui/checkbox.tsx` | Radix Checkbox |
| `components/ui/alert.tsx` | Alert + AlertDescription for errors |
| `components/ui/skeleton.tsx` | Loading skeleton |

### Modified files
| File | What changed |
|------|-------------|
| `lib/axios.ts` | Real Bearer token injection + 401→refresh→retry queue + redirect on refresh failure |
| `store/auth-store.ts` | Full production store — login, logout, refresh, restoreSession, clearSession, updateUser |
| `app/providers.tsx` | Added AuthProvider inside ThemeProvider |
| `app/login/page.tsx` | Two-panel layout with GuestRoute + LoginForm |
| `app/register/page.tsx` | Two-panel layout with GuestRoute + RegisterForm |
| `app/profile/page.tsx` | Protected + connected to GET /me, shows name/email/role/status/dates |
| `app/dashboard/page.tsx` | Protected + personalised welcome |
| `components/layout/Navbar.tsx` | Auth-aware — guest shows Sign in/Get started, logged-in shows avatar/logout, admin sees Admin link |

### Complete Authentication Flow
```
PAGE LOAD
  AuthProvider mounts → restoreSession()
    1. Read token from localStorage
    2. GET /api/v1/auth/me with token
       → 200: set user in Zustand, render app
       → 401: POST /api/v1/auth/refresh
           → success: retry /me, set user, render app
           → fail: clearAll(), show app unauthenticated

LOGIN
  User fills LoginForm → submit → authService.login()
    POST /api/v1/auth/login
    → store access_token + refresh_token + user in localStorage
    → set Zustand state (isAuthenticated=true)
    → redirect to /dashboard (or ?redirect= param)

REGISTER
  User fills RegisterForm → submit → authService.register()
    POST /api/v1/auth/register
    → success animation → auto-login → redirect /dashboard

PROTECTED API CALL (any 401)
  axios interceptor fires:
    POST /api/v1/auth/refresh with stored refresh_token
    → success: update tokens, retry original request
    → fail: clearAll() → redirect /login?session=expired
    Queue: concurrent 401s wait for one refresh, then all retry

LOGOUT
  Navbar sign out → authService.logout() (server-side, best effort)
  → clearAll() (localStorage + Zustand)
  → redirect /login

ROUTE PROTECTION
  ProtectedRoute: if not authenticated → /login?redirect=<path>
  GuestRoute: if authenticated → /dashboard
  require_role(UserRole.ADMIN): if wrong role → /dashboard
```

---

## 10. Test Results

### Backend
```
tests/test_database.py    26 passed  — Models, schemas, repositories, config, DB connectivity
tests/test_auth.py        42 passed  — Passwords, tokens, schemas, auth service, endpoints, roles
──────────────────────────────────────
TOTAL                     68 passed  0 failed   exit code 0
```

### Frontend
```
Build: npm run build
✓ Compiled successfully
✓ Linting and checking validity of types
✓ 12 routes — 0 errors, 0 warnings
```

---

## 11. Environment Variables — Full Reference

### Backend (`backend/.env`)
| Variable | Default | Purpose |
|----------|---------|---------|
| APP_NAME | Sahayak AI | Display name |
| APP_VERSION | 0.1.0 | Semantic version |
| APP_ENV | development | development / staging / production |
| LOG_LEVEL | INFO | DEBUG / INFO / WARNING / ERROR |
| SECRET_KEY | change-me | JWT signing key (generate with `secrets.token_hex(32)`) |
| ALGORITHM | HS256 | JWT algorithm |
| ACCESS_TOKEN_EXPIRE_MINUTES | 30 | Access token TTL |
| REFRESH_TOKEN_EXPIRE_DAYS | 7 | Refresh token TTL |
| DATABASE_URL | postgresql+asyncpg://... | asyncpg connection string |
| DATABASE_ECHO | false | SQL statement logging |
| DB_POOL_SIZE | 10 | Persistent connections |
| DB_MAX_OVERFLOW | 20 | Extra connections above pool |
| DB_POOL_TIMEOUT | 30 | Seconds to wait for connection |
| DB_POOL_RECYCLE | 1800 | Recycle after 30 min |
| ALLOWED_ORIGINS | ["http://localhost:3000"] | CORS allowed origins |

### Frontend (`frontend/.env.local`)
| Variable | Default | Purpose |
|----------|---------|---------|
| NEXT_PUBLIC_API_BASE_URL | http://localhost:8000 | Backend URL |
| NEXT_PUBLIC_API_VERSION | v1 | API version prefix |
| NEXT_PUBLIC_APP_NAME | Sahayak AI | App display name |
| NEXT_PUBLIC_APP_VERSION | 0.1.0 | Version in footer |
| NEXT_PUBLIC_ENABLE_CHAT | false | Feature flag |
| NEXT_PUBLIC_ENABLE_VOICE | false | Feature flag |

---

## 12. What Is NOT Implemented Yet

| Feature | Phase |
|---------|-------|
| Scheme CRUD API (backend) | Phase 4 |
| Eligibility engine (backend) | Phase 4 |
| User management API | Phase 4 |
| Dashboard with real data | Phase 4 |
| AI / LLM integration | Phase 5 |
| RAG pipeline (pgvector + embeddings) | Phase 5 |
| Multilingual support (i18n) | Phase 5 |
| AI chat interface | Phase 5 |
| Voice input | Phase 5 |
| Admin panel | Phase 6 |
| Analytics | Phase 6 |
| Email verification | Phase 4 |
| Forgot password / reset | Phase 4 |
| OAuth (Google, etc.) | Phase 4 |
| PWA / offline | Phase 7 |

---

## 13. Commands to Continue Development

### Start backend
```bash
cd backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start frontend
```bash
cd frontend
npm run dev
```

### Set up PostgreSQL + run migrations
```bash
# Start PostgreSQL (Docker)
docker run -d --name sahayak_postgres \
  -e POSTGRES_USER=sahayak \
  -e POSTGRES_PASSWORD=sahayak_password \
  -e POSTGRES_DB=sahayak_db \
  -p 5432:5432 postgres:16-alpine

cd backend
alembic upgrade head
```

### Run backend tests
```bash
cd backend
.venv\Scripts\pytest tests/ -v
```

### Build frontend
```bash
cd frontend
npm run build
```

### Full stack Docker
```bash
docker compose up --build
```

---

## 14. Key File Locations — Quick Reference

| Task | File |
|------|------|
| Add new API route | `backend/app/api/v1/router.py` + new file in `endpoints/` |
| Add new ORM model | `backend/app/models/new.py` → import in `models/__init__.py` → `alembic revision --autogenerate` |
| Add business logic | `backend/app/services/` |
| Add DB queries | `backend/app/repositories/` |
| Add new exception | `backend/app/core/exceptions.py` |
| Change JWT TTL | `backend/.env` — `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` |
| Add new page | `frontend/src/app/<route>/page.tsx` |
| Protect a page | Wrap with `<ProtectedRoute>` |
| Restrict to admin | Wrap with `<ProtectedRoute requiredRole="admin">` |
| Add API service | `frontend/src/services/` |
| Add global state | `frontend/src/store/` |
| Change theme colours | `frontend/src/styles/globals.css` |

---

*End of Master Report — Phase 1, 2, 3.1, 3.2 Complete*
*Next: Phase 4 — Scheme CRUD API + Eligibility Engine + User Management*
