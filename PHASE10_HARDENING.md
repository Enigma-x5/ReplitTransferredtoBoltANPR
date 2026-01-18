# Phase 10 Hardening: Runtime-Safe Detector Configuration

## Overview

Phase 10 hardening adds repo-controlled configuration, fail-safe initialization, and diagnostic tooling to make the YOLO+FFmpeg detector production-ready for Replit deployments where dependencies may be missing or incomplete.

## Changes Summary

### 1. Repo-Tracked Configuration Template

**File:** `config/.env.phase10.example`

A reference-only configuration template for Phase 10 detector settings:
- Not loaded automatically (manual copy to `.env` required)
- Documents all environment variables with defaults and descriptions
- Includes installation notes and activation instructions

**Key Variables:**
```bash
DETECTOR_BACKEND=yolo_ffmpeg
YOLO_MODEL=keremberke/yolov8n-license-plate
DETECT_CONFIDENCE=0.30
DETECTION_CONFIDENCE_THRESHOLD=0.30
FRAME_EXTRACTION_FPS=1
DEVICE=cpu
MIN_BOX_WIDTH=20
MIN_BOX_HEIGHT=10
```

### 2. Fail-Safe Detector Initialization

**File:** `src/services/detector_adapter.py`

Enhanced `get_detector()` function with automatic fallback:

```python
elif backend == "yolo_ffmpeg":
    logger.info("Loading YOLO+EasyOCR detector with ffmpeg frame extraction")
    try:
        from src.detectors.yolo_easyocr_ffmpeg import process_video
        return process_video
    except Exception as e:
        logger.error(
            "YOLO_FFMPEG_BACKEND_INIT_FAILED",
            error=str(e),
            error_type=type(e).__name__,
            fallback="mock",
            hint="Install dependencies: pip install torch ultralytics easyocr"
        )
        logger.warning("Falling back to mock detector due to YOLO_FFMPEG backend init failure")
        from src.detectors.mock_detector import process_video
        return process_video
```

**Behavior:**
- If YOLO/FFmpeg backend imports fail (missing torch, ultralytics, easyocr, etc.)
- Logs clear error: `YOLO_FFMPEG_BACKEND_INIT_FAILED`
- Automatically falls back to mock detector
- Worker still runs (degraded mode) instead of crashing

**Also applies to:** `yolo` backend (cv2-based)

### 3. Startup Configuration Logging

**File:** `src/services/detector_adapter.py` + `src/worker.py`

New function: `log_detector_config()`

Logs effective detector configuration at worker startup:

```json
{
  "message": "Detector configuration",
  "detector_backend": "yolo_ffmpeg",
  "detection_confidence_threshold": 0.7,
  "frame_extraction_fps": 1,
  "yolo_model": "keremberke/yolov8n-license-plate",
  "detect_confidence": "0.30",
  "device": "cpu",
  "min_box_width": "20",
  "min_box_height": "10"
}
```

**Integration:**
- Called automatically in `worker_loop()` on startup
- Backend-specific config only shown for relevant backends
- No secrets logged (all values are non-sensitive detector params)

### 4. Unified FPS Control

**Status:** Already correct in implementation

- `yolo_ffmpeg` backend uses `FRAME_EXTRACTION_FPS` exclusively
- `yolo` backend (cv2-based) uses `FRAME_SKIP` (different parameter)
- No conflicts or confusion between backends

**Usage by backend:**

| Backend | FPS Variable | Description |
|---------|-------------|-------------|
| `mock` | None | Random frames |
| `yolo` | `FRAME_SKIP` | Process every Nth frame with cv2 |
| `yolo_ffmpeg` | `FRAME_EXTRACTION_FPS` | Extract frames at X fps with ffmpeg |

### 5. Smoke Test Script

**File:** `scripts/detector_smoketest.py`

Standalone diagnostic script to verify detector backend before running pipeline:

**Features:**
- Prints effective detector configuration
- Tests backend-specific dependencies
- Validates imports and system tools
- Exit code 0 = success, 1 = failure

**Usage:**
```bash
python scripts/detector_smoketest.py
```

