import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from src.auth import get_current_user
from src.config import settings
from src.database import get_db
from src.models.upload import Upload, UploadStatus
from src.models.user import User
from src.schemas.upload import UploadJobResponse
from src.services.storage import get_storage_service
from src.services.queue import queue_service
from src.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post("", response_model=UploadJobResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(...),
    camera_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only video files allowed.")

    job_id = str(uuid.uuid4())
    storage_path = f"uploads/{job_id}/{file.filename}"

    try:
        storage_service = get_storage_service()
        await storage_service.upload_file(
            file.file,
            settings.STORAGE_BUCKET,
            storage_path,
            content_type=file.content_type or "video/mp4"
        )
    except Exception as e:
        logger.error("Failed to upload file", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to upload file")

    file.file.seek(0, 2)
    file_size = file.file.tell()

    upload = Upload(
        job_id=job_id,
        camera_id=uuid.UUID(camera_id) if camera_id else None,
        uploaded_by=current_user.id,
        filename=file.filename,
        storage_path=storage_path,
        file_size=file_size,
        status=UploadStatus.QUEUED,
    )
    db.add(upload)
    await db.commit()
    await db.refresh(upload)

    await queue_service.enqueue("video_processing", {
        "job_id": job_id,
        "upload_id": str(upload.id),
        "storage_path": storage_path,
        "camera_id": camera_id,
    })

    logger.info("Upload created", job_id=job_id, uploaded_by=str(current_user.id))

    return UploadJobResponse.model_validate(upload)
