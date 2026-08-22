from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.auth.dependencies import require_role
from app.database.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.models.scheme import Scheme
from app.models.translation import SchemeTranslation
from app.schemas.admin import DashboardOverviewResponse

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN))
):
    """
    Get high-level overview statistics for the admin dashboard.
    """
    total_users = await db.scalar(select(func.count(User.id)))
    active_users = await db.scalar(select(func.count(User.id)).where(User.is_active == True))
    
    total_schemes = await db.scalar(select(func.count(Scheme.id)))
    active_schemes = await db.scalar(select(func.count(Scheme.id)).where(Scheme.status == "published"))
    
    translation_records = await db.scalar(select(func.count(SchemeTranslation.id)))
    
    return DashboardOverviewResponse(
        total_users=total_users or 0,
        active_users=active_users or 0,
        total_schemes=total_schemes or 0,
        active_schemes=active_schemes or 0,
        translation_records=translation_records or 0,
        translation_coverage=0.0, # Placeholder
        supported_languages=13 # Static for now based on LanguageEnum
    )
