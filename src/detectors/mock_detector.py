import cv2
import random
import re
from pathlib import Path
from typing import Dict, List, Generator, Any
from datetime import datetime

from src.logging_config import get_logger

logger = get_logger(__name__)


def normalize_plate(plate: str) -> str:
    return re.sub(r'[^A-Z0-9]', '', plate.upper())


class MockDetector:
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        logger.info("Mock detector initialized", threshold=self.confidence_threshold)

    def process_video(
        self, video_path: str, camera_id: str = None
    ) -> Generator[Dict[str, Any], None, None]:
        logger.info("Processing video (mock mode)", video_path=video_path, camera_id=camera_id)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("Failed to open video file", video_path=video_path)
            raise ValueError(f"Cannot open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_no = 0
        detections_count = 0

        mock_plates = [
            "ABC123",
            "XYZ789",
            "LMN456",
            "TEST99",
            "DEMO01",
        ]

        num_detections = random.randint(2, min(5, max(2, total_frames // 100)))

        detection_frames = sorted(random.sample(
            range(0, max(1, total_frames - 1)),
            min(num_detections, max(1, total_frames - 1))
        ))

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_no in detection_frames:
                    plate_text = random.choice(mock_plates)
                    confidence = random.uniform(0.75, 0.95)

                    h, w = frame.shape[:2]
                    x1 = random.randint(w // 4, w // 2)
                    y1 = random.randint(h // 4, h // 2)
                    x2 = min(x1 + random.randint(80, 120), w - 1)
                    y2 = min(y1 + random.randint(30, 50), h - 1)

                    crop = frame[y1:y2, x1:x2]

                    detection = {
                        "plate": plate_text,
                        "normalized_plate": normalize_plate(plate_text),
                        "confidence": confidence,
                        "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                        "frame_no": frame_no,
                        "captured_at": datetime.utcnow(),
                        "crop": crop,
                        "camera_id": camera_id,
                    }

                    yield detection
                    detections_count += 1

                frame_no += 1

        finally:
            cap.release()
            logger.info(
                "Video processing complete (mock mode)",
                total_frames=frame_no,
                mock_detections=detections_count,
            )


def process_video(video_path: str, camera_id: str = None) -> Generator[Dict[str, Any], None, None]:
    detector = MockDetector()
    yield from detector.process_video(video_path, camera_id)
