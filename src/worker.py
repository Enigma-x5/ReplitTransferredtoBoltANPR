import asyncio
import uuid
import cv2
from datetime import datetime
from io import BytesIO
from pathlib import Path
import tempfile
import re

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from src.config import settings
from src.logging_config import setup_logging, get_logger
from src.models.upload import Upload, UploadStatus
from src.models.event import Event, ReviewState
from src.models.bolo import BOLO, BOLOMatch
from src.services.queue import queue_service
from src.services.storage import get_storage_service
from src.services.detector_adapter import DetectorAdapter
from prometheus_client import Counter, Gauge

setup_logging()
logger = get_logger(__name__)

engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

storage_service = get_storage_service()
detector = DetectorAdapter()

events_processed = Counter('anpr_events_processed', 'Total events processed')
events_failed = Counter('anpr_events_failed', 'Total events failed')
jobs_processed = Counter('anpr_jobs_processed', 'Total jobs processed')
jobs_failed = Counter('anpr_jobs_failed', 'Total jobs failed')
queue_size = Gauge('anpr_queue_size', 'Current queue size')


async def process_job(job_data: dict):
    async with AsyncSessionLocal() as db:
        upload_id = uuid.UUID(job_data["upload_id"])
        job_id = job_data["job_id"]

        result = await db.execute(select(Upload).where(Upload.id == upload_id))
        upload = result.scalar_one_or_none()

        if not upload:
            logger.error("Upload not found", upload_id=str(upload_id))
            return

        try:
            upload.status = UploadStatus.PROCESSING
            upload.started_at = datetime.utcnow()
            await db.commit()

            logger.info("Processing upload", job_id=job_id, upload_id=str(upload_id))

            video_path = await download_video(job_data["storage_path"])

            events_count = 0
            for detection in detector.process_video(video_path, job_data.get("camera_id")):
                event = await save_event(db, upload, detection)
                if event:
                    events_count += 1
                    events_processed.inc()
                    await check_bolos(db, event)

            upload.status = UploadStatus.DONE
            upload.completed_at = datetime.utcnow()
            upload.events_detected = events_count
            await db.commit()

            Path(video_path).unlink(missing_ok=True)

            logger.info("Upload processed", job_id=job_id, events=events_count)
            jobs_processed.inc()

        except Exception as e:
            logger.error("Job processing failed", job_id=job_id, error=str(e))
            upload.status = UploadStatus.FAILED
            upload.error_message = str(e)
            upload.completed_at = datetime.utcnow()
            await db.commit()
            jobs_failed.inc()


async def download_video(storage_path: str) -> str:
    url = await storage_service.get_presigned_url(settings.STORAGE_BUCKET, storage_path)

    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        temp_file.write(response.content)
        temp_file.close()

        logger.info("Video downloaded", path=temp_file.name)
        return temp_file.name


async def save_event(db: AsyncSession, upload: Upload, detection: dict) -> Event:
    crop_path = f"crops/{upload.id}/{uuid.uuid4()}.jpg"

    crop_bytes = cv2.imencode('.jpg', detection["crop"])[1].tobytes()
    crop_file = BytesIO(crop_bytes)

    await storage_service.upload_file(
        crop_file,
        settings.STORAGE_CROPS_BUCKET,
        crop_path,
        "image/jpeg"
    )

    event = Event(
        upload_id=upload.id,
        camera_id=detection["camera_id"] or upload.camera_id,
        plate=detection["plate"],
        normalized_plate=detection["normalized_plate"],
        confidence=detection["confidence"],
        bbox=detection["bbox"],
        frame_no=detection["frame_no"],
        captured_at=detection["captured_at"],
        crop_path=crop_path,
        review_state=ReviewState.UNREVIEWED,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    logger.info("Event saved", event_id=str(event.id), plate=event.plate)
    return event


async def check_bolos(db: AsyncSession, event: Event):
    result = await db.execute(
        select(BOLO).where(BOLO.active == True)
    )
    bolos = result.scalars().all()

    for bolo in bolos:
        if bolo.expires_at and bolo.expires_at < datetime.utcnow():
            continue

        if re.search(bolo.plate_pattern, event.normalized_plate, re.IGNORECASE):
            match = BOLOMatch(
                bolo_id=bolo.id,
                event_id=event.id,
            )
            db.add(match)
            await db.commit()

            logger.warning(
                "BOLO match detected",
                bolo_id=str(bolo.id),
                event_id=str(event.id),
                plate=event.plate,
            )

            await send_bolo_notification(bolo, event)


async def send_bolo_notification(bolo: BOLO, event: Event):
    try:
        if bolo.notification_webhook:
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(
                    bolo.notification_webhook,
                    json={
                        "bolo_id": str(bolo.id),
                        "event_id": str(event.id),
                        "plate": event.plate,
                        "confidence": event.confidence,
                        "captured_at": event.captured_at.isoformat(),
                    },
                    timeout=10.0,
                )
            logger.info("BOLO webhook sent", bolo_id=str(bolo.id))

    except Exception as e:
        logger.error("Failed to send BOLO notification", error=str(e))


async def worker_loop():
    logger.info("Worker started", concurrency=settings.WORKER_CONCURRENCY)

    while True:
        try:
            job = await queue_service.dequeue("video_processing", timeout=5)
            if job:
                queue_size.set(await queue_service.get_queue_length("video_processing"))
                await process_job(job)
            else:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error("Worker error", error=str(e))
            await asyncio.sleep(5)


async def main():
    await queue_service.connect()
    try:
        await worker_loop()
    finally:
        await queue_service.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
