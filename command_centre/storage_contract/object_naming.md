# Object Naming and Metadata Specification

## Overview

This document defines the **object naming convention and metadata schema** for Command Centre learning images.

**CRITICAL: THIS IS A SPECIFICATION, NOT AN IMPLEMENTATION**

No storage operations occur. This document defines the contract for future implementation.

## Design Principles

### Flat Namespace

**Use a flat object namespace with NO folder hierarchy.**

❌ **BAD** (City-based folders):
```
/city_mumbai/cam_001/2025/01/15/image_001.jpg
/city_delhi/cam_042/2025/01/15/image_002.jpg
```

✅ **GOOD** (Flat namespace):
```
01234567-89ab-cdef-0123-456789abcdef.jpg
11111111-2222-3333-4444-555555555555.jpg
```

**Why flat namespace?**
- Scalability: No folder limits
- Simplicity: Easier to manage and query
- Performance: Faster object operations
- Cloud-Native: Aligns with object storage best practices
- Privacy: City identity not exposed in paths

### City Identity in Metadata

**Store city identity as object metadata, NOT in paths.**

```
Object Name: 01234567-89ab-cdef-0123-456789abcdef.jpg
Metadata:
  city_id: city_mumbai
  camera_id: cam_001
  event_id: evt_20250115_120000_001
  label_status: changed
  uploaded_at: 2025-01-15T12:00:00Z
```

**Benefits:**
- Query by city using metadata filters
- Decouple storage from city structure
- Support city renaming without moving objects
- Enable multi-city aggregation queries

## Object Naming Pattern

### Recommended: UUID v4

**Format:** `{uuid}.{extension}`

**Examples:**
```
01234567-89ab-cdef-0123-456789abcdef.jpg
abcdef01-2345-6789-abcd-ef0123456789.jpg
f47ac10b-58cc-4372-a567-0e02b2c3d479.jpg
```

**Benefits:**
- Globally unique (no collisions)
- No information leakage
- URL-safe
- Sortable by time if using UUID v7 (optional)
- No folder structure needed

### Alternative: Timestamp + Random

**Format:** `{timestamp}_{random}.{extension}`

**Examples:**
```
20250115_120000_a1b2c3d4.jpg
20250115_120001_e5f6g7h8.jpg
```

**Benefits:**
- Chronologically sortable
- Human-readable timestamp
- Still collision-resistant

**Drawbacks:**
- Slightly longer
- Less standard than UUID

### Recommendation

**Use UUID v4** for simplicity and standards compliance.

## Object Extensions

Use standard image extensions based on format:

- `.jpg` or `.jpeg` - JPEG images (recommended for photos)
- `.png` - PNG images (if lossless required)
- `.webp` - WebP images (modern, efficient)

**Recommended:** `.jpg` for plate images (good compression, widely supported)

## Metadata Schema

### Required Metadata Fields

All objects MUST have these metadata fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `city_id` | string | City identifier | `city_mumbai` |
| `camera_id` | string | Camera identifier | `cam_001` |
| `event_id` | string | Original event ID from city | `evt_20250115_120000_001` |
| `label_status` | string | HITL label status | `correct`, `changed`, `unsure` |
| `uploaded_at` | ISO 8601 | Upload timestamp | `2025-01-15T12:00:00Z` |

### Optional Metadata Fields

Additional fields for enhanced functionality:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `detected_plate` | string | Detected plate text | `MH12AB1234` |
| `corrected_plate` | string | Corrected plate (if changed) | `MH12AB1234` |
| `confidence` | float | Detection confidence | `0.95` |
| `sample_id` | string | Learning sample ID | `sample_cityA_20250115_001` |
| `detection_timestamp` | ISO 8601 | When detected at city | `2025-01-15T08:30:00Z` |
| `image_quality_score` | float | Quality score | `0.87` |
| `sample_type` | string | Sample type | `automatic`, `manual` |
| `upload_batch_id` | string | Batch identifier | `batch_20250115` |

### Metadata Format

**Cloud Provider Metadata:**

Different storage backends have different metadata formats:

**AWS S3:**
```json
{
  "x-amz-meta-city-id": "city_mumbai",
  "x-amz-meta-camera-id": "cam_001",
  "x-amz-meta-event-id": "evt_20250115_120000_001",
  "x-amz-meta-label-status": "changed",
  "x-amz-meta-uploaded-at": "2025-01-15T12:00:00Z"
}
```

**Cloudflare R2 (S3-compatible):**
```json
{
  "city-id": "city_mumbai",
  "camera-id": "cam_001",
  "event-id": "evt_20250115_120000_001",
  "label-status": "changed",
  "uploaded-at": "2025-01-15T12:00:00Z"
}
```

