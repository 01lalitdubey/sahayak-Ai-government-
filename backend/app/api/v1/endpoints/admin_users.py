from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
import uuid

from app.auth.dependencies import require_role
from app.database.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.models.profile import Profile
from app.schemas.admin import AdminUserListResponse, AdminUserResponse, AdminUserUpdateRequest

router = APIRouter(prefix="/admin", tags=["Admin Users"])

@router.get("/users", response_model=AdminUserListResponse)
async def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN))
):
    """
    Get paginated list of users.
    """
    skip = (page - 1) * size
    
    query = select(User).join(Profile, isouter=True)
    count_query = select(func.count(User.id))
    
    # Filters
    if search:
        search_filter = or_(
            User.email.ilike(f"%{search}%"),
            Profile.full_name.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
        
    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)
        
    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)
        
    query = query.order_by(User.created_at.desc()).offset(skip).limit(size)
    
    total = await db.scalar(count_query)
    result = await db.execute(query)
    users = result.scalars().all()
    
    items = []
    for u in users:
        # Load profile dynamically if not loaded
        profile = await u.awaitable_attrs.profile
        items.append(AdminUserResponse(
            id=str(u.id),
            email=u.email,
            full_name=profile.full_name if profile else "Unknown",
            role=u.role,
            preferred_language=profile.preferred_language.value if profile and profile.preferred_language else "en",
            state=profile.state if profile else None,
            is_active=u.is_active,
            created_at=u.created_at,
            updated_at=u.updated_at
        ))
        
    return AdminUserListResponse(
        items=items,
        total=total or 0,
        page=page,
        size=size
    )

@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user_by_id(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN))
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    profile = await user.awaitable_attrs.profile
    return AdminUserResponse(
        id=str(user.id),
        email=user.email,
        full_name=profile.full_name if profile else "Unknown",
        role=user.role,
        preferred_language=profile.preferred_language.value if profile and profile.preferred_language else "en",
        state=profile.state if profile else None,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: uuid.UUID,
    payload: AdminUserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN))
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if payload.role is not None:
        if current_user.role != UserRole.SUPER_ADMIN and payload.role == UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Only SUPER_ADMIN can assign SUPER_ADMIN role")
        user.role = payload.role
        
    if payload.is_active is not None:
        user.is_active = payload.is_active
        
    await db.commit()
    await db.refresh(user)
    
    profile = await user.awaitable_attrs.profile
    return AdminUserResponse(
        id=str(user.id),
        email=user.email,
        full_name=profile.full_name if profile else "Unknown",
        role=user.role,
        preferred_language=profile.preferred_language.value if profile and profile.preferred_language else "en",
        state=profile.state if profile else None,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
