# PHASE 10.1.5: Detailed Rejection Reason Counters

## Problem

The initial Phase 10.1 fix added basic skip tracking, but didn't provide enough granularity to diagnose **why** crops were being rejected. We needed:

1. Separate counters for each rejection reason
2. Sample failures with bbox information for forensic analysis
3. Computed crop dimensions to identify bbox/sizing issues

## Changes Made

### Updated `src/worker.py`

#### A) Enhanced Job Processing with Detailed Counters (Lines 57-98)

**Before**:
```python
skipped_no_crop = 0
```

**After**:
```python
skip_counters = {
    "invalid_type": 0,
    "invalid_dims": 0,
    "too_small": 0,
    "solid_color": 0,
    "write_failed": 0,
    "frame_missing": 0,
}
failed_samples = []  # Store first 3 failed crops for forensics
```

**Summary Logging**:
```python
logger.info(
    "Upload processed - Summary",
    job_id=job_id,
    events_created=events_count,
    detections_total=detections_total,
    total_skipped=total_skipped,
    skipped_invalid_type=skip_counters["invalid_type"],
    skipped_invalid_dims=skip_counters["invalid_dims"],
    skipped_too_small=skip_counters["too_small"],
    skipped_solid_color=skip_counters["solid_color"],
    skipped_write_failed=skip_counters["write_failed"],
    skipped_frame_missing=skip_counters["frame_missing"]
)
```

**Failed Samples Logging**:
```python
if failed_samples:
    logger.info(
        "Failed crop samples",
        job_id=job_id,
        sample_count=len(failed_samples),
        samples=failed_samples
    )
```

#### B) Updated `save_event()` Signature (Line 118)

**Before**:
```python
async def save_event(db: AsyncSession, upload: Upload, detection: dict) -> Event:
```

**After**:
```python
async def save_event(
    db: AsyncSession,
    upload: Upload,
    detection: dict,
    skip_counters: dict = None,
    failed_samples: list = None
) -> tuple[Event, str]:
```

Returns tuple of `(Event, skip_reason)` where skip_reason is None on success.

#### C) Added Failure Tracking Helper (Lines 126-141)

```python
def track_failure(reason: str, extra_info: dict = None):
    if skip_counters is not None:
        skip_counters[reason] = skip_counters.get(reason, 0) + 1

    if failed_samples is not None and len(failed_samples) < 3:
        sample = {
            "frame_no": frame_no,
            "bbox": bbox,
            "reason": reason,
            "plate": detection.get("plate", ""),
        }
        if extra_info:
            sample.update(extra_info)
        failed_samples.append(sample)
```

This helper:
- Increments the appropriate counter
- Captures first 3 failures with context
- Includes bbox, frame_no, plate, and reason-specific extra info

#### D) Enhanced Rejection Reasons with Diagnostics

**1. Invalid Type** (Lines 179-186):
```python
track_failure("invalid_type", {"crop_type": type(crop_array).__name__})
return (None, "invalid_type")
```

**2. Invalid Dimensions** (Lines 191-200):
```python
track_failure("invalid_dims", {
    "crop_shape": list(crop_array.shape),
    "crop_width": crop_width,
    "crop_height": crop_height
})
return (None, "invalid_dims")
```

**3. Too Small** (Lines 202-213):
```python
track_failure("too_small", {
    "crop_width": crop_width,
    "crop_height": crop_height,
    "bbox_width": bbox.get("x2", 0) - bbox.get("x1", 0),
    "bbox_height": bbox.get("y2", 0) - bbox.get("y1", 0)
})
return (None, "too_small")
```

**4. Solid Color** (Lines 230-241):
```python
track_failure("solid_color", {
    "solid_value": crop_min,
    "crop_width": crop_width,
    "crop_height": crop_height
})
return (None, "solid_color")
```

**5. Write Failed** (Lines 257-260):
```python
track_failure("write_failed", {"error": str(e)})
return (None, "write_failed")
```

**6. Frame Missing** (Line 158):
```python
track_failure("frame_missing")
```

## Expected Log Output

### Successful Job
```json
{
  "event": "Upload processed - Summary",
  "job_id": "abc-123",
  "events_created": 15,
  "detections_total": 15,
  "total_skipped": 0,
  "skipped_invalid_type": 0,
  "skipped_invalid_dims": 0,
  "skipped_too_small": 0,
  "skipped_solid_color": 0,
  "skipped_write_failed": 0,
  "skipped_frame_missing": 0
}
```

### Job with Failures
```json
{
  "event": "Upload processed - Summary",
  "job_id": "abc-123",
  "events_created": 10,
  "detections_total": 18,
  "total_skipped": 8,
  "skipped_invalid_type": 0,
  "skipped_invalid_dims": 0,
  "skipped_too_small": 5,
  "skipped_solid_color": 3,
  "skipped_write_failed": 0,
  "skipped_frame_missing": 0
}

{
  "event": "Failed crop samples",
  "job_id": "abc-123",
  "sample_count": 3,
  "samples": [
    {
      "frame_no": 42,
      "bbox": {"x1": 100, "y1": 50, "x2": 103, "y2": 52},
      "reason": "too_small",
      "plate": "ABC123",
      "crop_width": 3,
      "crop_height": 2,
      "bbox_width": 3,
      "bbox_height": 2
    },
    {
      "frame_no": 87,
      "bbox": {"x1": 200, "y1": 100, "x2": 250, "y2": 120},
      "reason": "solid_color",
      "plate": "XYZ789",
      "solid_value": 0,
      "crop_width": 50,
      "crop_height": 20
    },
    {
      "frame_no": 102,
      "bbox": {"x1": 150, "y1": 80, "x2": 152, "y2": 81},
      "reason": "too_small",
      "plate": "DEF456",
      "crop_width": 2,
      "crop_height": 1,
      "bbox_width": 2,
      "bbox_height": 1
    }
  ]
}
```

## Diagnostic Use Cases

### 1. Identify Bbox Issues
If `skipped_too_small` is high and samples show tiny bbox dimensions:
- **Problem**: Remote inference returning invalid bboxes
- **Action**: Check bbox validation in remote service

### 2. Identify Decode Failures
If `skipped_solid_color` is high:
- **Problem**: Frame extraction or crop generation failing
- **Action**: Check ffmpeg extraction, verify frame files exist

### 3. Identify Type Mismatches
If `skipped_invalid_type` or `skipped_invalid_dims` is high:
- **Problem**: Detector not returning numpy arrays or wrong format
- **Action**: Check detector adapter implementation

### 4. Identify Frame Mapping Issues
If `skipped_frame_missing` is high:
- **Problem**: Frame numbers not matching extracted files
- **Action**: Verify Phase 10.1 frame mapping fix is working

## Testing

1. **Run remote inference pipeline** with video upload
2. **Check logs** for summary with all counters
3. **Examine failed samples** if any skips occur
4. **Correlate** bbox dimensions with crop dimensions to identify root cause

## Files Modified

- `src/worker.py` - Added detailed rejection counters and sample tracking

## Benefits

✅ Pinpoint exact failure reasons with separate counters
✅ Forensic analysis of first 3 failures per job
✅ Bbox + crop dimension correlation for sizing issues
✅ Clear visibility into pipeline health
✅ Actionable diagnostics for debugging

## Next Steps

1. Deploy updated worker
2. Monitor logs for skip counter patterns
3. Use failed samples to identify systemic issues
4. Address root causes based on counter distribution
