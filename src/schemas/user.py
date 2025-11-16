from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from src.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: UserRole = UserRole.CLERK


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True
