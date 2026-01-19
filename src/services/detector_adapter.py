from typing import Iterator, Dict, Any
from pathlib import Path
import re
from datetime import datetime

from src.config import settings
from src.logging_config import get_logger

logger = get_logger(__name__)


def normalize_plate(plate: str) -> str:
    return re.sub(r'[^A-Z0-9]', '', plate.upper())


def get_detector(backend: str = None):
    backend = backend or settings.DETECTOR_BACKEND

    if backend == "yolo":
        logger.info("Loading YOLO detector")
        try:
            from src.detectors.yolo_easyocr_adapter import process_video
            return process_video
        except Exception as e:
            logger.error(
                "YOLO_BACKEND_INIT_FAILED",
                error=str(e),
                error_type=type(e).__name__,
                fallback="mock"
            )
            logger.warning("Falling back to mock detector due to YOLO backend init failure")
            from src.detectors.mock_detector import process_video
            return process_video

    elif backend == "yolo_ffmpeg":
        logger.info("Loading YOLO+EasyOCR detector with ffmpeg frame extraction")
        try:
            from src.detectors.yolo_easyocr_ffmpeg import process_video
            return process_video
        except Exception as e:
            logger.error(
                "YOLO_FFMPEG_BACKEND_INIT_FAILED",
                error=str(e),
                error_type=type(e).__name__,
                fallback="mock",
                hint="Install dependencies: pip install torch ultralytics easyocr"
            )
            logger.warning("Falling back to mock detector due to YOLO_FFMPEG backend init failure")
            from src.detectors.mock_detector import process_video
            return process_video

    elif backend == "remote":
        logger.info("Loading remote inference detector")
        try:
            from src.detectors.remote_inference import process_video
            return process_video
        except Exception as e:
            logger.error(
                "REMOTE_BACKEND_INIT_FAILED",
                error=str(e),
                error_type=type(e).__name__,
                fallback="mock",
                hint="Check REMOTE_INFERENCE_URL and network connectivity"
            )
            logger.warning("Falling back to mock detector due to remote backend init failure")
            from src.detectors.mock_detector import process_video
            return process_video

    elif backend == "mock":
        logger.info("Loading mock detector")
        from src.detectors.mock_detector import process_video
        return process_video

    else:
        logger.warning(f"Unknown detector backend: {backend}, falling back to mock")
        from src.detectors.mock_detector import process_video
        return process_video


def log_detector_config():
    """Log effective detector configuration at startup."""
    config = {
        "detector_backend": settings.DETECTOR_BACKEND,
        "detection_confidence_threshold": settings.DETECTION_CONFIDENCE_THRESHOLD,
        "frame_extraction_fps": settings.FRAME_EXTRACTION_FPS,
    }

    # Add backend-specific config
    if settings.DETECTOR_BACKEND in ["yolo", "yolo_ffmpeg"]:
        import os
        config.update({
            "yolo_model": os.getenv("YOLO_MODEL", "keremberke/yolov8n-license-plate"),
            "detect_confidence": os.getenv("DETECT_CONFIDENCE", "0.30"),
            "device": os.getenv("DEVICE", "auto-detect"),
        })

        if settings.DETECTOR_BACKEND == "yolo_ffmpeg":
            config.update({
                "min_box_width": os.getenv("MIN_BOX_WIDTH", "20"),
                "min_box_height": os.getenv("MIN_BOX_HEIGHT", "10"),
            })

    elif settings.DETECTOR_BACKEND == "remote":
        config.update({
            "remote_inference_url": settings.REMOTE_INFERENCE_URL,
            "auth_configured": bool(settings.REMOTE_INFERENCE_TOKEN),
        })

    logger.info("Detector configuration", **config)


class DetectorAdapter:
    def __init__(self, confidence_threshold: float = None, backend: str = None):
        self.confidence_threshold = confidence_threshold or settings.DETECTION_CONFIDENCE_THRESHOLD
        self.backend = backend or settings.DETECTOR_BACKEND
        self.process_video_func = get_detector(self.backend)
        logger.info(
            "Detector adapter initialized",
            backend=self.backend,
            threshold=self.confidence_threshold
        )

    def process_video(
        self, video_path: str, camera_id: str
    ) -> Iterator[Dict[str, Any]]:
        logger.info(
            "Processing video",
            video_path=video_path,
            camera_id=camera_id,
            backend=self.backend
        )

        for detection in self.process_video_func(video_path, camera_id):
            if detection.get("confidence", 0) >= self.confidence_threshold:
                if "camera_id" not in detection:
                    detection["camera_id"] = camera_id
                if "captured_at" not in detection or not isinstance(detection["captured_at"], datetime):
                    detection["captured_at"] = datetime.utcnow()
                yield detection
