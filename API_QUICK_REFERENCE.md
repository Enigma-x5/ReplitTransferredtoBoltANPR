# API Quick Reference

Base URL: `http://localhost:8000/api`

## Authentication

All endpoints (except `/auth/login` and `/licenses/*`) require JWT authentication.

Include token in header:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "changeme123"
}

# Response
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 604800
}
```

## User Management (Admin Only)

### Create User
```bash
POST /api/users
Authorization: Bearer TOKEN

{
  "email": "user@example.com",
  "username": "john",
  "password": "secure_password",
  "role": "clerk"  # or "admin"
}
```

### List Users
```bash
GET /api/users
Authorization: Bearer TOKEN
```

## Camera Management

### Create Camera (Admin Only)
```bash
POST /api/cameras
Authorization: Bearer TOKEN

{
  "name": "Main Street Camera",
  "description": "North-facing at Main St intersection",
  "lat": 40.7128,
  "lon": -74.0060,
  "heading": 90.0,
  "rtsp_url": "rtsp://camera.local/stream",
  "active": true
}
```

### List Cameras
```bash
GET /api/cameras
Authorization: Bearer TOKEN
```

### Get Camera
```bash
GET /api/cameras/{camera_id}
Authorization: Bearer TOKEN
```

### Update Camera (Admin Only)
```bash
PATCH /api/cameras/{camera_id}
Authorization: Bearer TOKEN

{
  "name": "Updated Name",
  "active": false
}
```

## Video Upload & Processing

### Upload Video
```bash
POST /api/uploads
Authorization: Bearer TOKEN
Content-Type: multipart/form-data

# Using curl
curl -X POST http://localhost:8000/api/uploads \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@video.mp4" \
  -F "camera_id=uuid-here"

# Response
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### Check Job Status
```bash
GET /api/jobs/{job_id}
Authorization: Bearer TOKEN

# Response
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",  # or "done", "failed"
  "created_at": "2024-01-01T12:00:00Z"
}
```

## Event Search & Management

### Search Events
```bash
GET /api/events?plate=ABC123&limit=50
GET /api/events?camera_id={uuid}&from_ts=2024-01-01T00:00:00Z
GET /api/events?normalized=true&plate=ABC
Authorization: Bearer TOKEN

# Response
{
  "total": 150,
  "items": [
    {
      "id": "uuid",
      "plate": "ABC-123",
      "normalized_plate": "ABC123",
      "confidence": 0.95,
      "camera_id": "uuid",
      "bbox": {"x1": 100, "y1": 200, "x2": 300, "y2": 250},
      "captured_at": "2024-01-01T12:00:00Z",
      "frame_no": 42,
      "crop_path": "crops/uuid/image.jpg",
      "review_state": "unreviewed",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

### Get Event Details
```bash
GET /api/events/{event_id}
Authorization: Bearer TOKEN
```

### Confirm Event
```bash
POST /api/events/{event_id}/confirm
Authorization: Bearer TOKEN

{
  "notes": "Verified - plate is correct"
}

# Response: Updated event with review_state="confirmed"
```

### Submit Correction
```bash
POST /api/events/{event_id}/correction
Authorization: Bearer TOKEN

{
  "corrected_plate": "ABC-124",
  "comments": "OCR misread 3 as 4"
}

# Response
{
  "id": "correction-uuid",
  "event_id": "event-uuid",
  "original_plate": "ABC-123",
  "corrected_plate": "ABC-124",
  "corrected_by": "user-uuid",
  "confidence_before": 0.95,
  "comments": "OCR misread 3 as 4",
  "created_at": "2024-01-01T12:00:00Z"
}
```

## Feedback & Review Workflow

### Get Pending Reviews
```bash
GET /api/feedback/pending?limit=50
Authorization: Bearer TOKEN

# Returns EventListResponse with unreviewed events
```

### Request Export
```bash
POST /api/feedback/export
Authorization: Bearer TOKEN

