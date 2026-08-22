# Sahayak AI — Architecture Decision Record

## Overview

Sahayak AI follows a clean, layered architecture designed for independent scaling of frontend and backend.

## Frontend Architecture (Next.js 15 App Router)

```
Request → Next.js Route → React Server Component
                        → Client Component → Zustand Store
                                           → TanStack Query → Axios → FastAPI
```

### Layer Responsibilities

| Layer | Location | Responsibility |
|-------|----------|---------------|
| Pages | `app/**/page.tsx` | Route entry points — thin, compose components |
| Layout | `components/layout/` | Navbar, Footer, page shells |
| Components | `components/common/`, `components/ui/` | Reusable UI primitives |
| Hooks | `hooks/` | Data fetching (TanStack Query) + UI logic |
| Services | `services/` | Axios calls — one file per API resource |
| Store | `store/` | Zustand slices — auth state, UI state |
| Lib | `lib/` | Pure utilities — no side effects |
| Types | `types/` | TypeScript interfaces shared across layers |

## Backend Architecture (FastAPI)

```
HTTP Request → CORS → RequestLoggerMiddleware
            → FastAPI Route Handler (thin)
            → Service Layer (business logic)
            → Repository Layer (DB I/O)
            → SQLAlchemy Async Session → PostgreSQL
```

### Layer Responsibilities

| Layer | Location | Responsibility |
|-------|----------|---------------|
| API Routes | `api/v1/endpoints/` | HTTP layer — validation, status codes, response shaping |
| Services | `services/` | Business logic, orchestration, external service calls |
| Repositories | `repositories/` | All SQL — no business logic here |
| Models | `models/` | SQLAlchemy ORM table definitions |
| Schemas | `schemas/` | Pydantic v2 request/response contracts |
| Core | `core/` | Config, logging, security |
| Database | `database/` | Engine, session, base class |

## Frontend ↔ Backend Communication

- All API calls go through `src/lib/axios.ts` (pre-configured Axios instance)
- The base URL is `NEXT_PUBLIC_API_BASE_URL` (env var)
- All endpoints are prefixed `/api/v1/`
- Responses always follow the `ApiSuccessResponse<T>` or `ApiErrorResponse` envelope
- TanStack Query manages caching, background refetch, and loading states
- Authentication token (Phase 2) will be attached via Axios request interceptor

## PostgreSQL Connection (Phase 3)

1. `DATABASE_URL` env var → `app/core/config.py` → `Settings.DATABASE_URL`
2. `app/database/database.py` creates an `AsyncEngine` from that URL using `asyncpg` driver
3. `AsyncSessionLocal` session factory is created from the engine
4. FastAPI's `Depends(get_db)` injects a fresh `AsyncSession` per request
5. Alembic migrations run via `alembic upgrade head` before first boot
6. All schema changes are tracked as versioned migration files in `alembic/versions/`
