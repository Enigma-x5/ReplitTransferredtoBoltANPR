from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ActivateLicenseRequest(BaseModel):
    license_key: str
    node_id: str


class ActivateLicenseResponse(BaseModel):
    activated: bool
    expires_at: datetime
    features: dict


class UsageReportRequest(BaseModel):
    node_id: str
    camera_count: int
    timestamp: Optional[datetime] = None
