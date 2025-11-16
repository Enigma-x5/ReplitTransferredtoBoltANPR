from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.auth import get_current_user
from src.database import get_db
from src.models.upload import Upload
from src.models.user import User
from src.schemas.upload import UploadJobResponse
from src.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/{job_id}", response_model=UploadJobResponse)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Upload).where(Upload.job_id == job_id))
    upload = result.scalar_one_or_none()

    if not upload:
        raise HTTPException(status_code=404, detail="Job not found")

    return UploadJobResponse.model_validate(upload)
