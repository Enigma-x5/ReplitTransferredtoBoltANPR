# Command Centre Storage Contract

## Overview

This folder defines the **storage and object-naming contract** for Command Centre learning images.

**CRITICAL: THIS IS A CONTRACT ONLY, NOT AN IMPLEMENTATION**

No storage operations, uploads, or cloud connections are implemented. This document defines HOW storage WOULD work when implemented in the future.

## Purpose

Define a clear contract for:
1. Where learning images are stored centrally
2. How objects are named and organized
3. What metadata is required
4. Upload batch semantics
5. Object lifecycle policies

## Storage Architecture

### Central Object Storage

Learning images are stored in **central object storage** (e.g., Cloudflare R2, AWS S3, GCS).

**Key Principles:**
- **Centralized**: One storage bucket for all cities
- **Flat Namespace**: No city-based folder hierarchy
- **Metadata-Driven**: City identity stored as object metadata, NOT in paths
- **Immutable**: Objects never overwritten once uploaded
- **Batch Uploads**: Daily batch uploads from cities to Command Centre

### Separation from City Storage

```
City Client:
  - Operational images stored locally (ephemeral, high volume)
  - Curated samples selected for learning
  - Daily batch upload to Command Centre

Command Centre:
  - Learning images stored centrally (persistent, lower volume)
  - Linked to learning_samples and hitl_labels tables
  - Used for training and model evaluation
```

**City databases remain isolated** - no operational data flows to Command Centre.

## Upload Process

### Daily Batch Uploads

1. **Selection**: City selects samples to contribute to learning (based on criteria)
2. **HITL Filtering**: Exclude samples with `label_status = 'unsure'`
3. **Batch Creation**: Group selected samples into daily batch
4. **Upload**: Send batch to Command Centre storage
5. **Registration**: Register samples in `learning_samples` table with object references

### What Gets Uploaded

**Included:**
- Samples with `label_status = 'correct'` (confirmed detections)
- Samples with `label_status = 'changed'` (corrections for training)
- High-quality images suitable for training

**Excluded:**
- Samples with `label_status = 'unsure'` (ambiguous, not useful for training)
- Low-quality images (below quality threshold)
- Operational/PII data

### Upload Frequency

- **Recommended**: Daily batches during off-peak hours
- **Minimum**: Weekly batches
- **Maximum**: Real-time uploads (not recommended due to overhead)

## Data Retention and Eligibility Policy

### Upload Eligibility Rules

**CRITICAL: Only specific HITL statuses are eligible for upload to Command Centre.**

**Eligible for Upload:**
- Events with `label_status = 'correct'` (confirmed detections)
- Events with `label_status = 'changed'` (corrected detections)

**NOT Eligible for Upload:**
- Events with `label_status = 'unsure'` (ambiguous, operator uncertain)
- Events with `label_status = 'pending'` (awaiting HITL review)
- Events without any HITL status

**Rationale:**
- **Correct samples**: Confirm the model is working properly, useful for validation
- **Changed samples**: Provide corrections for model improvement, most valuable for training
- **Unsure samples**: Ambiguous data degrades training quality, excluded by design
- **Pending samples**: Incomplete workflow, not yet ready for learning purposes

### Image Retention Policy

**All images are ephemeral and automatically deleted according to policy.**

#### City/Client-Side Retention

Images stored locally at cities are subject to automatic deletion:

**Images WITHOUT completed HITL (pending or no HITL):**
- **Maximum retention**: 6 months
- **Purpose**: Allow time for HITL review and processing
- **After expiration**: Automatically deleted, no upload to Command Centre

**Images WITH completed HITL (correct, changed, or unsure):**
- **Maximum retention**: 1 month
- **Purpose**: Allow time for upload to Command Centre (if eligible)
- **After expiration**: Automatically deleted from city storage

#### Command Centre Retention

Images uploaded to Command Centre are also ephemeral:

**Learning images in Command Centre storage:**
- **Retention period**: Configurable, typically 1-2 years
- **Purpose**: Training and model evaluation only
- **After expiration**: Automatically deleted from object storage
- **Database metadata**: Retained for audit trail (without image reference)

### Data Lifecycle Summary

```
Event Captured
    ↓
[0-6 months] Awaiting HITL review (if no HITL performed)
    ↓
HITL Review Completed
    ↓
[0-1 month] City retention after HITL
    ↓
Eligibility Check:
    - correct/changed → Upload to Command Centre
    - unsure/pending → Discard, do NOT upload
    ↓
[City] Automatic deletion after 1 month
    ↓
[Command Centre] Store for 1-2 years (training/evaluation)
    ↓
[Command Centre] Automatic deletion after retention period
    ↓
Database metadata retained (no image reference)
```

### Ephemeral Data Principles

**All image data is temporary and used only for learning purposes:**

- **No permanent archival**: Images are not kept indefinitely
- **Learning-focused**: Images serve training and evaluation, then deleted
- **Metadata survives**: Database records remain for audit trail
- **Privacy by design**: Automatic deletion reduces privacy risk
- **Storage costs controlled**: Ephemeral storage limits growth

### Policy Enforcement

**Upload eligibility is enforced at the city/client level:**

- **City responsibility**: Cities filter events by HITL status before upload
- **Pre-upload validation**: Only eligible events are selected for batch uploads
- **Command Centre does NOT override**: Command Centre accepts uploads from cities based on trust
- **Audit trail**: All uploads logged with original HITL status in metadata