**Google Cloud Storage:**
```json
{
  "city_id": "city_mumbai",
  "camera_id": "cam_001",
  "event_id": "evt_20250115_120000_001",
  "label_status": "changed",
  "uploaded_at": "2025-01-15T12:00:00Z"
}
```

### Metadata Validation

**Required field validation:**
- `city_id`: Non-empty string, format: `city_{name}`
- `camera_id`: Non-empty string
- `event_id`: Non-empty string
- `label_status`: Must be one of: `correct`, `changed`, `unsure`
- `uploaded_at`: Valid ISO 8601 timestamp

**Optional field validation:**
- `confidence`: Float between 0.0 and 1.0
- `image_quality_score`: Float between 0.0 and 1.0

## Object Immutability

### No Overwrites

**Objects are NEVER overwritten once uploaded.**

- Each upload gets a unique object name (UUID)
- If image needs to be "updated", upload as new object
- Old object remains until lifecycle policy deletes it
- Corrections create new objects with updated metadata

### Why Immutability?

- **Data Integrity**: No accidental overwrites
- **Audit Trail**: Complete history of uploads
- **Concurrent Safety**: No race conditions
- **Versioning**: Implicit versioning via new objects
- **Rollback**: Can revert to previous objects if needed

## Deletion Policy

### Metadata-Driven Deletion

**Deletion is based on metadata queries, NOT paths.**

❌ **BAD** (Path-based deletion):
```
Delete all objects in /city_mumbai/
```

✅ **GOOD** (Metadata-based deletion):
```
Delete all objects where metadata.city_id = 'city_mumbai'
```

### Deletion Use Cases

**1. Retention Policy**
- Delete objects older than retention period
- Query: `uploaded_at < (now - retention_period)`

**2. Quality Filtering**
- Delete low-quality samples
- Query: `image_quality_score < threshold`

**3. Label Status Filtering**
- Delete unsure samples (if accidentally uploaded)
- Query: `label_status = 'unsure'`

**4. Privacy/GDPR Requests**
- Delete objects from specific city or time period
- Query: `city_id = 'city_X' AND detection_timestamp BETWEEN start AND end`

### Soft Deletion (Recommended)

Instead of immediate deletion, use lifecycle policies:

1. **Mark for deletion**: Add metadata flag `marked_for_deletion: true`
2. **Grace period**: Keep object for 30 days
3. **Automatic deletion**: Lifecycle policy deletes after grace period
4. **Audit log**: Log all deletions

## Query Patterns

### Query by City

```
Filter objects where metadata.city_id = 'city_mumbai'
```

Returns all objects from Mumbai, regardless of object name.

### Query by Label Status

```
Filter objects where metadata.label_status = 'changed'
```

Returns all corrected samples (valuable for training).

### Query by Date Range

```
Filter objects where metadata.uploaded_at BETWEEN '2025-01-01' AND '2025-01-31'
```

Returns all objects uploaded in January 2025.

### Query by Multiple Criteria

```
Filter objects where:
  metadata.city_id = 'city_mumbai'
  AND metadata.label_status IN ('correct', 'changed')
  AND metadata.uploaded_at >= '2025-01-01'
  AND metadata.confidence >= 0.8
```

Returns high-quality, labeled samples from Mumbai since Jan 2025.

## Upload Batch Semantics

### Daily Batch Structure

**Batch Identifier:** `batch_{city_id}_{date}`

Example: `batch_city_mumbai_20250115`

**Batch Metadata:**
- All objects in a batch share `upload_batch_id` metadata
- Enables tracking which objects were uploaded together
- Simplifies retry logic (re-upload entire batch if needed)

### Batch Upload Process

1. **Prepare Batch**
   - Select samples for upload (exclude `label_status=unsure`)
   - Generate UUID for each object
   - Prepare metadata for each object

2. **Upload Objects**
   - Upload objects with unique UUIDs
   - Set required metadata on each object
   - Set `upload_batch_id` for tracking

3. **Register in Database**
   - Insert records into `learning_samples` table
   - Set `image_reference` to object URL
   - Link to `hitl_labels` if labels exist

4. **Verify Upload**
   - Query storage for `upload_batch_id`
   - Verify count matches expected
   - Mark batch as complete in city database

### Idempotency

**Batch uploads should be idempotent:**

- If batch upload fails partially, can retry
- Already-uploaded objects are not re-uploaded
- Use `event_id` to detect duplicates
- Check if object with same `event_id` metadata exists before upload

## Example Object Specifications

