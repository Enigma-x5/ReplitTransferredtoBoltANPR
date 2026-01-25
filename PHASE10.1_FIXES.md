# PHASE 10.1: Crop Path Null + Frame Mapping Fixes

## Problem Summary

Remote inference returns detections, but worker fails to generate crops and tries to insert events with `crop_path=None`, breaking DB/UI and causing rollbacks/API failures.

## Root Causes Identified

1. **Frame mapping bug**: Remote inference used batch-local frame indices (0..batch_size-1) instead of global frame numbers, causing frame extraction failures
2. **Missing crop validation**: Worker created Events even when crop generation failed, violating DB constraint
3. **No skip counters**: No visibility into why events were being skipped
4. **Schema mismatch**: EventResponse required non-null crop_path, breaking API when null values existed

## Changes Made

### A) Fixed Frame Mapping in `src/detectors/remote_inference.py`

**Issue**: Batch-local frame indices were used as global frame numbers, breaking crop extraction.

**Fix**: Lines 346-394
- Added `batch_global_indices = list(range(i, i + len(batch_frames)))` to track global frame numbers
- Map batch-local index back to global: `global_frame_no = batch_global_indices[batch_local_idx]`
- Added validation for out-of-range indices
- Enhanced logging with both `batch_local_idx` and `global_frame_no`

### B) Updated Worker to Skip Invalid Crops in `src/worker.py`

**Issue**: Events created with null crop_path, violating DB constraints.

**Fix**: Lines 55-73 (process_job)
- Added counters: `detections_total`, `skipped_no_crop`
- Enhanced summary logging with all counts

**Fix**: Lines 151-227 (save_event)
- Return `None` early if crop is not numpy array
- Return `None` early if crop has invalid dimensions
- Return `None` early if crop is too small
- Return `None` early if crop is solid color (decode failure)
- Wrapped upload in try/except, return `None` if upload fails
- Changed log level from ERROR to WARNING for skip cases
- Only create Event if crop_path is valid and upload succeeded

### C) Added API Safety in `src/api/events.py` and `src/schemas/event.py`

**Issue**: API breaks when crop_path is null.

**Fix**: `src/schemas/event.py` line 26
- Changed `crop_path: str` to `crop_path: Optional[str] = None`
- Allows backward compatibility with null values

**Fix**: `src/api/events.py` lines 40-41
- Added filter: `conditions.append(Event.crop_path.isnot(None))`
- Prevents null crop_path events from breaking UI (temporary safety)

### D) Created Cleanup Script `scripts/cleanup_null_crops.py`

**Purpose**: One-time admin utility to delete Events with null crop_path.

**Features**:
- `--dry-run` flag to preview what would be deleted
- Shows count and sample of events to be deleted
- Comprehensive logging
- Executable: `python scripts/cleanup_null_crops.py [--dry-run]`

## Expected Outcomes

1. **No more null crop_path insertions**: Worker skips events without valid crops
2. **Correct frame extraction**: Frame numbers map correctly from remote inference to local frame files
3. **Better observability**: Logs show:
   - `events_created`: Count of successfully saved events
   - `detections_total`: Total detections from inference
   - `skipped_no_crop`: Count of skipped events
   - Reason for each skip (invalid type, shape, size, solid color, upload failure)
4. **API stability**: Events API handles null crop_path gracefully
5. **Clean database**: Cleanup script removes existing corrupt rows

## Testing Recommendations

1. Run cleanup script to remove existing null crop_path rows:
   ```bash
   python scripts/cleanup_null_crops.py --dry-run  # Preview
   python scripts/cleanup_null_crops.py             # Execute
   ```

2. Test remote inference pipeline with video upload:
   - Verify frame_no in logs shows correct global indices
   - Check that crops are generated successfully
   - Verify no events created with null crop_path

3. Monitor worker logs for summary:
   ```
   Upload processed - Summary | events_created=X detections_total=Y skipped_no_crop=Z
   ```

4. Verify UI displays events correctly without errors

## Files Modified

- `src/detectors/remote_inference.py` - Fixed frame number mapping
- `src/worker.py` - Added crop validation and skip logic
- `src/api/events.py` - Added null crop_path filter
- `src/schemas/event.py` - Made crop_path optional
- `scripts/cleanup_null_crops.py` - Created cleanup utility (NEW)

## Backward Compatibility

- EventResponse schema now allows null crop_path for backward compatibility
- Events API filters out null crop_path to prevent UI breaks
- No database migration needed (crop_path column remains nullable=False in schema, but worker prevents null inserts)
- Cleanup script is optional but recommended

## Next Steps

1. Deploy changes
2. Run cleanup script to remove corrupt rows
3. Monitor worker logs for skip counts
4. Verify remote inference produces valid crops
5. Consider adding crop validation metrics/alerts
