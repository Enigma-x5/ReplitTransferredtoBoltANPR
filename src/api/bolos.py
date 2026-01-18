import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.auth import get_current_user
from src.database import get_db
from src.models.bolo import BOLO
from src.models.user import User
from src.schemas.bolo import BOLOCreate, BOLOResponse
from src.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/bolos", tags=["BOLOs"])


@router.post("", response_model=BOLOResponse, status_code=status.HTTP_201_CREATED)
async def create_bolo(
    bolo_data: BOLOCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bolo = BOLO(
        **bolo_data.model_dump(),
        created_by=current_user.id,
    )
    db.add(bolo)
    await db.commit()
    await db.refresh(bolo)

    logger.info("BOLO created", bolo_id=str(bolo.id), pattern=bolo.plate_pattern)

    return BOLOResponse.model_validate(bolo)


@router.get("", response_model=list[BOLOResponse])
async def list_bolos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(BOLO).order_by(BOLO.created_at.desc()))
    bolos = result.scalars().all()
    return [BOLOResponse.model_validate(bolo) for bolo in bolos]


@router.patch("/{bolo_id}/toggle", response_model=BOLOResponse)
async def toggle_bolo(
    bolo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(BOLO).where(BOLO.id == bolo_id))
    bolo = result.scalar_one_or_none()

    if not bolo:
        raise HTTPException(status_code=404, detail="BOLO not found")

    bolo.active = not bolo.active
    await db.commit()
    await db.refresh(bolo)

    logger.info("BOLO toggled", bolo_id=str(bolo.id), active=bolo.active)

    return BOLOResponse.model_validate(bolo)
