from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import get_current_admin
from src.database import get_db, engine
from src.models.user import User
from src.services.queue import queue_service
from src.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    try:
        await db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        db_status = "unhealthy"

    try:
        queue_length = await queue_service.get_queue_length("video_processing")
        queue_status = "healthy"
    except Exception as e:
        logger.error("Queue health check failed", error=str(e))
        queue_status = "unhealthy"
        queue_length = -1

    return {
        "status": "ok" if db_status == "healthy" and queue_status == "healthy" else "degraded",
        "database": db_status,
        "queue": {
            "status": queue_status,
            "pending_jobs": queue_length,
        },
    }
