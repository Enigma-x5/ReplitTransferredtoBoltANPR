import asyncio
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
import tempfile
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.config import settings
from src.logging_config import setup_logging, get_logger
from src.models.upload import Upload, UploadStatus
from src.models.event import Event, ReviewState
from src.models.bolo import BOLO, BOLOMatch
from src.services.queue import queue_service
from src.services.storage import get_storage_service
from src.services.detector_adapter import DetectorAdapter
from src.database import AsyncSessionLocal
from prometheus_client import Counter, Gauge

setup_logging()
logger = get_logger(__name__)

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

            if video_path.startswith("/tmp"):
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
    
    if url.startswith("file://"):
        local_path = url.replace("file://", "")
        if Path(local_path).exists():
            logger.info("Using local file directly", path=local_path)
            return local_path
        else:
            raise FileNotFoundError(f"Local file not found: {local_path}")

    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        temp_file.write(response.content)
        temp_file.close()

        logger.info("Video downloaded", path=temp_file.name)
        return temp_file.name


_debug_frame_saved = {}


async def save_event(db: AsyncSession, upload: Upload, detection: dict) -> Event:
    from PIL import Image
    import numpy as np

    job_id = str(upload.id)
    frame_no = detection.get("frame_no", 0)
    crop_path = f"crops/{upload.id}/{uuid.uuid4()}.jpg"

    crop_array = detection.get("crop")
    frame_array = detection.get("frame")

    # DEBUG: Log frame stats if frame is available
    if frame_array is not None and isinstance(frame_array, np.ndarray):
        logger.info(
            "DEBUG_FRAME_STATS",
            job_id=job_id,
            frame_no=frame_no,
            frame_shape=frame_array.shape,
            frame_dtype=str(frame_array.dtype),
            frame_min=int(frame_array.min()),
            frame_max=int(frame_array.max())
        )

        # Save ONE full frame per job for forensic inspection
        if job_id not in _debug_frame_saved:
            _debug_frame_saved[job_id] = True
            debug_dir = Path("storage/anpr-crops/debug")
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_path = debug_dir / f"fullframe_{job_id}_frame{frame_no}.jpg"
            try:
                # Convert BGR to RGB without cv2
                frame_rgb = frame_array[..., ::-1].copy()
                Image.fromarray(frame_rgb.astype('uint8')).save(str(debug_path), format='JPEG', quality=90)
                logger.info("DEBUG_FULLFRAME_SAVED", path=str(debug_path), shape=frame_array.shape)
            except Exception as e:
                logger.error("DEBUG_FULLFRAME_SAVE_FAILED", error=str(e))
    elif frame_array is None:
        logger.warning("DEBUG_FRAME_MISSING", job_id=job_id, frame_no=frame_no)

    # Validate crop is a real numpy array with valid dimensions
    if not isinstance(crop_array, np.ndarray):
        logger.error("DEBUG_CROP_INVALID_TYPE", job_id=job_id, frame_no=frame_no, crop_type=type(crop_array).__name__)
        crop_path = None
    elif crop_array.ndim != 3 or crop_array.shape[2] != 3:
        logger.error("DEBUG_CROP_INVALID_SHAPE", job_id=job_id, frame_no=frame_no, shape=crop_array.shape)
        crop_path = None
    elif crop_array.shape[0] < 5 or crop_array.shape[1] < 5:
        logger.error("DEBUG_CROP_TOO_SMALL", job_id=job_id, frame_no=frame_no, shape=crop_array.shape)
        crop_path = None
    else:
        crop_min = int(crop_array.min())
        crop_max = int(crop_array.max())

        # DEBUG: Log crop stats before saving
        logger.info(
            "DEBUG_CROP_STATS",
            job_id=job_id,
            frame_no=frame_no,
            crop_shape=crop_array.shape,
            crop_dtype=str(crop_array.dtype),
            crop_min=crop_min,
            crop_max=crop_max
        )

        # Check for solid color crop (indicates decode failure)
        if crop_min == crop_max:
            logger.error(
                "DEBUG_CROP_SOLID_COLOR",
                job_id=job_id,
                frame_no=frame_no,
                value=crop_min,
                msg="Crop is solid color - likely decode failure"
            )

        # Convert BGR (OpenCV) to RGB (PIL) without cv2
        crop_rgb = crop_array[..., ::-1].copy()
        img = Image.fromarray(crop_rgb.astype('uint8'))

        crop_file = BytesIO()
        img.save(crop_file, format='JPEG', quality=90)
        crop_file.seek(0)

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
    from src.services.detector_adapter import log_detector_config

    logger.info("Worker started", concurrency=settings.WORKER_CONCURRENCY)
    log_detector_config()

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
