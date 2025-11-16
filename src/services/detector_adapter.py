from typing import Iterator, Dict, Any
from pathlib import Path
import cv2
import re
from datetime import datetime

from src.config import settings
from src.logging_config import get_logger

logger = get_logger(__name__)


def normalize_plate(plate: str) -> str:
    return re.sub(r'[^A-Z0-9]', '', plate.upper())


class DetectorAdapter:
    def __init__(self, confidence_threshold: float = None):
        self.confidence_threshold = confidence_threshold or settings.DETECTION_CONFIDENCE_THRESHOLD
        logger.info("Detector adapter initialized", threshold=self.confidence_threshold)

    def process_video(
        self, video_path: str, camera_id: str
    ) -> Iterator[Dict[str, Any]]:
        logger.info("Processing video", video_path=video_path, camera_id=camera_id)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("Failed to open video file", video_path=video_path)
            raise ValueError(f"Cannot open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps / settings.FRAME_EXTRACTION_FPS) if fps > 0 else 1
        frame_no = 0
        processed = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_no % frame_interval == 0:
                    detections = self._detect_plates_in_frame(frame, frame_no)

                    for detection in detections:
                        if detection["confidence"] >= self.confidence_threshold:
                            detection["camera_id"] = camera_id
                            detection["captured_at"] = datetime.utcnow()
                            yield detection
                            processed += 1

                frame_no += 1

        finally:
            cap.release()
            logger.info(
                "Video processing complete",
                total_frames=frame_no,
                processed_detections=processed,
            )

    def _detect_plates_in_frame(self, frame, frame_no: int) -> list[Dict[str, Any]]:
        from src.detectors.yolo_easyocr_adapter import detect_plates

        try:
            results = detect_plates(frame)

            detections = []
            for result in results:
                crop = self._extract_crop(frame, result["bbox"])

                detection = {
                    "plate": result["plate"],
                    "normalized_plate": normalize_plate(result["plate"]),
                    "confidence": result["confidence"],
                    "bbox": result["bbox"],
                    "frame_no": frame_no,
                    "crop": crop,
                }
                detections.append(detection)

            return detections
        except Exception as e:
            logger.error("Detection failed for frame", frame_no=frame_no, error=str(e))
            return []

    def _extract_crop(self, frame, bbox: dict) -> Any:
        x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
        crop = frame[y1:y2, x1:x2]
        return crop