**Why city-level enforcement?**
- Cities have the authoritative HITL status information
- Reduces unnecessary data transfer (don't upload to check eligibility)
- Maintains data sovereignty (cities control what they share)
- Simplifies Command Centre logic (trust uploaded data meets criteria)

### Retention Policy Benefits

**Automatic deletion provides multiple benefits:**

- **Privacy compliance**: Reduced data retention supports GDPR and similar regulations
- **Storage cost control**: Automatic cleanup prevents unbounded growth
- **Data quality**: Fresh data more relevant for training
- **Security**: Less data exposure over time
- **Operational simplicity**: Automatic policies, no manual cleanup required

### Edge Cases and Exceptions

**HITL status changes after upload:**
- If a city operator changes HITL status after upload (e.g., 'correct' → 'unsure'), the image remains in Command Centre until retention policy expires
- No retroactive deletion from Command Centre based on status changes
- New status does not trigger re-upload or update

**Manual deletion requests:**
- Cities or operators may request early deletion (e.g., for privacy/GDPR reasons)
- Deletion requests processed via metadata queries (see "Object Lifecycle" section)
- Deletion typically completed within 7 days of request

**Retention period adjustments:**
- Retention periods are configurable per deployment
- Changes apply to new uploads, not retroactively
- Longer retention may be needed for specialized training scenarios

## Storage Backend Options

The contract is backend-agnostic. Recommended options:

### Cloudflare R2 (Recommended)
- Cost-effective (no egress fees)
- S3-compatible API
- Global edge network
- Good for frequent training pipeline access

### AWS S3
- Industry standard
- Rich ecosystem
- Mature tooling
- Higher egress costs

### Google Cloud Storage (GCS)
- Good integration with ML tools
- Multi-region options
- Competitive pricing

### Other S3-Compatible Storage
- MinIO (self-hosted)
- Backblaze B2
- DigitalOcean Spaces

## Object References

Objects are referenced in the `learning_samples` table via the `image_reference` field.

**Format Examples:**
```
r2://learning-images/01234567-89ab-cdef-0123-456789abcdef.jpg
s3://learning-images/01234567-89ab-cdef-0123-456789abcdef.jpg
https://learning-images.example.com/01234567-89ab-cdef-0123-456789abcdef.jpg
```

The reference format depends on the storage backend chosen.

## Metadata Storage

City identity and sample context are stored as **object metadata**, not in paths.

Required metadata fields (see `object_naming.md` for details):
- `city_id`
- `camera_id`
- `event_id`
- `label_status`
- `uploaded_at`

This enables:
- Querying objects by city without path manipulation
- Filtering objects by label status
- Tracking upload provenance
- Policy-driven lifecycle management

## Object Lifecycle

### Immutability

- Objects are **immutable** once uploaded
- Never overwrite existing objects
- Use unique object names (UUIDs recommended)
- Corrections/updates create new objects

### Deletion Policy

- **Metadata-Driven**: Deletion based on metadata, not paths
- **Retention**: Define retention periods (e.g., 2 years)
- **Archival**: Move old objects to cold storage
- **GDPR/Privacy**: Support deletion requests via metadata queries

Example policies:
- Archive objects older than 1 year
- Delete `label_status=unsure` objects after 30 days (if accidentally uploaded)
- Keep `label_status=changed` objects indefinitely (valuable corrections)

## Security and Access Control

### Authentication

- API keys or IAM roles for authenticated access
- No public access to learning images
- Separate credentials for:
  - City clients (upload-only)
  - Command Centre (read/write)
  - Training pipeline (read-only)

### Privacy

- No PII in object names or paths
- City identity in metadata only
- Images should not contain identifiable information beyond plates
- Comply with data protection regulations

## Cost Considerations

### Storage Costs

- **Hot Storage**: Frequently accessed (recent samples)
- **Cold Storage**: Infrequently accessed (old samples, archives)
- **Compression**: Use JPEG compression to reduce size

### Transfer Costs

- **Batch Uploads**: More efficient than real-time
- **Egress Fees**: Consider providers with free egress (e.g., Cloudflare R2)
- **Training Access**: Minimize downloads via caching

## Integration with Learning Store

### Database Schema Integration

```
learning_samples.image_reference -> Object Storage URL
  ↓
Object Storage (Cloudflare R2, S3, etc.)
  ↓
Object with metadata:
  - city_id
  - camera_id
  - event_id
  - label_status
  - uploaded_at
```

### Query Pattern

1. Query `learning_samples` table for samples meeting criteria
2. Get `image_reference` URLs
3. Fetch objects from storage using URLs
4. Use metadata for filtering/verification

## Implementation Status

**NOT IMPLEMENTED**

This is a contract definition. Actual implementation requires:
1. Choose storage backend (e.g., Cloudflare R2)
2. Create storage bucket
3. Configure credentials and access policies
4. Implement upload client in city code
5. Implement receiver in Command Centre
6. Update `learning_samples` table with object references

## Related Documentation

- `object_naming.md`: Detailed object naming and metadata specification
- `../learning_store/README.md`: Database schema for learning store
- `../learning_store/learning_samples.sql`: Table definition for sample metadata

## Notes

- This contract is designed to be cloud-agnostic
- Implementation can adapt to specific cloud provider features
- Metadata schema should align with `learning_samples` table fields
- Object naming should support future scaling (millions of images)

## Future Considerations

- **Deduplication**: Detect and handle duplicate images
- **Versioning**: Object versioning for accidental overwrites
- **CDN**: Content delivery network for faster training access
- **Replication**: Multi-region replication for disaster recovery
- **Encryption**: At-rest and in-transit encryption
