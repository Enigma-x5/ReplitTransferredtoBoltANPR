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
        from src.detectors.yolo_easyocr_adapter import process_video
        return process_video
    elif backend == "yolo_ffmpeg":
        logger.info("Loading YOLO+EasyOCR detector with ffmpeg frame extraction")
        from src.detectors.yolo_easyocr_ffmpeg import process_video
        return process_video
    elif backend == "mock":
        logger.info("Loading mock detector")
        from src.detectors.mock_detector import process_video
        return process_video
    else:
        logger.warning(f"Unknown detector backend: {backend}, falling back to mock")
        from src.detectors.mock_detector import process_video
        return process_video


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
