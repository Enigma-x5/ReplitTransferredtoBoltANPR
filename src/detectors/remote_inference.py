"""
Remote Inference Detector Backend

Calls an external FastAPI inference service via HTTP.
Suitable for Replit environments where torch/YOLO dependencies may be problematic.

Phase 10 Update: Sends extracted frames (JPEG) instead of full video.
"""

import re
import httpx
import time
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Generator, Any, List
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
        self.frame_batch_size = settings.REMOTE_FRAME_BATCH_SIZE
        self.frame_timeout_s = settings.REMOTE_FRAME_TIMEOUT_S
        self.fps = settings.FRAME_EXTRACTION_FPS

        if not self.inference_url:
            raise ValueError("REMOTE_INFERENCE_URL must be set for remote backend")

        logger.info(
            "REMOTE_DETECTOR_INIT",
            url=self.inference_url,
            url_repr=repr(self.inference_url),
            auth_configured=bool(self.auth_token),
            frame_batch_size=self.frame_batch_size,
            frame_timeout_s=self.frame_timeout_s,
            fps=self.fps
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

    def _extract_frames(self, video_path: str, output_dir: Path) -> List[Path]:
        """
        Extract frames from video using ffmpeg at configured FPS.
        Returns list of frame paths.
        """
        logger.info(
            "FRAME_EXTRACTION_START",
            video_path=video_path,
            output_dir=str(output_dir),
            fps=self.fps
        )

        start_time = time.time()

        # Use ffmpeg to extract frames
        # Output pattern: frame_000001.jpg, frame_000002.jpg, ...
        output_pattern = str(output_dir / "frame_%06d.jpg")

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"fps={self.fps}",
            "-q:v", "2",
            output_pattern,
            "-hide_banner",
            "-loglevel", "error"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=120
            )

            elapsed_ms = int((time.time() - start_time) * 1000)

            # Get list of extracted frames
            frame_files = sorted(output_dir.glob("frame_*.jpg"))

            logger.info(
                "FRAME_EXTRACTION_COMPLETE",
                frames_extracted=len(frame_files),
                elapsed_ms=elapsed_ms,
                fps=self.fps
            )

            return frame_files

        except subprocess.TimeoutExpired as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "FRAME_EXTRACTION_TIMEOUT",
                video_path=video_path,
                elapsed_ms=elapsed_ms,
                timeout_s=120
            )
            raise RuntimeError(f"Frame extraction timeout after 120s") from e

        except subprocess.CalledProcessError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "FRAME_EXTRACTION_ERROR",
                video_path=video_path,
                error=e.stderr,
                returncode=e.returncode,
                elapsed_ms=elapsed_ms
            )
            raise RuntimeError(f"Frame extraction failed: {e.stderr}") from e

    def _send_frame_batch(
        self,
        frame_paths: List[Path],
        batch_index: int,
        camera_id: str
    ) -> Dict[str, Any]:
        """
        Send a batch of frames to remote inference endpoint.
        Returns detections_by_frame dict.
        """
        endpoint = f"{self.inference_url.rstrip('/')}/infer/frames"

        logger.info(
            "REMOTE_FRAME_BATCH_START",
            batch_index=batch_index,
            batch_size=len(frame_paths),
            url=endpoint,
            url_repr=repr(endpoint),
            camera_id=camera_id
        )

        start_time = time.time()

        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        try:
            # Prepare multipart form-data with multiple files
            files = []
            for frame_path in frame_paths:
                files.append(
                    ("files", (frame_path.name, open(frame_path, "rb"), "image/jpeg"))
                )

            data = {"camera_id": camera_id or "unknown"}

            timeout = httpx.Timeout(5.0, read=self.frame_timeout_s)

            with httpx.Client(timeout=timeout) as client:
                response = client.post(
                    endpoint,
                    files=files,
                    data=data,
                    headers=headers
                )

            # Close file handles
            for _, (_, file_obj, _) in files:
                file_obj.close()

            elapsed_ms = int((time.time() - start_time) * 1000)

            if response.status_code != 200:
                logger.error(
                    "REMOTE_FRAME_BATCH_ERROR",
                    batch_index=batch_index,
                    error_type="http_error",
                    message=f"Status {response.status_code}: {response.text[:200]}",
                    status_code=response.status_code,
                    response_text=response.text[:1000],
                    elapsed_ms=elapsed_ms
                )
                raise RuntimeError(
                    f"Remote frame batch inference failed with status {response.status_code}: {response.text[:200]}"
                )

            result = response.json()

            # Validate response structure
            if "detections_by_frame" not in result:
                logger.error(
                    "REMOTE_FRAME_BATCH_ERROR",
                    batch_index=batch_index,
                    error_type="invalid_response",
                    message="Response missing 'detections_by_frame' field",
                    response_keys=list(result.keys()),
                    response_preview=str(result)[:500]
                )
                raise ValueError("Remote inference response missing 'detections_by_frame' field")

            detections_by_frame = result["detections_by_frame"]
            total_detections = sum(len(dets) for dets in detections_by_frame.values())

            logger.info(
                "REMOTE_FRAME_BATCH_DONE",
                batch_index=batch_index,
                status_code=response.status_code,
                elapsed_ms=elapsed_ms,
                detections_returned=total_detections,
                frames_processed=len(detections_by_frame)
            )

            return result

        except httpx.TimeoutException as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "REMOTE_FRAME_BATCH_ERROR",
                batch_index=batch_index,
                error_type="timeout",
                message=str(e),
                elapsed_ms=elapsed_ms,
                timeout_s=self.frame_timeout_s
            )
            raise RuntimeError(f"Remote frame batch timeout after {elapsed_ms}ms") from e

        except httpx.RequestError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "REMOTE_FRAME_BATCH_ERROR",
                batch_index=batch_index,
                error_type="request_error",
                message=str(e),
                elapsed_ms=elapsed_ms
            )
            raise RuntimeError(f"Remote frame batch request error: {str(e)}") from e

    def process_video(
        self, video_path: str, camera_id: str = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Process video by extracting frames and sending them to remote inference service.
        Phase 10: Frame-based inference instead of full video upload.
        """
        video_file = Path(video_path)
        if not video_file.exists():
            logger.error("Video file not found", path=video_path)
            raise FileNotFoundError(f"Video file not found: {video_path}")

        filesize_bytes = video_file.stat().st_size

        logger.info(
            "REMOTE_INFER_REQUEST_START",
            camera_id=camera_id or "unknown",
            video_path=video_path,
            filesize_bytes=filesize_bytes,
            fps=self.fps,
            batch_size=self.frame_batch_size
        )

        overall_start = time.time()
        temp_dir = None

        try:
            # Create temp directory for frames
            temp_dir = Path(tempfile.mkdtemp(prefix="anpr_frames_"))

            # Extract frames from video
            frame_paths = self._extract_frames(video_path, temp_dir)

            if not frame_paths:
                logger.warning(
                    "REMOTE_INFER_NO_FRAMES",
                    video_path=video_path,
                    camera_id=camera_id
                )
                return

            logger.info(
                "REMOTE_INFER_FRAMES_EXTRACTED",
                total_frames=len(frame_paths),
                temp_dir=str(temp_dir)
            )

            # Process frames in batches
            total_detections = 0
            batch_count = 0

            for i in range(0, len(frame_paths), self.frame_batch_size):
                batch_frames = frame_paths[i:i + self.frame_batch_size]
                batch_index = batch_count

                result = self._send_frame_batch(batch_frames, batch_index, camera_id or "unknown")

                # Parse detections from response
                detections_by_frame = result.get("detections_by_frame", {})

                # Yield detections in expected format
                for frame_idx_str, detections_list in detections_by_frame.items():
                    frame_idx = int(frame_idx_str)

                    for detection_data in detections_list:
                        plate = detection_data.get("plate", "")
                        confidence = detection_data.get("confidence", 0.0)
                        bbox = detection_data.get("bbox", {})

                        detection = {
                            "plate": plate,
                            "normalized_plate": detection_data.get("normalized_plate") or normalize_plate(plate),
                            "confidence": confidence,
                            "bbox": bbox,
                            "frame_no": frame_idx,
                            "captured_at": datetime.utcnow(),
                            "crop": None,
                            "frame": None,
                            "camera_id": camera_id,
                        }

                        yield detection
                        total_detections += 1

                        logger.info(
                            "REMOTE_DETECTION_YIELDED",
                            detection_idx=total_detections,
                            plate=plate,
                            confidence=confidence,
                            frame_no=frame_idx,
                            batch_index=batch_index
                        )

                batch_count += 1

            elapsed_ms = int((time.time() - overall_start) * 1000)

            logger.info(
                "REMOTE_INFER_COMPLETE",
                total_detections=total_detections,
                total_frames=len(frame_paths),
                total_batches=batch_count,
                total_elapsed_ms=elapsed_ms
            )

        except Exception as e:
            elapsed_ms = int((time.time() - overall_start) * 1000)
            logger.error(
                "REMOTE_INFER_ERROR",
                error=str(e),
                error_type=type(e).__name__,
                elapsed_ms=elapsed_ms,
                video_path=video_path
            )
            raise

        finally:
            # Cleanup temp directory
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                    logger.info("REMOTE_INFER_CLEANUP", temp_dir=str(temp_dir))
                except Exception as cleanup_error:
                    logger.warning(
                        "REMOTE_INFER_CLEANUP_FAILED",
                        temp_dir=str(temp_dir),
                        error=str(cleanup_error)
                    )


def process_video(video_path: str, camera_id: str = None) -> Generator[Dict[str, Any], None, None]:
    """Entry point for detector adapter."""
    detector = RemoteInferenceDetector()
    yield from detector.process_video(video_path, camera_id)
