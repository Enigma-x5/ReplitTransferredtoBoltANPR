# Phase 10 Update: Remote Inference Observability & Fail-Fast

## Changes Summary

Enhanced the remote inference detector backend with comprehensive logging and fail-fast error handling to diagnose issues quickly.

## Modified Files

### 1. `src/detectors/remote_inference.py`

**Added Health Check on Initialization**
- New `_verify_health()` method called during `__init__`
- Tests `GET /health` endpoint with 3s timeout
- Raises `RuntimeError` if service is unreachable
- Prevents silent failures at startup

**Reduced Timeouts**
- Changed from: `timeout=300.0` (5 minutes)
- Changed to: `timeout=httpx.Timeout(5.0, read=60.0)` (connect 5s, read 60s)
- Provides faster feedback on connection issues

**Explicit Structured Logging**
- Added log event before request: `REMOTE_INFER_REQUEST_START`
  - Includes: url, camera_id, video_path, filesize_bytes
- Added log event after response: `REMOTE_INFER_RESPONSE`
  - Includes: status_code, elapsed_ms, response_size_bytes
- Added success log: `REMOTE_INFER_SUCCESS`
  - Includes: detections_count, elapsed_ms
- Added per-detection log: `REMOTE_DETECTION_YIELDED`
  - Includes: detection_idx, plate, confidence, frame_no
- Added completion log: `REMOTE_INFER_COMPLETE`
  - Includes: total_detections, total_elapsed_ms

**Enhanced Error Logging**
- `REMOTE_INFER_HTTP_ERROR` - Non-200 status with response preview
- `REMOTE_INFER_INVALID_RESPONSE` - Missing "detections" field with response keys
- `REMOTE_INFER_TIMEOUT` - Timeout with elapsed_ms and endpoint
- `REMOTE_INFER_REQUEST_ERROR` - Network errors with error type
- `REMOTE_INFER_ERROR` - Generic errors with error type and elapsed time

**Response Validation**
- Now validates that response JSON includes "detections" field
- Raises `ValueError` with helpful message if missing
- Prevents silent failures from malformed responses

**Fail-Fast Error Handling**
- All errors now raise exceptions (no silent returns)
- Worker catches exceptions and marks upload as FAILED
- Error messages visible in database and logs

### 2. `src/services/detector_adapter.py`

**Removed Silent Fallback**
- Remote backend no longer falls back to mock on error
- Exceptions propagate to worker immediately
- Failures are now visible instead of hidden

**Before:**
```python
except Exception as e:
    logger.error("REMOTE_BACKEND_INIT_FAILED", ...)
    logger.warning("Falling back to mock detector...")
    from src.detectors.mock_detector import process_video
    return process_video
```

**After:**
```python
from src.detectors.remote_inference import process_video
return process_video
```

### 3. `scripts/detector_smoketest.py`

**Updated Health Check**
- Now instantiates `RemoteInferenceDetector()` instead of just checking HTTP
- This triggers the actual health check logic
- Verifies detector can initialize before worker starts
- Better matches production behavior

**Before:**
```python
with httpx.Client(timeout=3.0) as client:
    response = client.get(health_url)
    # ... check response
from src.detectors.remote_inference import process_video
```

**After:**
```python
from src.detectors.remote_inference import RemoteInferenceDetector
detector = RemoteInferenceDetector()
# Health check runs during __init__
```

### 4. `.replit`

**Updated Configuration**
- Set `REMOTE_INFERENCE_URL` to CloudFlare tunnel URL
- Set `REMOTE_INFERENCE_TOKEN` to empty (no auth)
- Backend remains `remote`

## New Documentation Files

### 1. `PHASE10_REMOTE_INFERENCE.md`
- Updated with new logging details
- Documents all log events
- Explains fail-fast behavior
- Updated timeout values

### 2. `PHASE10_REMOTE_LOGS_GUIDE.md` (NEW)
- Comprehensive log analysis guide
- Shows expected logs for success vs failure scenarios
- Debugging checklist
- Common mistakes and solutions
- Manual testing commands

### 3. `PHASE10_OBSERVABILITY_UPDATE.md` (THIS FILE)
- Summary of all changes
- Before/after comparisons
- File-by-file change list

## Benefits

### 1. **Visibility**
- Every remote call produces clear logs with timing
- Failures show exactly what went wrong
- No more silent failures or mysterious hangs

### 2. **Speed**
- Fast timeouts (5s connect, 60s read) provide quick feedback
- Health check at startup prevents wasted processing
- Failed uploads marked immediately

### 3. **Debuggability**
- Structured logs include all context needed
- Elapsed times help identify performance issues
- Error types and messages guide troubleshooting

### 4. **Reliability**
- Response validation catches malformed responses
- Health check prevents startup with dead service
- No silent fallbacks hiding problems

## Testing the Changes

### Manual Test 1: Health Check Success
```bash
# Start remote inference service with /health endpoint
python scripts/detector_smoketest.py
# Should show: ✓ Health check passed
```

### Manual Test 2: Health Check Failure
```bash
# Stop remote service or set wrong URL
REMOTE_INFERENCE_URL=https://invalid.example.com python scripts/detector_smoketest.py
# Should show: ✗ Failed to initialize remote detector
```

### Manual Test 3: Video Upload Success
```bash
# Upload video via API with worker running
# Worker logs should show:
# - REMOTE_INFER_REQUEST_START
# - REMOTE_INFER_RESPONSE
# - REMOTE_INFER_SUCCESS
# - REMOTE_DETECTION_YIELDED (for each detection)
# - Upload processed with events count
```

### Manual Test 4: Video Upload Failure
```bash
# Stop remote service mid-processing
# Worker logs should show:
# - REMOTE_INFER_REQUEST_START
# - REMOTE_INFER_TIMEOUT or REMOTE_INFER_REQUEST_ERROR
# - Job processing failed
# - Upload status = FAILED in database
```

## Migration Notes

### For Existing Deployments

1. **No database changes required** - All changes are code-only
2. **No API changes** - Same endpoints and behavior
3. **Environment variables unchanged** - Same config as before
4. **Breaking change**: Remote backend no longer falls back to mock
   - This is intentional to make failures visible
   - If remote service is down, uploads will fail (as they should)

### Configuration Required

Ensure these are set in environment:
```bash
DETECTOR_BACKEND=remote
REMOTE_INFERENCE_URL=https://your-inference-service.example.com
REMOTE_INFERENCE_TOKEN=  # optional, empty for no auth
```

## Log Search Queries

To quickly find issues in production logs:

```bash
# Find remote inference errors
grep "REMOTE_INFER_ERROR" worker.log

# Find slow requests (>10s)
grep "REMOTE_INFER_RESPONSE" worker.log | awk '$3 > 10000'

# Find failed health checks
grep "REMOTE_HEALTH_CHECK_FAILED\|REMOTE_HEALTH_CHECK_TIMEOUT" worker.log

# Find uploads with zero detections
grep "detections_count=0" worker.log

# Find all failed jobs
grep "Job processing failed" worker.log
```

## Next Steps

1. **Start Remote Service**: Ensure inference service is running with /health and /infer/video endpoints
2. **Run Smoketest**: Verify health check passes: `python scripts/detector_smoketest.py`
3. **Start Worker**: Worker will validate health on startup
4. **Monitor Logs**: Watch for `REMOTE_INFER_*` events
5. **Check Failed Uploads**: Query database for uploads with status='FAILED' to see error messages

## Rollback Plan

If issues arise, revert to mock detector:
```bash
DETECTOR_BACKEND=mock
```

This will bypass remote inference entirely and use synthetic test data.
