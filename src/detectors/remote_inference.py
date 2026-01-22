"""
Remote Inference Detector Backend

Calls an external FastAPI inference service via HTTP.
Suitable for Replit environments where torch/YOLO dependencies may be problematic.
"""

import re
import httpx
import time
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
            "REMOTE_DETECTOR_INIT",
            url=self.inference_url,
            url_repr=repr(self.inference_url),
            auth_configured=bool(self.auth_token)
        )

        self._verify_health()

    def _verify_health(self):
        """Verify remote service is reachable via /health endpoint. Fail fast if not."""
        health_url = f"{self.inference_url.rstrip('/')}/health"

        logger.info("REMOTE_HEALTH_CHECK_START", url=health_url, url_repr=repr(health_url))

        try:
            with httpx.Client(timeout=3.0) as client:
                start_time = time.time()
                response = client.get(health_url)
                elapsed_ms = int((time.time() - start_time) * 1000)

                if response.status_code != 200:
                    logger.error(
                        "REMOTE_HEALTH_CHECK_FAILED",
                        url=health_url,
                        status_code=response.status_code,
                        response_text=response.text[:500],
                        elapsed_ms=elapsed_ms
                    )
                    raise RuntimeError(
                        f"Remote inference service health check failed: {response.status_code} - {response.text[:200]}"
                    )

                logger.info(
                    "REMOTE_HEALTH_CHECK_OK",
                    url=health_url,
                    status_code=response.status_code,
                    elapsed_ms=elapsed_ms
                )

        except httpx.TimeoutException as e:
            logger.error(
                "REMOTE_HEALTH_CHECK_TIMEOUT",
                url=health_url,
                error=str(e),
                timeout_seconds=3
            )
            raise RuntimeError(
                f"Remote inference service not reachable (timeout after 3s): {health_url}"
            ) from e
        except httpx.RequestError as e:
            logger.error(
                "REMOTE_HEALTH_CHECK_ERROR",
                url=health_url,
                error=str(e),
                error_type=type(e).__name__
            )
            raise RuntimeError(
                f"Remote inference service not reachable: {health_url} - {str(e)}"
            ) from e

    def process_video(
        self, video_path: str, camera_id: str = None
    ) -> Generator[Dict[str, Any], None, None]:
        """Process video by sending to remote inference service."""
        video_file = Path(video_path)
        if not video_file.exists():
            logger.error("Video file not found", path=video_path)
            raise FileNotFoundError(f"Video file not found: {video_path}")

        filesize_bytes = video_file.stat().st_size
        endpoint = f"{self.inference_url.rstrip('/')}/infer/video"

        logger.info(
            "REMOTE_INFER_REQUEST_START",
            url=endpoint,
            url_repr=repr(endpoint),
            camera_id=camera_id or "unknown",
            video_path=video_path,
            filesize_bytes=filesize_bytes
        )

        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        try:
            start_time = time.time()

            with open(video_file, "rb") as f:
                files = {"file": (video_file.name, f, "video/mp4")}
                data = {"camera_id": camera_id or "unknown"}

                with httpx.Client(timeout=httpx.Timeout(5.0, read=60.0)) as client:
                    response = client.post(
                        endpoint,
                        files=files,
                        data=data,
                        headers=headers
                    )

            elapsed_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "REMOTE_INFER_RESPONSE",
                status_code=response.status_code,
                elapsed_ms=elapsed_ms,
                response_size_bytes=len(response.content)
            )

            if response.status_code != 200:
                logger.error(
                    "REMOTE_INFER_HTTP_ERROR",
                    status_code=response.status_code,
                    response_text=response.text[:1000],
                    elapsed_ms=elapsed_ms
                )
                raise RuntimeError(
                    f"Remote inference failed with status {response.status_code}: {response.text[:200]}"
                )

            result = response.json()

            if "detections" not in result:
                logger.error(
                    "REMOTE_INFER_INVALID_RESPONSE",
                    response_keys=list(result.keys()),
                    response_preview=str(result)[:500]
                )
                raise ValueError("Remote inference response missing 'detections' field")

            detections_list = result["detections"]
            logger.info(
                "REMOTE_INFER_SUCCESS",
                detections_count=len(detections_list),
                elapsed_ms=elapsed_ms
            )

            for idx, detection_data in enumerate(detections_list):
                plate = detection_data.get("plate", "")
                confidence = detection_data.get("confidence", 0.0)
                bbox = detection_data.get("bbox", {})
                frame_no = detection_data.get("frame_no", 0)

                detection = {
                    "plate": plate,
                    "normalized_plate": normalize_plate(plate),
                    "confidence": confidence,
                    "bbox": bbox,
                    "frame_no": frame_no,
                    "captured_at": datetime.utcnow(),
                    "crop": None,
                    "frame": None,
                    "camera_id": camera_id,
                }

                yield detection

                logger.info(
                    "REMOTE_DETECTION_YIELDED",
                    detection_idx=idx,
                    plate=plate,
                    confidence=confidence,
                    frame_no=frame_no
                )

            logger.info(
                "REMOTE_INFER_COMPLETE",
                total_detections=len(detections_list),
                total_elapsed_ms=elapsed_ms
            )

        except httpx.TimeoutException as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "REMOTE_INFER_TIMEOUT",
                error=str(e),
                error_type=type(e).__name__,
                elapsed_ms=elapsed_ms,
                endpoint=endpoint
            )
            raise RuntimeError(f"Remote inference timeout after {elapsed_ms}ms: {str(e)}") from e

        except httpx.RequestError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "REMOTE_INFER_REQUEST_ERROR",
                error=str(e),
                error_type=type(e).__name__,
                elapsed_ms=elapsed_ms,
                endpoint=endpoint
            )
            raise RuntimeError(f"Remote inference request error: {str(e)}") from e

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000) if 'start_time' in locals() else 0
            logger.error(
                "REMOTE_INFER_ERROR",
                error=str(e),
                error_type=type(e).__name__,
                elapsed_ms=elapsed_ms
            )
            raise


def process_video(video_path: str, camera_id: str = None) -> Generator[Dict[str, Any], None, None]:
    """Entry point for detector adapter."""
    detector = RemoteInferenceDetector()
    yield from detector.process_video(video_path, camera_id)