**Example output:**
```
============================================================
DETECTOR SMOKE TEST
============================================================

============================================================
DETECTOR CONFIGURATION
============================================================
  DETECTOR_BACKEND                    = yolo_ffmpeg
  DETECTION_CONFIDENCE_THRESHOLD      = 0.7
  FRAME_EXTRACTION_FPS                = 1
  YOLO_MODEL                          = keremberke/yolov8n-license-plate
  DETECT_CONFIDENCE                   = 0.30
  DEVICE                              = cpu
  MIN_BOX_WIDTH                       = 20
  MIN_BOX_HEIGHT                      = 10
============================================================

Testing detector backend initialization...
Backend: yolo_ffmpeg

Testing YOLO+FFmpeg backend dependencies...
✓ ffmpeg available: ffmpeg version 4.4.2
✓ torch imported (version: 2.1.0)
  CUDA available: False
✓ ultralytics imported
✓ easyocr imported
✓ PIL and numpy imported
✓ YOLO+FFmpeg detector imported successfully

============================================================
✓ SMOKE TEST PASSED
============================================================
The detector backend initialized successfully.
You can now run the worker or upload videos for processing.
```

**Checks per backend:**

| Backend | Checks |
|---------|--------|
| `mock` | Import only (always succeeds) |
| `yolo` | cv2, easyocr, ultralytics imports |
| `yolo_ffmpeg` | ffmpeg binary, torch, ultralytics, easyocr, PIL, numpy imports |

## Workflow

### Development (Bolt)
1. Make all code and config changes in Bolt
2. Commit to repository
3. Push to Replit

### Runtime (Replit)
1. Pull latest code
2. Run smoke test: `python scripts/detector_smoketest.py`
3. If pass: start worker normally
4. If fail: install dependencies or use mock backend
5. Check worker logs for `Detector configuration` at startup

### Troubleshooting

**Scenario 1: Backend fails to init, worker crashes**
- **Before hardening:** Worker crashes on import error
- **After hardening:** Worker falls back to mock, logs error, continues running

**Scenario 2: Unclear why detections don't work**
- **Before hardening:** Must manually check env vars, imports
- **After hardening:** Run `python scripts/detector_smoketest.py` for instant diagnosis

**Scenario 3: Forgot which backend is active**
- **Before hardening:** Must check .env manually
- **After hardening:** Check worker logs on startup for `Detector configuration`

## Error Codes

### YOLO_FFMPEG_BACKEND_INIT_FAILED
- **Cause:** torch, ultralytics, or easyocr import failed
- **Action:** Automatic fallback to mock detector
- **Fix:** `pip install torch ultralytics easyocr`

### YOLO_BACKEND_INIT_FAILED
- **Cause:** cv2, ultralytics, or easyocr import failed
- **Action:** Automatic fallback to mock detector
- **Fix:** `pip install opencv-python-headless ultralytics easyocr`

## Testing

### Test fail-safe fallback:
```bash
# Set backend to yolo_ffmpeg without installing deps
export DETECTOR_BACKEND=yolo_ffmpeg
pip uninstall -y torch ultralytics easyocr

# Worker should start and log YOLO_FFMPEG_BACKEND_INIT_FAILED
python src/worker.py

# Expected: Worker runs with mock detector instead of crashing
```

### Test smoke test:
```bash
# Should fail with helpful messages
export DETECTOR_BACKEND=yolo_ffmpeg
pip uninstall -y torch
python scripts/detector_smoketest.py
# Exit code: 1

# Should pass
pip install torch ultralytics easyocr
python scripts/detector_smoketest.py
# Exit code: 0
```

### Test startup logging:
```bash
# Start worker and check logs
python src/worker.py 2>&1 | grep "Detector configuration"

# Expected output includes all effective config values
```

## Files Modified

1. `src/services/detector_adapter.py`
   - Added try/except with fallback in `get_detector()`
   - Added `log_detector_config()` function

2. `src/worker.py`
   - Added `log_detector_config()` call at startup

## Files Created

1. `config/.env.phase10.example` - Configuration template
2. `scripts/detector_smoketest.py` - Diagnostic script
3. `PHASE10_HARDENING.md` - This document

## Benefits

✅ **No manual Replit edits** - All config in repo
✅ **Worker never crashes** - Automatic fallback to mock
✅ **Clear diagnostics** - Smoke test + startup logging
✅ **Deterministic config** - Template-based, version-controlled
✅ **Safe deployments** - Degraded mode better than failure

## Next Steps

1. Test smoke test script with various dependency states
2. Verify fail-safe fallback in Replit environment
3. Confirm startup logging appears in worker output
4. Update deployment documentation with smoke test step
