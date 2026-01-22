# Phase 10: Frame-Based Remote Inference - COMPLETE

## Summary

Remote inference now sends **extracted frames (JPEG)** to the inference service instead of full video files.

## Implementation Complete

### ✅ Files Modified

1. **`src/config.py`**
   - Added `REMOTE_FRAME_BATCH_SIZE: int = 8`
   - Added `REMOTE_FRAME_TIMEOUT_S: int = 90`

2. **`src/detectors/remote_inference.py`**
   - Complete rewrite for frame-based inference
   - `_extract_frames()`: Extracts frames using ffmpeg at configured FPS
   - `_send_frame_batch()`: Sends frames to POST `/infer/frames`
   - `process_video()`: Orchestrates extraction, batching, and yielding

3. **`.replit`**
   - `DETECTOR_BACKEND = "remote"`
   - `REMOTE_INFERENCE_URL = "https://follow-specialized-borough-myth.trycloudflare.com"`
   - `REMOTE_FRAME_BATCH_SIZE = "8"`
   - `REMOTE_FRAME_TIMEOUT_S = "90"`
   - `FRAME_EXTRACTION_FPS = "1"`

4. **`scripts/detector_smoketest.py`**
   - Shows frame-based configuration
   - Checks ffmpeg availability
   - Notes POST `/infer/frames` endpoint

### ✅ New Features

**Frame Extraction**
- Uses ffmpeg to extract frames at `FRAME_EXTRACTION_FPS` (default: 1 FPS)
- Stores frames as JPEG in temp directory: `frame_000001.jpg`, `frame_000002.jpg`, ...
- High-quality JPEG compression (`-q:v 2`)
- Automatic cleanup after processing

**Batch Processing**
- Sends frames in batches of `REMOTE_FRAME_BATCH_SIZE` (default: 8)
- Configurable timeout per batch: `REMOTE_FRAME_TIMEOUT_S` (default: 90s)
- Connect timeout: 5s, Read timeout: configurable

**Request Format**
```bash
POST {REMOTE_INFERENCE_URL}/infer/frames

multipart/form-data:
  camera_id: <camera_id>
  files: <multiple JPEG files>
```

**Response Format**
```json
{
  "detections_by_frame": {
    "0": [
      {
        "bbox": {"x1": 100, "y1": 50, "x2": 200, "y2": 100},
        "confidence": 0.85,
        "plate": "ABC123",
        "normalized_plate": "ABC123"
      }
    ],
    "1": [],
    "2": [...]
  },
  "meta": {...}
}
```

### ✅ Observability

**New Log Events**
- `FRAME_EXTRACTION_START` - Frame extraction begins
- `FRAME_EXTRACTION_COMPLETE` - Frames extracted with count and timing
- `REMOTE_FRAME_BATCH_START` - Batch send begins
- `REMOTE_FRAME_BATCH_DONE` - Batch processed successfully
- `REMOTE_FRAME_BATCH_ERROR` - Batch failed (with error_type and message)
- `REMOTE_DETECTION_YIELDED` - Detection yielded to worker
- `REMOTE_INFER_COMPLETE` - All batches processed
- `REMOTE_INFER_CLEANUP` - Temp directory cleaned up

**Log Fields**
- `batch_index`: Batch number (0, 1, 2, ...)
- `batch_size`: Frames in this batch
- `url`: Endpoint URL
- `elapsed_ms`: Time taken
- `detections_returned`: Detections from this batch
- `frames_processed`: Frames in response
- `error_type`: Type of error (timeout, http_error, request_error, invalid_response)
- `message`: Error details

### ✅ Pipeline Integration

**Detection Output Format** (unchanged)
```python
{
    "plate": "ABC123",
    "normalized_plate": "ABC123",
    "confidence": 0.85,
    "bbox": {"x1": 100, "y1": 50, "x2": 200, "y2": 100},
    "frame_no": 0,
    "captured_at": datetime.utcnow(),
    "crop": None,      # Pipeline generates locally using bbox
    "frame": None,
    "camera_id": "cam1"
}
```

The worker pipeline continues to:
- Generate crops locally from bbox
- Create events in database
- Handle HITL flow
- Store objects in MinIO

## Remote Service Requirements

Your remote inference service must implement:

### GET /health
Health check (already supported)

### POST /infer/frames (NEW)

**Request:**
- Content-Type: `multipart/form-data`
- Form fields:
  - `camera_id`: string
  - `files`: multiple JPEG files (field name must be "files")

**Response:**
```json
{
  "detections_by_frame": {
    "0": [
      {
        "bbox": {"x1": int, "y1": int, "x2": int, "y2": int},
        "confidence": float,
        "plate": string,
        "normalized_plate": string (optional)
      }
    ]
  },
  "meta": {
    "frames_processed": int,
    "total_detections": int
  }
}
```

**Notes:**
- Frame indices must be 0-based integers matching file order
- Empty arrays for frames with no detections
- `normalized_plate` is optional (computed locally if missing)

## Testing

### Smoke Test
```bash
python scripts/detector_smoketest.py
```

Expected output:
```
==============================================================
DETECTOR SMOKE TEST
==============================================================

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
! REMOTE INFERENCE MODE (Frame-based)
! Requires: Remote inference service running and accessible
! Endpoint: POST /infer/frames
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Testing remote inference backend (frame-based)...
✓ Remote URL configured: https://follow-specialized-borough-myth.trycloudflare.com
  Frame batch size: 8
  Frame timeout: 90s
  FPS: 1
✓ ffmpeg found at: /nix/store/.../bin/ffmpeg
  Initializing detector (includes health check)...
✓ Remote inference detector initialized successfully
✓ Health check passed (GET /health)
  Note: Frame inference uses POST /infer/frames

==============================================================
✓ SMOKE TEST PASSED
==============================================================
```

## Benefits

1. **Reduced Bandwidth**: Send only extracted frames vs full video
2. **Better Control**: Configure batch size, timeout, FPS independently
3. **Faster Feedback**: Start getting results from first batch
4. **Network Resilience**: Smaller requests less likely to fail
5. **Cost Optimization**: Only send frames at desired FPS
6. **Easier Debugging**: Inspect individual frames and batches
7. **Observability**: Detailed logs per batch

## Configuration Tuning

### Batch Size
- **Small (1-4)**: Lower latency, more requests
- **Medium (8-16)**: Balanced (recommended)
- **Large (32+)**: Higher throughput, risk of timeouts

### Timeout
- **30s**: Fast networks, small batches, GPU inference
- **60s**: Typical networks, medium batches
- **90s**: Conservative (default)
- **120s+**: Very large batches or slow CPU

### FPS
- **0.5-1**: Fewer frames, faster (default: 1)
- **2-5**: Better coverage, more processing

## Next Steps

1. Ensure your remote service implements POST `/infer/frames`
2. Update remote service to return `detections_by_frame` format
3. Test with sample video upload
4. Monitor logs for performance
5. Tune batch size and timeout based on results

## Compatibility Notes

**Breaking Changes:**
- Remote service MUST implement POST `/infer/frames`
- Response format changed from `{"detections": [...]}` to `{"detections_by_frame": {...}}`

**Non-Breaking:**
- Detection format to worker unchanged
- Database schema unchanged
- Frontend unchanged
- Worker job processing unchanged

The old POST `/infer/video` endpoint is no longer used but can remain for backward compatibility.
