from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
from app.models.enums import UserRole

# Dashboard
class DashboardOverviewResponse(BaseModel):
    total_users: int
    active_users: int
    total_schemes: int
    active_schemes: int
    translation_records: int
    translation_coverage: float
    supported_languages: int

# Users
class AdminUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    preferred_language: str
    state: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AdminUserListResponse(BaseModel):
    items: List[AdminUserResponse]
    total: int
    page: int
    size: int

class AdminUserUpdateRequest(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

# System
class SystemHealthResponse(BaseModel):
    status: str
    database: str
    version: str
    timestamp: datetime
    active_connections: int
