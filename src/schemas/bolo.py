from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class BOLOCreate(BaseModel):
    plate_pattern: str
    description: Optional[str] = None
    active: bool = True
    priority: int = 1
    notification_webhook: Optional[str] = None
    notification_email: Optional[str] = None
    expires_at: Optional[datetime] = None


class BOLOResponse(BaseModel):
    id: UUID
    plate_pattern: str
    description: Optional[str]
    created_by: UUID
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True
