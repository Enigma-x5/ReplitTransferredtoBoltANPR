import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.auth import get_current_user, get_current_admin
from src.database import get_db
from src.models.camera import Camera
from src.models.user import User
from src.schemas.camera import CameraCreate, CameraUpdate, CameraResponse
from src.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/cameras", tags=["Cameras"])


@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera_data: CameraCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    camera = Camera(**camera_data.model_dump())
    db.add(camera)
    await db.commit()
    await db.refresh(camera)

    logger.info("Camera created", camera_id=str(camera.id), created_by=str(current_user.id))

    return CameraResponse.model_validate(camera)


@router.get("", response_model=list[CameraResponse])
async def list_cameras(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Camera))
    cameras = result.scalars().all()
    return [CameraResponse.model_validate(camera) for camera in cameras]


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()

    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    return CameraResponse.model_validate(camera)


@router.patch("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: uuid.UUID,
    camera_data: CameraUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()

    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    for field, value in camera_data.model_dump(exclude_unset=True).items():
        setattr(camera, field, value)

    await db.commit()
    await db.refresh(camera)

    logger.info("Camera updated", camera_id=str(camera.id), updated_by=str(current_user.id))

    return CameraResponse.model_validate(camera)
