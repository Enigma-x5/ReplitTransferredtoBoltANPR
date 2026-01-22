# Phase 10: Remote Inference Detector Backend

## Overview

Added a new detector backend called "remote" that offloads ANPR inference to an external FastAPI service via HTTP. This enables ANPR processing in Replit environments where torch/YOLO dependencies are problematic.

**Latest Update**: Enhanced with explicit logging, fast timeouts, and fail-fast behavior for better observability and debugging.

## Implementation

### New Files

**`src/detectors/remote_inference.py`**
- Implements `RemoteInferenceDetector` class
- **Health check on init**: Verifies `/health` endpoint (3s timeout) - raises error if unreachable
- POSTs video files to remote inference service endpoint
- Sends multipart form-data: `file` (video bytes) + `camera_id`
- **Fast timeouts**: Connect 5s, Read 60s (no silent hangs)
- Supports optional Bearer token authentication
- **Explicit structured logging**:
  - `REMOTE_INFER_REQUEST_START` - before sending (url, camera_id, filesize_bytes)
  - `REMOTE_INFER_RESPONSE` - after response (status_code, elapsed_ms)
  - `REMOTE_INFER_SUCCESS` - on success (detections_count, elapsed_ms)
  - `REMOTE_INFER_ERROR` - on failure (error type, message, elapsed_ms)
  - `REMOTE_DETECTION_YIELDED` - per detection (plate, confidence, frame_no)
- **Response validation**: Ensures "detections" field exists, raises error if missing
- Yields detections in standard format (plate, confidence, bbox, frame_no, etc.)
- Does NOT require crops from remote service (pipeline generates them locally)
- **Fail-fast error handling**: All errors propagate to worker (no silent failures)

### Modified Files

**`src/config.py`**
- Added `REMOTE_INFERENCE_URL` configuration
- Added `REMOTE_INFERENCE_TOKEN` configuration

**`src/services/detector_adapter.py`**
- Added "remote" backend support in `get_detector()`
- **No silent fallback**: Remote backend failures propagate immediately (no mock fallback)
- Added remote config logging in `log_detector_config()`

**`scripts/detector_smoketest.py`**
- Added remote backend health check
- Verifies `REMOTE_INFERENCE_URL` is configured
- Tests detector initialization (includes health check)
- Validates service is reachable before worker starts
- Updated configuration output for remote settings

**`.replit`**
- Set `DETECTOR_BACKEND = "remote"`
- Set `REMOTE_INFERENCE_URL = "https://quick-institutions-assistance-write.trycloudflare.com "`
- Set `REMOTE_INFERENCE_TOKEN = ""`

## Remote Service Requirements

The external inference service must implement:

### Endpoints

1. **POST /infer/video**
   - Accepts multipart form-data
   - Fields:
     - `file`: Video file bytes
     - `camera_id`: Camera identifier string
   - Optional: Bearer token authentication
   - Returns JSON:
     ```json
     {
       "detections": [
         {
           "plate": "ABC123",
           "confidence": 0.95,
           "bbox": {"x1": 100, "y1": 50, "x2": 200, "y2": 80},
           "frame_no": 30
         }
       ],
       "meta": {}
     }
     ```

2. **GET /health**
   - Returns 200 OK when service is available
   - Used by smoketest to verify connectivity

## Configuration

Set environment variables:

```bash
DETECTOR_BACKEND=remote
REMOTE_INFERENCE_URL=https://your-inference-service.example.com
REMOTE_INFERENCE_TOKEN=your-auth-token-here  # optional
```

## Logging & Observability

All remote inference operations produce structured logs with millisecond timings:

### Initialization
- `REMOTE_DETECTOR_INIT` - Detector initialized with URL
- `REMOTE_HEALTH_CHECK_START` - Health check starting
- `REMOTE_HEALTH_CHECK_OK` - Health check succeeded (status_code, elapsed_ms)
- `REMOTE_HEALTH_CHECK_FAILED` - Health check failed (status_code, response_text)
- `REMOTE_HEALTH_CHECK_TIMEOUT` - Health check timed out (timeout=3s)
- `REMOTE_HEALTH_CHECK_ERROR` - Network error during health check

### Video Processing
- `REMOTE_INFER_REQUEST_START` - Before sending video (url, camera_id, filesize_bytes)
- `REMOTE_INFER_RESPONSE` - After receiving response (status_code, elapsed_ms, response_size_bytes)
- `REMOTE_INFER_SUCCESS` - Processing succeeded (detections_count, elapsed_ms)
- `REMOTE_DETECTION_YIELDED` - Per detection (detection_idx, plate, confidence, frame_no)
- `REMOTE_INFER_COMPLETE` - All detections yielded (total_detections, total_elapsed_ms)

### Errors
- `REMOTE_INFER_HTTP_ERROR` - Non-200 status (status_code, response_text, elapsed_ms)
- `REMOTE_INFER_INVALID_RESPONSE` - Missing "detections" field (response_keys)
- `REMOTE_INFER_TIMEOUT` - Request timed out (elapsed_ms, endpoint)
- `REMOTE_INFER_REQUEST_ERROR` - Network error (error_type, error, elapsed_ms)
- `REMOTE_INFER_ERROR` - Other processing error (error_type, error, elapsed_ms)

**All errors propagate to worker** → Upload marked as FAILED → Visible in DB and logs

## Pipeline Behavior

The upload/worker pipeline behavior:
1. Worker initializes detector (health check runs once)
2. Worker sends video to remote service
3. Remote service returns detections (plate, bbox, confidence, frame_no)
4. Worker generates crops locally from bbox + stored video frames
5. Events and crops are processed as usual

**On failure**: Worker catches exception, logs error, marks upload as FAILED with error message

## Benefits

- **Replit-Compatible**: No torch/YOLO dependencies needed
- **Scalable**: Offload compute-intensive inference to dedicated servers
- **Flexible**: Easy to swap inference backends without code changes
- **Secure**: Optional authentication via Bearer tokens
- **Robust**: Automatic fallback to mock detector on failures

## Testing

Run the detector smoketest:

```bash
python3 scripts/detector_smoketest.py
```

For remote backend, this will:
- Verify URL is configured
- Check service is reachable via /health endpoint
- Validate detector can be imported

## Notes

- Remote backend does NOT send crops in response (pipeline generates them)
- **Timeouts**: Connect 5s, Read 60s (fail fast for quicker feedback)
- Health check timeout: 3s
- All existing mock and yolo_ffmpeg backends remain unchanged
- **No silent fallback**: Remote failures propagate immediately (no mock fallback)
- Worker logs show exact failure reason for debugging
- All errors include elapsed time for performance analysis
