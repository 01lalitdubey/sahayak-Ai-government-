"""
Database Health Endpoint — Sahayak AI
GET /api/v1/database/health

Runs a live SELECT 1 against PostgreSQL and reports connectivity status.
Used by load balancers, Docker healthchecks, and monitoring dashboards.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.database.database import check_db_connection
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/database", tags=["Database"])


@router.get(
    "/health",
    summary="Database health check",
    response_description="Database connectivity status",
)
async def database_health() -> JSONResponse:
    """
    Connects to PostgreSQL and runs SELECT 1.

    Returns:
    - **200** — database is reachable
    - **503** — database is unavailable
    """
    is_connected = await check_db_connection()

    if is_connected:
        logger.info("Database health check: OK")
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "database": "connected",
                "message": "PostgreSQL is reachable",
            },
        )

    logger.warning("Database health check: FAILED")
    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "database": "unavailable",
            "message": "Cannot reach PostgreSQL. Check DATABASE_URL and ensure the server is running.",
        },
    )
