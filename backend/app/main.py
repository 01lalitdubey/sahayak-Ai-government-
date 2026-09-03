"""
Sahayak AI — FastAPI Application Entry Point
=============================================
App factory pattern: all middleware, routers, and exception handlers
are registered here. Keep this file thin — delegate logic to modules.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError, OperationalError, TimeoutError

from app.core.config import settings
from app.core.ratelimit import limiter
from app.core.logging import configure_logging, get_logger
from app.core.exception_handlers import (
    sahayak_exception_handler,
    sqlalchemy_integrity_handler,
    sqlalchemy_operational_handler,
    sqlalchemy_timeout_handler,
    unhandled_exception_handler,
)
from app.core.exceptions import SahayakBaseException


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Render slowapi's 429 in the app's standard error envelope."""
    logger.warning("Rate limit hit on %s %s: %s", request.method, request.url.path, exc.detail)
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "message": f"Too many requests ({exc.detail}). Please slow down and retry.",
            "status_code": 429,
        },
    )
from app.database.database import init_db, close_db
from app.middleware.request_logger import RequestLoggerMiddleware
from app.api.v1.router import api_router

# ── Logging must be configured before any import emits logs ───────────────
configure_logging()
logger = get_logger(__name__)


# ── Application Lifespan ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info(
        "🚀 Starting %s v%s [%s]",
        settings.APP_NAME, settings.APP_VERSION, settings.APP_ENV,
    )
    await init_db()
    yield
    logger.info("🛑 Shutting down %s", settings.APP_NAME)
    await close_db()


# ── Application Factory ────────────────────────────────────────────────────
def create_application() -> FastAPI:
    app = FastAPI(
        title=f"{settings.APP_NAME} Backend",
        version=settings.APP_VERSION,
        description=(
            "Sahayak AI — Multilingual AI assistant for Indian government schemes.\n\n"
            "**Authentication:** Use `POST /api/v1/auth/login` to obtain a Bearer token, "
            "then click **Authorize** above and enter `Bearer <your_token>`."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        swagger_ui_parameters={"persistAuthorization": True},
    )

    # ── CORS ──────────────────────────────────────────────────────────────
    # In development, allow all origins so local Next.js (localhost, 127.0.0.1,
    # network IPs) can reach the API without CORS preflight rejections.
    cors_origins = ["*"] if settings.is_development else settings.ALLOWED_ORIGINS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False if cors_origins == ["*"] else True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Custom middleware ──────────────────────────────────────────────────
    app.add_middleware(RequestLoggerMiddleware)

    # ── Rate limiting (slowapi) ───────────────────────────────────────────
    app.state.limiter = limiter

    # ── Exception handlers ─────────────────────────────────────────────────
    # Order matters: most specific first, catch-all last
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)                     # type: ignore[arg-type]
    app.add_exception_handler(SahayakBaseException, sahayak_exception_handler)          # type: ignore[arg-type]
    app.add_exception_handler(IntegrityError, sqlalchemy_integrity_handler)              # type: ignore[arg-type]
    app.add_exception_handler(OperationalError, sqlalchemy_operational_handler)          # type: ignore[arg-type]
    app.add_exception_handler(TimeoutError, sqlalchemy_timeout_handler)                  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)                    # type: ignore[arg-type]

    # ── Routers ───────────────────────────────────────────────────────────
    app.include_router(api_router)

    # ── Root endpoints ────────────────────────────────────────────────────
    @app.get("/", tags=["Root"], summary="API root")
    async def root() -> JSONResponse:
        return JSONResponse(content={
            "success": True,
            "message": f"Welcome to {settings.APP_NAME} API",
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "docs": "/docs",
            "redoc": "/redoc",
        })

    @app.get("/health", tags=["Health"], summary="Application health check")
    async def health_check() -> JSONResponse:
        return JSONResponse(content={
            "success": True,
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
        })

    return app


app = create_application()
