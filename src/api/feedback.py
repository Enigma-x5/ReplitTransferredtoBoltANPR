import re
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.auth import get_current_user
from src.database import get_db
from src.models.event import Event, ReviewState
from src.models.bolo import BOLO
from src.models.export import Export, ExportStatus
from src.models.user import User
from src.schemas.event import EventListResponse, EventResponse
from src.services.queue import queue_service
from src.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/feedback", tags=["Feedback"])


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", (s or "").upper()).strip()


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

    bolo_result = await db.execute(select(BOLO.plate_pattern).where(BOLO.active == True))
    bolo_patterns = {_norm(row[0]) for row in bolo_result.fetchall()}

    items = []
    for event in events:
        event_dict = EventResponse.model_validate(event).model_dump()
        if event.crop_path:
            event_dict['crop_url'] = f"/media/anpr-crops/{event.crop_path}"
        plate_norm = _norm(event.normalized_plate or event.plate)
        event_dict['is_bolo_match'] = plate_norm in bolo_patterns
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
