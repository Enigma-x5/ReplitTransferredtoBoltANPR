import random
import re
import numpy as np
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Generator, Any, Optional
from datetime import datetime

from src.logging_config import get_logger

logger = get_logger(__name__)


def normalize_plate(plate: str) -> str:
    return re.sub(r'[^A-Z0-9]', '', plate.upper())


class MockDetector:
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        self.crops_logged = 0
        self.max_crop_logs = 5
        logger.info("Mock detector initialized", threshold=self.confidence_threshold)

    def _extract_frame_with_ffmpeg(self, video_path: str, frame_no: int) -> Optional[np.ndarray]:
        """Extract a single frame using ffmpeg CLI and load with PIL."""
        try:
            from PIL import Image

            # Create temporary file for extracted frame
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                tmp_path = tmp_file.name

            # Use ffmpeg to extract specific frame
            cmd = [
                'ffmpeg',
                '-y',
                '-i', video_path,
                '-vf', f'select=eq(n\\,{frame_no})',
                '-vframes', '1',
                tmp_path
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )

            if result.returncode != 0 or not Path(tmp_path).exists():
                logger.warning("ffmpeg extraction failed", frame_no=frame_no, returncode=result.returncode)
                Path(tmp_path).unlink(missing_ok=True)
                return None

            logger.info("ffmpeg frame extracted", frame_no=frame_no, tmp_path=tmp_path)

            # Load with PIL and convert to numpy array (RGB)
            img = Image.open(tmp_path)
            frame_rgb = np.array(img)

            # Convert RGB to BGR for OpenCV compatibility
            if frame_rgb.ndim == 3 and frame_rgb.shape[2] == 3:
                frame_bgr = frame_rgb[:, :, ::-1].copy()
            else:
                frame_bgr = frame_rgb

            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)

            logger.info("Frame loaded via ffmpeg+PIL", shape=frame_bgr.shape, dtype=frame_bgr.dtype)
            return frame_bgr

        except Exception as e:
            logger.error("ffmpeg frame extraction failed", frame_no=frame_no, error=str(e))
            return None

    def _extract_real_crop(self, frame: np.ndarray, bbox: dict, frame_no: int) -> Optional[np.ndarray]:
        """Extract real crop from video frame with validation and clamping."""
        if frame is None or not isinstance(frame, np.ndarray):
            logger.warning("Invalid frame, skipping crop", frame_no=frame_no)
            return None

        if frame.ndim != 3 or frame.shape[2] != 3:
            logger.warning("Invalid frame shape, skipping crop", shape=frame.shape, frame_no=frame_no)
            return None

        h, w = frame.shape[:2]
        if h <= 0 or w <= 0:
            logger.warning("Invalid frame dimensions", h=h, w=w, frame_no=frame_no)
            return None

        # Clamp bbox to frame bounds
        x1 = max(0, min(bbox["x1"], w - 1))
        y1 = max(0, min(bbox["y1"], h - 1))
        x2 = max(0, min(bbox["x2"], w))
        y2 = max(0, min(bbox["y2"], h))

        crop_w = x2 - x1
        crop_h = y2 - y1

        if crop_w < 5 or crop_h < 5:
            logger.warning("Crop too small, skipping", w=crop_w, h=crop_h, frame_no=frame_no)
            return None

        # Extract real crop from frame
        crop = frame[y1:y2, x1:x2]

        # Log first N crops for debugging
        if self.crops_logged < self.max_crop_logs:
            logger.info(
                "Crop extracted",
                frame_no=frame_no,
                frame_shape=frame.shape,
                bbox_orig=bbox,
                bbox_clamped={"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                crop_shape=crop.shape
            )
            self.crops_logged += 1

        return crop

    def process_video(
        self, video_path: str, camera_id: str = None
    ) -> Generator[Dict[str, Any], None, None]:
        logger.info("Processing video (mock mode)", video_path=video_path, camera_id=camera_id)

        mock_plates = [
            "ABC123",
            "XYZ789",
            "LMN456",
            "TEST99",
            "DEMO01",
            "MH12AB1234",
            "DL8CAB5678",
        ]

        # Try to decode real video frames with cv2
        cv2_available = False
        cap = None
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.warning("Cannot open video with cv2, will use ffmpeg fallback", path=video_path)
                cap = None
            else:
                cv2_available = True
                logger.info("Using cv2 for frame extraction")
        except (ImportError, AttributeError) as e:
            logger.warning("cv2 not available, using ffmpeg fallback", error=str(e))
            cap = None

        num_detections = random.randint(2, 5)

        for i in range(num_detections):
            plate_text = random.choice(mock_plates)
            confidence = random.uniform(0.75, 0.95)

            frame = None
            frame_no = i * 30

            # Try to read actual frame from video
            if cv2_available and cap is not None:
                # Use cv2 method
                import cv2
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
                ret, frame = cap.read()
                if not ret or frame is None:
                    logger.warning("Failed to read frame with cv2", frame_no=frame_no)
                    frame = None
            else:
                # Use ffmpeg fallback
                frame = self._extract_frame_with_ffmpeg(video_path, frame_no)

            # Generate random bbox that fits within frame if available
            if frame is not None:
                h, w = frame.shape[:2]
                x1 = random.randint(50, max(51, w - 150))
                y1 = random.randint(50, max(51, h - 100))
                x2 = min(x1 + random.randint(80, 120), w - 1)
                y2 = min(y1 + random.randint(30, 50), h - 1)
            else:
                x1 = random.randint(100, 200)
                y1 = random.randint(100, 200)
                x2 = x1 + random.randint(80, 120)
                y2 = y1 + random.randint(30, 50)

            bbox = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}

            # Extract real crop if frame is available
            crop = None
            if frame is not None:
                crop = self._extract_real_crop(frame, bbox, frame_no)

            # Skip detection if we couldn't get a valid crop from real frame
            if crop is None:
                logger.warning("Skipping detection - no valid crop", frame_no=frame_no, plate=plate_text)
                continue

            detection = {
                "plate": plate_text,
                "normalized_plate": normalize_plate(plate_text),
                "confidence": confidence,
                "bbox": bbox,
                "frame_no": frame_no,
                "captured_at": datetime.utcnow(),
                "crop": crop,
                "frame": frame,
                "camera_id": camera_id,
            }

            yield detection
            logger.info("Mock detection generated", plate=plate_text, confidence=confidence)

        if cap is not None:
            cap.release()

        logger.info(
            "Video processing complete (mock mode)",
            mock_detections=num_detections,
        )


def process_video(video_path: str, camera_id: str = None) -> Generator[Dict[str, Any], None, None]:
    detector = MockDetector()
    yield from detector.process_video(video_path, camera_id)
