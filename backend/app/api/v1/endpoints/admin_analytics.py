from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_role
from app.database.database import get_db
from app.models.enums import UserRole
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin Analytics"])

@router.get("/analytics/growth")
async def get_growth_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN))
):
    """
    Get user growth analytics over time.
    (Placeholder implementation for now)
    """
    return {
        "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "data": [10, 25, 45, 60, 80, 110, 150]
    }

@router.get("/analytics/schemes")
async def get_scheme_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN))
):
    """
    Get scheme popularity analytics.
    (Placeholder implementation for now)
    """
    return {
        "labels": ["Agriculture", "Education", "Health", "Housing", "Women"],
        "data": [120, 95, 80, 60, 45]
    }
