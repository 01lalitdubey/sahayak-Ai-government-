from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime

from app.auth.dependencies import require_role
from app.database.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.admin import SystemHealthResponse

router = APIRouter(prefix="/admin", tags=["Admin System"])

@router.get("/system/health", response_model=SystemHealthResponse)
async def get_system_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN))
):
    """
    Get backend system health.
    """
    try:
        # Check DB connection
        await db.execute(text("SELECT 1"))
        db_status = "Healthy"
    except Exception:
        db_status = "Error"
        
    return SystemHealthResponse(
        status="Healthy" if db_status == "Healthy" else "Warning",
        database=db_status,
        version="1.0.0",
        timestamp=datetime.utcnow(),
        active_connections=1 # Placeholder
    )
