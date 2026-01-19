"""
Remote Inference Detector Backend

Calls an external FastAPI inference service via HTTP.
Suitable for Replit environments where torch/YOLO dependencies may be problematic.
"""

import re
import httpx
from pathlib import Path
from typing import Dict, Generator, Any, Optional
from datetime import datetime

from src.config import settings
from src.logging_config import get_logger

logger = get_logger(__name__)


def normalize_plate(plate: str) -> str:
    return re.sub(r'[^A-Z0-9]', '', plate.upper())


class RemoteInferenceDetector:
    def __init__(self, inference_url: str = None, auth_token: str = None):
        self.inference_url = inference_url or settings.REMOTE_INFERENCE_URL
        self.auth_token = auth_token or settings.REMOTE_INFERENCE_TOKEN

        if not self.inference_url:
            raise ValueError("REMOTE_INFERENCE_URL must be set for remote backend")

        logger.info(
            "Remote inference detector initialized",
            url=self.inference_url,
            auth_configured=bool(self.auth_token)
        )

    def process_video(
        self, video_path: str, camera_id: str = None
    ) -> Generator[Dict[str, Any], None, None]:
        """Process video by sending to remote inference service."""
        logger.info(
            "Processing video via remote inference",
            video_path=video_path,
            camera_id=camera_id,
            url=self.inference_url
        )

        video_file = Path(video_path)
        if not video_file.exists():
            logger.error("Video file not found", path=video_path)
            return

        # Prepare headers
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        # Prepare multipart form data
        try:
            with open(video_file, "rb") as f:
                files = {"file": (video_file.name, f, "video/mp4")}
                data = {"camera_id": camera_id or "unknown"}

                # Make HTTP request to remote service
                endpoint = f"{self.inference_url.rstrip('/')}/infer/video"
                logger.info("Sending video to remote inference", endpoint=endpoint)

                with httpx.Client(timeout=300.0) as client:
                    response = client.post(
                        endpoint,
                        files=files,
                        data=data,
                        headers=headers
                    )

                if response.status_code != 200:
                    logger.error(
                        "Remote inference failed",
                        status_code=response.status_code,
                        response=response.text[:500]
                    )
                    return

                # Parse JSON response
                result = response.json()
                logger.info(
                    "Remote inference response received",
                    detections_count=len(result.get("detections", []))
                )

                # Yield detections
                for detection_data in result.get("detections", []):
                    # Extract fields from remote response
                    plate = detection_data.get("plate", "")
                    confidence = detection_data.get("confidence", 0.0)
                    bbox = detection_data.get("bbox", {})
                    frame_no = detection_data.get("frame_no", 0)

                    # Build detection dict in expected format
                    detection = {
                        "plate": plate,
                        "normalized_plate": normalize_plate(plate),
                        "confidence": confidence,
                        "bbox": bbox,
                        "frame_no": frame_no,
                        "captured_at": datetime.utcnow(),
                        "crop": None,  # Remote backend doesn't provide crop
                        "frame": None,  # Remote backend doesn't provide full frame
                        "camera_id": camera_id,
                    }

                    yield detection
                    logger.info(
                        "Remote detection yielded",
                        plate=plate,
                        confidence=confidence,
                        frame_no=frame_no
                    )

                logger.info(
                    "Video processing complete (remote mode)",
                    detections=len(result.get("detections", []))
                )

        except httpx.RequestError as e:
            logger.error(
                "Remote inference request failed",
                error=str(e),
                error_type=type(e).__name__,
                url=self.inference_url
            )
        except Exception as e:
            logger.error(
                "Remote inference error",
                error=str(e),
                error_type=type(e).__name__
            )


def process_video(video_path: str, camera_id: str = None) -> Generator[Dict[str, Any], None, None]:
    """Entry point for detector adapter."""
    detector = RemoteInferenceDetector()
    yield from detector.process_video(video_path, camera_id)
