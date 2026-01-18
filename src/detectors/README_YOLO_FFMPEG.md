# YOLO + EasyOCR Detector with FFmpeg Frame Extraction

## Overview

This detector provides real license plate detection and OCR using:
- **YOLO** (ultralytics) for license plate detection
- **EasyOCR** for text recognition
- **ffmpeg** for reliable video frame extraction (avoids cv2 issues in Replit)

## Usage

Set environment variable:
```bash
DETECTOR_BACKEND=yolo_ffmpeg
```

## Configuration

All configuration is via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `YOLO_MODEL` | `keremberke/yolov8n-license-plate` | YOLO model to use for detection |
| `DETECT_CONFIDENCE` | `0.30` | Minimum detection confidence threshold |
| `FRAME_EXTRACTION_FPS` | `1` | Frames per second to extract from video |
| `DEVICE` | `cuda` (if available) else `cpu` | Device for inference |
| `MIN_BOX_WIDTH` | `20` | Minimum bounding box width |
| `MIN_BOX_HEIGHT` | `10` | Minimum bounding box height |

## Architecture

### Frame Extraction (ffmpeg)
1. Video is processed with ffmpeg CLI to extract frames at specified FPS
2. Frames are saved as JPEG files in a temporary directory
3. No cv2 dependency required - works reliably in Replit

### Detection (YOLO)
1. Each extracted frame is loaded with PIL and converted to numpy
2. YOLO model runs inference to detect license plate bounding boxes
3. Detections are filtered by confidence threshold and minimum size

### OCR (EasyOCR)
1. Each detected license plate region is cropped with small padding
2. EasyOCR reads text from the cropped region
3. If no text is detected, plate is marked as "UNREAD"

## Output Format

Each detection yields a dictionary with:
- `plate`: Raw OCR text (or "UNREAD")
- `normalized_plate`: Uppercase alphanumeric only
- `confidence`: Detection confidence (from YOLO, not OCR)
- `bbox`: `{x1, y1, x2, y2}` coordinates
- `frame_no`: Frame index (0-based)
- `captured_at`: Timestamp
- `crop`: Numpy array of cropped license plate image
- `camera_id`: Camera identifier

## Logging

The detector logs:
- **Frame extraction count**: Number of frames extracted by ffmpeg
- **Per-frame detection count**: Number of detections in each frame
- **OCR failures count**: Number of plates marked as "UNREAD"
- **OCR success rate**: Percentage of successful OCR reads

## Example Log Output

```json
{
  "message": "Frame extraction complete",
  "frames_extracted": 30,
  "fps": 1
}

{
  "message": "Frame detections",
  "frame_no": 5,
  "detections": 2
}

{
  "message": "Video processing complete",
  "frames_processed": 30,
  "total_detections": 12,
  "ocr_failures": 1,
  "ocr_success_rate": "91.7%"
}
```

## Integration

The detector integrates with the existing pipeline:
1. Upload video via `/api/uploads` endpoint
2. Worker enqueues processing job
3. Detector processes video and yields detections
4. Events are saved to database with crops stored in object storage
5. Review interface displays events with real crops and OCR text

## Dependencies

Required packages (added to requirements.txt):
- `ultralytics==8.0.196` - YOLO models
- `easyocr==1.7.0` - OCR engine
- `torch==2.1.0` - PyTorch backend
- `torchvision==0.16.0` - Vision utilities
- `Pillow` - Image loading (already present)

## Performance Notes

- **CPU Mode**: Works but slow. Expect ~2-5 seconds per frame
- **GPU Mode**: Much faster. Requires CUDA-capable GPU
- **Frame Rate**: Lower FPS = faster processing but fewer detections
- **Model Size**: `yolov8n` is nano/fast, larger models more accurate but slower

## Troubleshooting

**Smoke test fails with ffmpeg timeout (Replit):**
- Fixed in latest version - uses `shutil.which("ffmpeg")` instead of running `ffmpeg --version`
- Version check is now skipped for Replit compatibility
- Smoke test only verifies ffmpeg binary exists in PATH

**No frames extracted:**
- Check ffmpeg is installed: `which ffmpeg`
- Verify video file is valid
- Check ffmpeg logs in stderr

**Low detection count:**
- Lower `DETECT_CONFIDENCE` threshold
- Increase `FRAME_EXTRACTION_FPS` for more frames
- Try a different YOLO model

**Many "UNREAD" plates:**
- OCR quality depends on crop resolution
- Ensure license plates are clearly visible in video
- Consider adjusting min box size thresholds
