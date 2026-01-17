import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.auth import get_current_user
from src.database import get_db
from src.models.event import Event, ReviewState, Correction
from src.models.user import User
from src.schemas.event import EventResponse, EventListResponse, ConfirmEventRequest
from src.schemas.correction import CorrectionCreate, CorrectionResponse
from src.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=EventListResponse)
async def search_events(
    plate: Optional[str] = Query(None),
    normalized: Optional[bool] = Query(False),
    camera_id: Optional[str] = Query(None),
    from_ts: Optional[datetime] = Query(None),
    to_ts: Optional[datetime] = Query(None),
    limit: int = Query(50, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Event)
    conditions = []

    if plate:
        if normalized:
            conditions.append(Event.normalized_plate.ilike(f"%{plate}%"))
        else:
            conditions.append(Event.plate.ilike(f"%{plate}%"))

    if camera_id:
        conditions.append(Event.camera_id == uuid.UUID(camera_id))

    if from_ts:
        conditions.append(Event.captured_at >= from_ts)

    if to_ts:
        conditions.append(Event.captured_at <= to_ts)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(Event.captured_at.desc()).limit(limit)

    result = await db.execute(query)
    events = result.scalars().all()

    count_query = select(func.count(Event.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    items = []
    for event in events:
        event_dict = EventResponse.model_validate(event).model_dump()
        if event.crop_path:
            event_dict['crop_url'] = f"/media/anpr-crops/{event.crop_path}"
        items.append(EventResponse(**event_dict))

    return EventListResponse(
        total=total,
        items=items
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    event_dict = EventResponse.model_validate(event).model_dump()
    if event.crop_path:
        event_dict['crop_url'] = f"/media/anpr-crops/{event.crop_path}"

    return EventResponse(**event_dict)


@router.post("/{event_id}/confirm", response_model=EventResponse)
async def confirm_event(
    event_id: uuid.UUID,
    request: ConfirmEventRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()

        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        event.review_state = ReviewState.CONFIRMED
        event.reviewed_by = current_user.id
        event.reviewed_at = datetime.now(timezone.utc)
        event.notes = request.notes

        await db.commit()
        await db.refresh(event)

        logger.info("Event confirmed", event_id=str(event_id), confirmed_by=str(current_user.id))

        event_dict = EventResponse.model_validate(event).model_dump()
        if event.crop_path:
            event_dict['crop_url'] = f"/media/anpr-crops/{event.crop_path}"

        return EventResponse(**event_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to confirm event", event_id=str(event_id), error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to confirm event: {str(e)}")


@router.post("/{event_id}/correction", response_model=CorrectionResponse, status_code=201)
async def create_correction(
    event_id: uuid.UUID,
    correction_data: CorrectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()

        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        correction = Correction(
            event_id=event_id,
            original_plate=event.plate,
            corrected_plate=correction_data.corrected_plate,
            corrected_by=current_user.id,
            confidence_before=event.confidence,
            comments=correction_data.comments,
        )
        db.add(correction)

        event.review_state = ReviewState.CORRECTED
        event.reviewed_by = current_user.id
        event.reviewed_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(correction)

        logger.info(
            "Correction created",
            event_id=str(event_id),
            original=event.plate,
            corrected=correction_data.corrected_plate,
            by=str(current_user.id)
        )

        return CorrectionResponse.model_validate(correction)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create correction", event_id=str(event_id), error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create correction: {str(e)}")
