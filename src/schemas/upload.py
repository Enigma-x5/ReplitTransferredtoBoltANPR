from datetime import datetime

from pydantic import BaseModel

from src.models.upload import UploadStatus


class UploadJobResponse(BaseModel):
    job_id: str
    status: UploadStatus
    created_at: datetime

    class Config:
        from_attributes = True