{
  "from_ts": "2024-01-01T00:00:00Z",
  "to_ts": "2024-01-31T23:59:59Z",
  "min_confidence": 0.8
}

# Response
{
  "export_id": "uuid"
}

# Note: Export is async. Check export status in exports table
```

## BOLO (Be On the Lookout) Alerts

### Create BOLO
```bash
POST /api/bolos
Authorization: Bearer TOKEN

{
  "plate_pattern": "ABC.*",  # Regex pattern
  "description": "Stolen vehicle - report immediately",
  "active": true,
  "priority": 1,
  "notification_webhook": "https://webhook.site/your-webhook",
  "notification_email": "alerts@police.gov",
  "expires_at": "2024-12-31T23:59:59Z"
}
```

### List BOLOs
```bash
GET /api/bolos
Authorization: Bearer TOKEN
```

## Licensing & Metering

### Activate License
```bash
POST /api/licenses/activate

{
  "license_key": "ANPR-XXXX-XXXX-XXXX-XXXX",
  "node_id": "customer-node-001"
}

# Response
{
  "activated": true,
  "expires_at": "2025-01-01T00:00:00Z",
  "features": {
    "max_cameras": 10,
    "advanced_analytics": true
  }
}
```

### Report Usage
```bash
POST /api/licenses/usage

{
  "node_id": "customer-node-001",
  "camera_count": 5,
  "timestamp": "2024-01-01T12:00:00Z"
}

# Response
{
  "status": "acknowledged"
}
```

## Admin & Monitoring

### Health Check
```bash
GET /api/admin/health
Authorization: Bearer TOKEN (admin)

# Response
{
  "status": "ok",
  "database": "healthy",
  "queue": {
    "status": "healthy",
    "pending_jobs": 3
  }
}
```

### Prometheus Metrics
```bash
GET /metrics

# No authentication required
# Returns Prometheus-format metrics
```

## Common Workflows

### Complete Upload → Review → Correction Flow

```bash
# 1. Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme123"}' \
  | jq -r '.access_token')

# 2. Create camera
CAMERA_ID=$(curl -X POST http://localhost:8000/api/cameras \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Cam","lat":40.7,"lon":-74.0}' \
  | jq -r '.id')

# 3. Upload video
JOB_ID=$(curl -X POST http://localhost:8000/api/uploads \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.mp4" \
  -F "camera_id=$CAMERA_ID" \
  | jq -r '.job_id')

# 4. Wait for processing (poll job status)
watch -n 2 "curl -s http://localhost:8000/api/jobs/$JOB_ID \
  -H 'Authorization: Bearer $TOKEN' | jq '.status'"

# 5. Get pending reviews
curl http://localhost:8000/api/feedback/pending \
  -H "Authorization: Bearer $TOKEN" | jq

# 6. Correct an event
EVENT_ID="uuid-from-step-5"
curl -X POST http://localhost:8000/api/events/$EVENT_ID/correction \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"corrected_plate":"CORRECT-PLATE","comments":"Fixed OCR error"}'

# 7. Export corrections
curl -X POST http://localhost:8000/api/feedback/export \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"min_confidence":0.8}' | jq
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad request (validation error)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not found
- `500` - Internal server error

## Rate Limits

Currently no rate limits implemented. Consider adding for production:
- Login: 5 requests/minute per IP
- Upload: 10 requests/minute per user
- Events search: 100 requests/minute per user

## Pagination

Search endpoints support pagination:
- `limit` query param (default: 50, max: 1000)
- Returns `total` count in response

Future enhancement: Add `offset` or cursor-based pagination.

## Authentication Token

JWT tokens contain:
```json
{
  "sub": "user-uuid",
  "role": "admin",
  "exp": 1234567890
}
```

Default expiration: 7 days (configurable via `JWT_EXPIRATION_MINUTES`)

To refresh token: Re-login (refresh tokens not yet implemented)

## API Versioning

Current version: `0.2.0`

All endpoints under `/api` prefix. Future versions will use `/api/v2`, etc.

## OpenAPI Documentation

Interactive docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
