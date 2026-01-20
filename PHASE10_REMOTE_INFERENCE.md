# Phase 10: Remote Inference Detector Backend

## Overview

Added a new detector backend called "remote" that offloads ANPR inference to an external FastAPI service via HTTP. This enables ANPR processing in Replit environments where torch/YOLO dependencies are problematic.

## Implementation

### New Files

**`src/detectors/remote_inference.py`**
- Implements `RemoteInferenceDetector` class
- POSTs video files to remote inference service endpoint
- Sends multipart form-data: `file` (video bytes) + `camera_id`
- Supports optional Bearer token authentication
- Parses JSON response with detections array
- Yields detections in standard format (plate, confidence, bbox, frame_no, etc.)
- Does NOT require crops from remote service (pipeline generates them locally)
- Robust error handling with detailed logging

### Modified Files

**`src/config.py`**
- Added `REMOTE_INFERENCE_URL` configuration
- Added `REMOTE_INFERENCE_TOKEN` configuration

**`src/services/detector_adapter.py`**
- Added "remote" backend support in `get_detector()`
- Falls back to mock if remote backend fails
- Added remote config logging in `log_detector_config()`

**`scripts/detector_smoketest.py`**
- Added remote backend health check
- Verifies `REMOTE_INFERENCE_URL` is configured
- Tests connectivity via `GET /health` (3s timeout)
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

## Pipeline Behavior

The upload/worker pipeline remains unchanged:
1. Worker sends video to remote service
2. Remote service returns detections (plate, bbox, confidence, frame_no)
3. Worker generates crops locally from bbox + stored video frames
4. Events and crops are processed as usual

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
- Uses httpx client with 300s timeout for video uploads
- All existing mock and yolo_ffmpeg backends remain unchanged
- Falls back to mock detector if remote service is unavailable
