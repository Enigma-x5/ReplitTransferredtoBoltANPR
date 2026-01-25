from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from src.models.event import ReviewState


class BBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class EventResponse(BaseModel):
    id: UUID
    plate: str
    normalized_plate: str
    confidence: float
    camera_id: UUID
    bbox: dict
    captured_at: datetime
    frame_no: int
    crop_path: Optional[str] = None  # Allow null for backward compatibility
    crop_url: Optional[str] = None
    review_state: ReviewState
    created_at: datetime
    is_bolo_match: bool = False

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    total: int
    items: list[EventResponse]


class ConfirmEventRequest(BaseModel):
    confirmed_by: Optional[str] = None
    notes: Optional[str] = None