### Example 1: Correct Detection

```
Object Name:
  f47ac10b-58cc-4372-a567-0e02b2c3d479.jpg

Metadata:
  city_id: city_mumbai
  camera_id: cam_highway_01
  event_id: evt_20250115_083000_001
  label_status: correct
  detected_plate: MH12AB1234
  confidence: 0.95
  sample_id: sample_mumbai_20250115_001
  detection_timestamp: 2025-01-15T08:30:00Z
  uploaded_at: 2025-01-15T12:00:00Z
  image_quality_score: 0.92
  sample_type: automatic
  upload_batch_id: batch_city_mumbai_20250115
```

### Example 2: Corrected Detection

```
Object Name:
  a1b2c3d4-e5f6-4789-abcd-ef0123456789.jpg

Metadata:
  city_id: city_delhi
  camera_id: cam_downtown_05
  event_id: evt_20250115_143000_042
  label_status: changed
  detected_plate: DL3CAB1Z34
  corrected_plate: DL3CAB1234
  confidence: 0.87
  sample_id: sample_delhi_20250115_042
  detection_timestamp: 2025-01-15T14:30:00Z
  uploaded_at: 2025-01-15T20:00:00Z
  image_quality_score: 0.88
  sample_type: manual
  upload_batch_id: batch_city_delhi_20250115
```

### Example 3: Excluded (Unsure)

**This sample would NOT be uploaded** (label_status = 'unsure')

```
City Event:
  event_id: evt_20250115_090000_007
  detected_plate: MH12??????
  label_status: unsure

Action: DO NOT UPLOAD
Reason: Unsure samples excluded from learning store
```

## Scalability Considerations

### Object Count Projections

**Assumptions:**
- 10 cities
- 100 cameras per city
- 100 detections per camera per day
- 5% contribution rate to learning store

**Daily uploads:**
- 10 cities × 100 cameras × 100 detections × 5% = 5,000 objects/day

**Annual uploads:**
- 5,000 objects/day × 365 days = 1,825,000 objects/year

**5-year total:**
- 1,825,000 × 5 = 9,125,000 objects (9M+ objects)

### Scaling Strategy

**Flat namespace handles millions of objects:**
- Modern object storage scales to billions of objects
- No folder limits (some systems limit files per folder)
- List operations paginated
- Metadata queries efficient

**If scaling beyond 100M objects:**
- Consider sharding by year: `2025/01234567-89ab-cdef-0123-456789abcdef.jpg`
- Still metadata-driven, year prefix just for organizational efficiency
- Not recommended initially

## Storage Size Estimates

**Assumptions:**
- Average image size: 200 KB (JPEG compressed)
- 5,000 objects/day

**Daily storage:**
- 5,000 × 200 KB = 1 GB/day

**Annual storage:**
- 1 GB/day × 365 = 365 GB/year

**5-year storage:**
- 365 GB × 5 = 1.825 TB

**Cost estimates (Cloudflare R2):**
- Storage: $0.015/GB/month
- Monthly cost: 1,825 GB × $0.015 = $27.38/month
- Annual cost: $328.56/year

**Very affordable for long-term ML dataset storage.**

## Implementation Checklist

When implementing this contract:

- [ ] Choose storage backend (Cloudflare R2, S3, GCS)
- [ ] Create storage bucket with appropriate permissions
- [ ] Configure IAM roles and access policies
- [ ] Implement UUID generation for object names
- [ ] Implement metadata setting on upload
- [ ] Implement city-side batch upload logic
- [ ] Implement Command Centre receiver for uploads
- [ ] Update `learning_samples.image_reference` with object URLs
- [ ] Implement metadata query functionality
- [ ] Configure lifecycle policies for retention
- [ ] Test upload/query/delete operations
- [ ] Document actual storage backend configuration
- [ ] Monitor storage costs and usage

## Related Documentation

- `README.md`: Storage architecture overview
- `../learning_store/README.md`: Database schema
- `../learning_store/learning_samples.sql`: Table for object references

## Notes

- This specification is cloud-agnostic
- Actual implementation may adapt to specific provider features
- Metadata field names may vary by provider (use provider's conventions)
- Always validate metadata on upload
- Log all storage operations for audit trail

## Future Enhancements

- **Content-based deduplication**: Hash images to detect duplicates
- **Thumbnail generation**: Store small previews alongside full images
- **Multi-region replication**: Replicate to multiple regions for performance
- **Object versioning**: Enable versioning as backup against accidental deletion
- **Presigned URLs**: Generate time-limited URLs for secure access
- **CDN integration**: Cache frequently accessed objects at edge
