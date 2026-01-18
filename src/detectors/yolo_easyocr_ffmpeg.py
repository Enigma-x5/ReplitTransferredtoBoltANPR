"""
Real YOLO + EasyOCR detector using ffmpeg for frame extraction.
Avoids cv2 dependency issues in Replit by using ffmpeg CLI for video decoding.
"""
import os
import re
import subprocess
import tempfile
import numpy as np
from pathlib import Path
from typing import Dict, Generator, Any, Optional
from datetime import datetime
from PIL import Image

from src.logging_config import get_logger

logger = get_logger(__name__)


def normalize_plate(plate: str) -> str:
    """Normalize plate text by removing non-alphanumeric characters."""
    return re.sub(r'[^A-Z0-9]', '', plate.upper())


class YOLOEasyOCRFFmpegDetector:
    """
    Real license plate detector using YOLO for detection and EasyOCR for text recognition.
    Uses ffmpeg for reliable frame extraction without cv2 dependency.
    """

    def __init__(
        self,
        model_name: str = None,
        confidence_threshold: float = None,
        fps: int = None,
        device: str = None,
        min_box_width: int = 20,
        min_box_height: int = 10
    ):
        # Load configuration from environment variables
        self.model_name = model_name or os.getenv("YOLO_MODEL", "keremberke/yolov8n-license-plate")
        self.confidence_threshold = confidence_threshold or float(os.getenv("DETECT_CONFIDENCE", "0.30"))
        self.fps = fps or int(os.getenv("FRAME_EXTRACTION_FPS", "1"))
        self.device = device or os.getenv("DEVICE", "cuda" if self._cuda_available() else "cpu")
        self.min_box_width = min_box_width
        self.min_box_height = min_box_height

        logger.info(
            "Initializing YOLO+EasyOCR detector with ffmpeg",
            model=self.model_name,
            confidence=self.confidence_threshold,
            fps=self.fps,
            device=self.device,
            min_box_size=f"{self.min_box_width}x{self.min_box_height}"
        )

        # Lazy load models
        self._yolo_model = None
        self._ocr_reader = None

    def _cuda_available(self) -> bool:
        """Check if CUDA is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    @property
    def yolo_model(self):
        """Lazy load YOLO model."""
        if self._yolo_model is None:
            logger.info("Loading YOLO model", model=self.model_name)
            from ultralytics import YOLO
            self._yolo_model = YOLO(self.model_name)
            logger.info("YOLO model loaded successfully")
        return self._yolo_model

    @property
    def ocr_reader(self):
        """Lazy load EasyOCR reader."""
        if self._ocr_reader is None:
            logger.info("Loading EasyOCR reader", device=self.device)
            import easyocr
            # Use GPU if available, set to False for CPU
            use_gpu = self.device == "cuda"
            self._ocr_reader = easyocr.Reader(['en'], gpu=use_gpu)
            logger.info("EasyOCR reader loaded successfully", gpu=use_gpu)
        return self._ocr_reader

    def _extract_frames_with_ffmpeg(self, video_path: str, temp_dir: Path) -> list[Path]:
        """
        Extract frames from video using ffmpeg at specified FPS.
        Returns list of extracted frame file paths.
        """
        logger.info("Extracting frames with ffmpeg", video=video_path, fps=self.fps, temp_dir=str(temp_dir))

        # Output pattern for extracted frames
        output_pattern = temp_dir / "frame_%04d.jpg"

        # ffmpeg command to extract frames at specified FPS
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f'fps={self.fps}',
            '-q:v', '2',  # High quality JPEG
            str(output_pattern)
        ]

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300,  # 5 minute timeout
                check=True
            )

            # Get list of extracted frames
            frame_files = sorted(temp_dir.glob("frame_*.jpg"))

            logger.info(
                "Frame extraction complete",
                frames_extracted=len(frame_files),
                fps=self.fps
            )

            return frame_files

        except subprocess.CalledProcessError as e:
            logger.error(
                "ffmpeg extraction failed",
                returncode=e.returncode,
                stderr=e.stderr.decode('utf-8', errors='ignore')
            )
            return []
        except subprocess.TimeoutExpired:
            logger.error("ffmpeg extraction timeout", video=video_path)
            return []
        except Exception as e:
            logger.error("Frame extraction error", error=str(e), error_type=type(e).__name__)
            return []

    def _load_frame(self, frame_path: Path) -> Optional[np.ndarray]:
        """Load frame from file using PIL and convert to numpy array."""
        try:
            img = Image.open(frame_path)
            # Convert to RGB numpy array
            frame_rgb = np.array(img)
            return frame_rgb
        except Exception as e:
            logger.error("Failed to load frame", frame=str(frame_path), error=str(e))
            return None

    def _run_ocr(self, crop_image: np.ndarray) -> str:
        """
        Run EasyOCR on cropped license plate region.
        Returns detected text or "UNREAD" if no text detected.
        """
        try:
            # Ensure crop is in RGB format for OCR
            if crop_image.ndim == 3 and crop_image.shape[2] == 3:
                crop_rgb = crop_image
            else:
                logger.warning("Invalid crop dimensions for OCR", shape=crop_image.shape)
                return "UNREAD"

            # Run OCR
            results = self.ocr_reader.readtext(crop_rgb)

            if not results:
                return "UNREAD"

            # Take the detection with highest confidence
            best_text = max(results, key=lambda x: x[2])[1]

            # Clean up the text
            cleaned_text = best_text.strip().upper()

            return cleaned_text if cleaned_text else "UNREAD"

        except Exception as e:
            logger.error("OCR failed", error=str(e), error_type=type(e).__name__)
            return "UNREAD"

    def _process_frame(
        self,
        frame: np.ndarray,
        frame_no: int,
        camera_id: str
    ) -> list[Dict[str, Any]]:
        """
        Process a single frame with YOLO detection and OCR.
        Returns list of detections from this frame.
        """
        detections = []

        try:
            # Run YOLO detection
            results = self.yolo_model(frame, verbose=False)

            if not results or len(results) == 0:
                return detections

            result = results[0]

            if result.boxes is None or len(result.boxes) == 0:
                return detections

            # Process each detected bounding box
            for box in result.boxes:
                try:
                    # Get box coordinates and confidence
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    conf = float(box.conf[0])

                    # Filter by confidence threshold
                    if conf < self.confidence_threshold:
                        continue

                    # Filter by minimum box size
                    box_width = x2 - x1
                    box_height = y2 - y1

                    if box_width < self.min_box_width or box_height < self.min_box_height:
                        logger.debug(
                            "Box too small, skipping",
                            width=box_width,
                            height=box_height,
                            frame_no=frame_no
                        )
                        continue

                    # Add small padding to crop
                    pad = 5
                    h, w = frame.shape[:2]
                    x1_pad = max(0, x1 - pad)
                    y1_pad = max(0, y1 - pad)
                    x2_pad = min(w, x2 + pad)
                    y2_pad = min(h, y2 + pad)

                    # Extract crop
                    crop = frame[y1_pad:y2_pad, x1_pad:x2_pad]

                    if crop.size == 0:
                        logger.warning("Empty crop, skipping", frame_no=frame_no)
                        continue

                    # Run OCR on crop
                    plate_text = self._run_ocr(crop)

                    # Create detection dict
                    detection = {
                        "plate": plate_text,
                        "normalized_plate": normalize_plate(plate_text),
                        "confidence": conf,
                        "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                        "frame_no": frame_no,
                        "captured_at": datetime.utcnow(),
                        "crop": crop,
                        "camera_id": camera_id
                    }

                    detections.append(detection)

                except Exception as e:
                    logger.error(
                        "Error processing detection box",
                        frame_no=frame_no,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    continue

        except Exception as e:
            logger.error(
                "Error processing frame",
                frame_no=frame_no,
                error=str(e),
                error_type=type(e).__name__
            )

        return detections

    def process_video(
        self,
        video_path: str,
        camera_id: str = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Process video file and yield license plate detections.
        Uses ffmpeg for frame extraction, YOLO for detection, EasyOCR for text recognition.
        """
        logger.info(
            "Starting video processing",
            video=video_path,
            camera_id=camera_id,
            backend="yolo_ffmpeg"
        )

        total_detections = 0
        ocr_failures = 0

        # Create temporary directory for frame extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Extract frames with ffmpeg
            frame_files = self._extract_frames_with_ffmpeg(video_path, temp_path)

            if not frame_files:
                logger.warning("No frames extracted, aborting processing", video=video_path)
                return

            logger.info(
                "Processing extracted frames",
                frame_count=len(frame_files),
                fps=self.fps
            )

            # Process each extracted frame
            for frame_idx, frame_path in enumerate(frame_files):
                # Load frame
                frame = self._load_frame(frame_path)

                if frame is None:
                    logger.warning("Failed to load frame, skipping", frame=str(frame_path))
                    continue

                # Process frame with YOLO + OCR
                frame_detections = self._process_frame(frame, frame_idx, camera_id)

                # Log per-frame detection count
                if frame_detections:
                    logger.info(
                        "Frame detections",
                        frame_no=frame_idx,
                        detections=len(frame_detections)
                    )

                # Yield detections and count OCR failures
                for detection in frame_detections:
                    total_detections += 1
                    if detection["plate"] == "UNREAD":
                        ocr_failures += 1
                    yield detection

        # Final summary
        logger.info(
            "Video processing complete",
            video=video_path,
            frames_processed=len(frame_files),
            total_detections=total_detections,
            ocr_failures=ocr_failures,
            ocr_success_rate=f"{((total_detections - ocr_failures) / total_detections * 100) if total_detections > 0 else 0:.1f}%"
        )


def process_video(video_path: str, camera_id: str = None) -> Generator[Dict[str, Any], None, None]:
    """
    Main entry point for YOLO+EasyOCR detector with ffmpeg frame extraction.
    """
    detector = YOLOEasyOCRFFmpegDetector()
    yield from detector.process_video(video_path, camera_id)
