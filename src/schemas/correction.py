from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CorrectionCreate(BaseModel):
    corrected_plate: str
    comments: Optional[str] = None


class CorrectionResponse(BaseModel):
    id: UUID
    event_id: UUID
    original_plate: str
    corrected_plate: str
    corrected_by: UUID
    confidence_before: float
    comments: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
