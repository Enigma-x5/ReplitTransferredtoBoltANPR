import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.auth import get_current_user
from src.database import get_db
from src.models.event import Event, ReviewState
from src.models.export import Export, ExportStatus
from src.models.user import User
from src.schemas.event import EventListResponse, EventResponse
from src.services.queue import queue_service
from src.services.storage import get_storage_service
from src.config import settings
from src.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.get("/pending", response_model=EventListResponse)
async def list_pending_feedback(
    limit: int = Query(50, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Event)
        .where(Event.review_state == ReviewState.UNREVIEWED)
        .order_by(Event.captured_at.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    events = result.scalars().all()

    storage = get_storage_service()
    items = []
    for event in events:
        event_dict = EventResponse.model_validate(event).model_dump()
        if event.crop_path:
            try:
                event_dict['crop_url'] = await storage.get_presigned_url(
                    settings.STORAGE_CROPS_BUCKET, event.crop_path, expiry=3600
                )
            except Exception as e:
                logger.warning(f"Failed to generate presigned URL for {event.crop_path}: {e}")
                event_dict['crop_url'] = None
        items.append(EventResponse(**event_dict))

    return EventListResponse(
        total=len(items),
        items=items
    )


@router.post("/export")
async def request_export(
    from_ts: Optional[datetime] = None,
    to_ts: Optional[datetime] = None,
    min_confidence: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    export = Export(
        requested_by=current_user.id,
        status=ExportStatus.PENDING,
        filters={
            "from_ts": from_ts.isoformat() if from_ts else None,
            "to_ts": to_ts.isoformat() if to_ts else None,
            "min_confidence": min_confidence,
        },
    )
    db.add(export)
    await db.commit()
    await db.refresh(export)

    await queue_service.enqueue("export_processing", {
        "export_id": str(export.id),
        "filters": export.filters,
    })

    logger.info("Export requested", export_id=str(export.id), requested_by=str(current_user.id))

    return {"export_id": str(export.id)}
