from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CameraCreate(BaseModel):
    name: str
    description: Optional[str] = None
    lat: float
    lon: float
    heading: Optional[float] = None
    rtsp_url: Optional[str] = None
    active: bool = True


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    heading: Optional[float] = None
    rtsp_url: Optional[str] = None
    active: Optional[bool] = None


class CameraResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    lat: float
    lon: float
    heading: Optional[float]
    rtsp_url: Optional[str]
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True
