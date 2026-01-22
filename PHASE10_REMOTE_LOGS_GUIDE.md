# Phase 10 Remote Inference - Log Analysis Guide

## Quick Diagnosis

### When Remote Service is WORKING ✓

You should see this sequence in worker logs:

```
REMOTE_DETECTOR_INIT             url=https://... auth_configured=False
REMOTE_HEALTH_CHECK_START        url=https://.../health
REMOTE_HEALTH_CHECK_OK           status_code=200 elapsed_ms=234
Detector adapter initialized     backend=remote threshold=0.30
```

Then for each video upload:

```
REMOTE_INFER_REQUEST_START       url=https://.../infer/video camera_id=cam1 filesize_bytes=1048576
REMOTE_INFER_RESPONSE            status_code=200 elapsed_ms=3456 response_size_bytes=2048
REMOTE_INFER_SUCCESS             detections_count=3 elapsed_ms=3456
REMOTE_DETECTION_YIELDED         detection_idx=0 plate=ABC123 confidence=0.95 frame_no=30
REMOTE_DETECTION_YIELDED         detection_idx=1 plate=XYZ789 confidence=0.87 frame_no=45
REMOTE_DETECTION_YIELDED         detection_idx=2 plate=DEF456 confidence=0.92 frame_no=60
REMOTE_INFER_COMPLETE            total_detections=3 total_elapsed_ms=3456
Event saved                      event_id=... plate=ABC123
Event saved                      event_id=... plate=XYZ789
Event saved                      event_id=... plate=DEF456
Upload processed                 job_id=... events=3
```

### When Remote Service is UNREACHABLE ✗

Worker logs will show:

```
REMOTE_DETECTOR_INIT             url=https://... auth_configured=False
REMOTE_HEALTH_CHECK_START        url=https://.../health
REMOTE_HEALTH_CHECK_TIMEOUT      url=https://.../health error=... timeout_seconds=3
Job processing failed            job_id=... error=Remote inference service not reachable (timeout after 3s): https://.../health
Upload processed                 status=FAILED error_message=Remote inference service not reachable...
```

**What to check:**
- Is the CloudFlare tunnel still running?
- Is the inference service process alive?
- Is the URL correct (no trailing space)?
- Can you curl the health endpoint manually?

### When Remote Service Returns Non-200 Status ✗

```
REMOTE_INFER_REQUEST_START       url=https://.../infer/video camera_id=cam1 filesize_bytes=1048576
REMOTE_INFER_RESPONSE            status_code=500 elapsed_ms=234
REMOTE_INFER_HTTP_ERROR          status_code=500 response_text=Internal Server Error elapsed_ms=234
Job processing failed            job_id=... error=Remote inference failed with status 500: Internal Server Error
```

**What to check:**
- Check inference service logs for errors
- Verify the service can process videos
- Check if the service has required dependencies

### When Remote Service Returns Invalid Response ✗

```
REMOTE_INFER_REQUEST_START       url=https://.../infer/video camera_id=cam1 filesize_bytes=1048576
REMOTE_INFER_RESPONSE            status_code=200 elapsed_ms=234
REMOTE_INFER_INVALID_RESPONSE    response_keys=['error', 'message'] response_preview={'error': 'Failed to process'}
Job processing failed            job_id=... error=Remote inference response missing 'detections' field
```

**What to check:**
- Inference service must return JSON with "detections" array
- Check inference service implementation
- Verify API contract matches expectations

### When Remote Service Times Out ✗

```
REMOTE_INFER_REQUEST_START       url=https://.../infer/video camera_id=cam1 filesize_bytes=1048576
REMOTE_INFER_TIMEOUT             error=... elapsed_ms=60234 endpoint=https://.../infer/video
Job processing failed            job_id=... error=Remote inference timeout after 60234ms: ...
```

**What to check:**
- Video processing taking >60s (read timeout)
- Inference service may be overloaded
- Consider optimizing inference service
- Or increase read timeout if legitimately needed

### When Remote Service Has No Detections ✓

This is NOT an error - it means the video had no license plates:

```
REMOTE_INFER_REQUEST_START       url=https://.../infer/video camera_id=cam1 filesize_bytes=1048576
REMOTE_INFER_RESPONSE            status_code=200 elapsed_ms=2345
REMOTE_INFER_SUCCESS             detections_count=0 elapsed_ms=2345
REMOTE_INFER_COMPLETE            total_detections=0 total_elapsed_ms=2345
Upload processed                 job_id=... events=0
```

**This is normal** - the video just didn't contain any plates.

## Timeout Reference

| Operation | Timeout | Reason |
|-----------|---------|--------|
| Health Check (connect+read) | 3s | Fast startup validation |
| Video Upload (connect) | 5s | Fail fast on connection issues |
| Video Upload (read) | 60s | Allow time for inference processing |

## Configuration Check

In `.replit` or environment:

```bash
DETECTOR_BACKEND=remote
REMOTE_INFERENCE_URL=https://quick-institutions-assistance-write.trycloudflare.com
REMOTE_INFERENCE_TOKEN=  # empty = no auth
```

**Common mistakes:**
- Trailing space in URL (will cause 404)
- Wrong protocol (http vs https)
- Forgetting to start CloudFlare tunnel
- Tunnel URL expired (cloudflare.com tunnels are temporary)

## Testing Remote Service Manually

```bash
# Test health endpoint
curl -v https://quick-institutions-assistance-write.trycloudflare.com/health

# Expected: 200 OK

# Test inference endpoint
curl -v -F "file=@test_video.mp4" -F "camera_id=test" \
  https://quick-institutions-assistance-write.trycloudflare.com/infer/video

# Expected: 200 OK with JSON {"detections": [...]}
```

## Worker Flow

```
1. Worker starts
   └─> Detector initialized (health check runs ONCE)
       ├─> ✓ Success: Ready to process jobs
       └─> ✗ Failure: Worker exits immediately

2. Job dequeued
   └─> Video sent to remote service
       ├─> ✓ Success: Detections returned → Events created
       └─> ✗ Failure: Upload marked FAILED with error message

3. Next job...
   └─> No health check (already validated)
```

## UI/Database Visibility

Failed uploads are visible in:
- **Database**: `uploads` table, `status='FAILED'`, `error_message` populated
- **API**: GET /api/uploads shows failed uploads with error messages
- **Frontend**: Uploads page shows status and error
- **Logs**: Worker logs show full error details

## Debugging Checklist

When uploads stay in PROCESSING or fail:

1. ✓ Check worker logs for `REMOTE_INFER_*` messages
2. ✓ Verify health check passed at worker startup
3. ✓ Check elapsed_ms values (slow network? slow inference?)
4. ✓ Verify remote service logs (if accessible)
5. ✓ Test health endpoint manually with curl
6. ✓ Test inference endpoint manually with sample video
7. ✓ Check for trailing spaces in REMOTE_INFERENCE_URL
8. ✓ Verify CloudFlare tunnel is still active
9. ✓ Check database: SELECT * FROM uploads WHERE status='FAILED'
10. ✓ Check API: curl http://localhost:8000/api/uploads

## Success Criteria

A successful end-to-end flow shows:
- Health check passes in <3s
- Video upload completes in <60s
- Response includes "detections" array
- Each detection creates an Event
- Upload status = DONE
- No error logs

If any step fails, logs will show exactly where and why.
