import random
import re
import numpy as np
from pathlib import Path
from typing import Dict, Generator, Any
from datetime import datetime

from src.logging_config import get_logger

logger = get_logger(__name__)


def normalize_plate(plate: str) -> str:
    return re.sub(r'[^A-Z0-9]', '', plate.upper())


class MockDetector:
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        logger.info("Mock detector initialized (no cv2)", threshold=self.confidence_threshold)

    def process_video(
        self, video_path: str, camera_id: str = None
    ) -> Generator[Dict[str, Any], None, None]:
        logger.info("Processing video (mock mode - no cv2)", video_path=video_path, camera_id=camera_id)

        mock_plates = [
            "ABC123",
            "XYZ789",
            "LMN456",
            "TEST99",
            "DEMO01",
            "MH12AB1234",
            "DL8CAB5678",
        ]

        num_detections = random.randint(2, 5)
        
        for i in range(num_detections):
            plate_text = random.choice(mock_plates)
            confidence = random.uniform(0.75, 0.95)

            x1 = random.randint(100, 200)
            y1 = random.randint(100, 200)
            x2 = x1 + random.randint(80, 120)
            y2 = y1 + random.randint(30, 50)

            mock_crop = np.zeros((y2 - y1, x2 - x1, 3), dtype=np.uint8)
            mock_crop[:, :] = [random.randint(50, 200) for _ in range(3)]

            detection = {
                "plate": plate_text,
                "normalized_plate": normalize_plate(plate_text),
                "confidence": confidence,
                "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                "frame_no": i * 30,
                "captured_at": datetime.utcnow(),
                "crop": mock_crop,
                "camera_id": camera_id,
            }

            yield detection
            logger.info("Mock detection generated", plate=plate_text, confidence=confidence)

        logger.info(
            "Video processing complete (mock mode)",
            mock_detections=num_detections,
        )


def process_video(video_path: str, camera_id: str = None) -> Generator[Dict[str, Any], None, None]:
    detector = MockDetector()
    yield from detector.process_video(video_path, camera_id)
