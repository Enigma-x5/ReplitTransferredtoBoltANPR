# Developer Handoff Guide

## Project Overview

This is a production-ready FastAPI backend for ANPR (Automatic Number Plate Recognition) with human-in-the-loop corrections, BOLO alerts, and licensing/metering.

**Tech Stack**:
- Python 3.11+
- FastAPI (async)
- SQLAlchemy 2.x (async ORM)
- PostgreSQL 15+ (via Supabase or self-hosted)
- Redis (queue)
- MinIO/Supabase Storage (object storage)
- Docker + Docker Compose
- GitHub Actions (CI/CD)

## Project Structure

```
anpr-city-api/
├── src/
│   ├── api/              # API route handlers
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── users.py      # User management
│   │   ├── cameras.py    # Camera CRUD
│   │   ├── uploads.py    # Video upload handling
│   │   ├── jobs.py       # Job status queries
│   │   ├── events.py     # Detection event search
│   │   ├── feedback.py   # Review and correction workflow
│   │   ├── bolos.py      # BOLO alert management
│   │   ├── licenses.py   # License activation
│   │   └── admin.py      # Admin/health endpoints
│   ├── models/           # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── camera.py
│   │   ├── upload.py
│   │   ├── event.py
│   │   ├── bolo.py
│   │   ├── license.py
│   │   ├── export.py
│   │   └── audit.py
│   ├── schemas/          # Pydantic request/response schemas
│   ├── services/         # Business logic services
│   │   ├── storage.py    # S3/Supabase storage abstraction
│   │   ├── queue.py      # Redis queue service
│   │   └── detector_adapter.py  # Video processing orchestrator
│   ├── detectors/        # Detection algorithms
│   │   └── yolo_easyocr_adapter.py  # STUB - Replace with real detector
│   ├── auth.py           # JWT authentication logic
│   ├── config.py         # Settings management
│   ├── database.py       # Database connection
│   ├── logging_config.py # Structured logging
│   ├── main.py           # FastAPI app entrypoint
│   └── worker.py         # Background job processor
├── migrations/           # SQL migration scripts
│   └── 001_initial_schema.sql
├── alembic/              # Alembic migration tool config
├── tests/                # Pytest tests
├── docker-compose.yml    # Self-hosted mode
├── docker-compose.supabase.yml  # Supabase mode
├── Dockerfile
├── .github/workflows/ci.yml  # CI pipeline
├── requirements.txt
├── .env.example
└── README.md
```

## Key Design Decisions

### 1. Dual Mode Architecture

The system supports two deployment modes:

- **Supabase Mode**: Uses Supabase Auth, Storage, and Postgres
- **Self-hosted Mode**: Uses PostgreSQL + MinIO + local auth

Switch via `MODE` environment variable. This allows customers to choose between managed services and full control.

### 2. Async Everything

All I/O operations are async:
- Database queries use SQLAlchemy async
- HTTP clients use httpx
- Queue operations use aioredis

This enables high concurrency with low resource usage.

### 3. Pluggable Detector

The detector is abstracted behind `DetectorAdapter` and `yolo_easyocr_adapter.py`. This allows:
- Easy swapping of detection algorithms
- Testing without real ML models
- Customer-specific model integration

**TODO**: Replace the stub with actual YOLO + EasyOCR code.

### 4. Queue-Based Processing

Video processing is decoupled from API:
1. Client uploads video → API stores in S3/Supabase → enqueues job to Redis
2. Worker pulls job → downloads video → runs detector → saves events
3. Client polls `/jobs/{job_id}` for status

This enables:
- Scalable worker pool
- Fault tolerance
- Progress tracking

### 5. Human-in-the-Loop Corrections

Events start as `unreviewed`. Users can:
- Confirm (mark as correct)
- Correct (provide correct plate text)
- Reject

Corrections are stored separately and flagged for export to retraining datasets.

## Critical Code Sections

### Authentication Flow

```python
# src/api/auth.py
# Login endpoint validates credentials and issues JWT
# JWT contains user_id and role for RBAC

# src/auth.py
# get_current_user() dependency extracts user from JWT
# get_current_admin() checks role = admin
```

### Upload → Detection Pipeline

```python
# 1. src/api/uploads.py
#    - Client uploads video multipart file
#    - Save to storage
#    - Create Upload record
#    - Enqueue job to Redis

# 2. src/worker.py
#    - Worker polls Redis queue
#    - Downloads video
#    - Calls detector_adapter.process_video()
#    - For each detection:
#        - Save crop to storage
#        - Create Event record
#        - Check BOLO matches
#    - Update Upload status
```

### BOLO Matching

```python
# src/worker.py:check_bolos()
# For each new event:
#   - Query active BOLOs
#   - Regex match against plate_pattern
#   - If match, create BOLOMatch record
#   - Send webhook/email notification
```

### Storage Abstraction

```python
# src/services/storage.py
# StorageService interface with two implementations:
#   - SupabaseStorageService
#   - MinioStorageService
# Both support: upload_file, get_presigned_url, delete_file
```

## Environment Variables

See `.env.example` for all variables. Critical ones:

- `MODE`: `supabase` or `selfhost`
- `DATABASE_URL`: Async Postgres connection string
- `JWT_SECRET`: MUST be secure random string (32+ chars)
- `REDIS_URL`: Redis connection string
- `SUPABASE_*`: Only if MODE=supabase
- `MINIO_*`: Only if MODE=selfhost

## Database Schema

All tables defined in `src/models/`. Key tables:

- `users`: Authentication and RBAC
- `cameras`: Camera registry with geolocation
- `uploads`: Video upload job tracking
- `events`: Detection results (plate, confidence, bbox, crop)
- `corrections`: Human corrections to detections
- `bolos`: Alert patterns
- `bolo_matches`: When an event matches a BOLO
- `licenses`: License key management
- `usage_reports`: Metering data
- `exports`: Export job tracking
- `audit_logs`: Activity audit trail

## Running the System

### Self-Hosted (Docker Compose)

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head

# View logs
docker-compose logs -f api
docker-compose logs -f worker
```

### Supabase Mode

```bash
# 1. Create Supabase project at https://supabase.com
# 2. Run migrations/001_initial_schema.sql in Supabase SQL editor
# 3. Configure .env with Supabase credentials
# 4. Start services
docker-compose -f docker-compose.supabase.yml up -d
```

### Local Development

```bash
# Install deps
pip install -r requirements.txt

# Start Postgres and Redis (or use Docker)
docker-compose up -d postgres redis

# Run API
python -m uvicorn src.main:app --reload

# Run worker (separate terminal)
python -m src.worker
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_auth.py::test_login_success -v
```

Tests use a separate test database and clean up after each test.

## Common Development Tasks

### Adding a New API Endpoint

1. Define Pydantic schema in `src/schemas/`
2. Create route handler in `src/api/`
3. Add route to `src/main.py` router
4. Write test in `tests/`
5. Update OpenAPI docs (automatic via FastAPI)

### Adding a New Database Table

1. Create model in `src/models/`
2. Import in `src/models/__init__.py`
3. Create Alembic migration: `alembic revision -m "description"`
4. Write migration SQL
5. Test migration: `alembic upgrade head`

### Integrating Real Detector

Edit `src/detectors/yolo_easyocr_adapter.py`:

```python
from ultralytics import YOLO
import easyocr

# Load models (do this once, not per frame)
yolo_model = YOLO('models/plate_detector.pt')
ocr_reader = easyocr.Reader(['en'])

def detect_plates(frame):
    results = yolo_model(frame)
    detections = []
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
            crop = frame[y1:y2, x1:x2]
            ocr_results = ocr_reader.readtext(crop)
            if ocr_results:
                plate_text = ocr_results[0][1]
                confidence = ocr_results[0][2]
                detections.append({
                    'plate': plate_text,
                    'confidence': confidence,
                    'bbox': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}
                })
    return detections
```

## Deployment

### Docker Image Build

```bash
docker build -t anpr-city-api:latest .
docker tag anpr-city-api:latest your-registry/anpr-city-api:latest
docker push your-registry/anpr-city-api:latest
```

### Kubernetes

See `k8s/` directory for manifests (TODO: create these).

Key resources needed:
- Deployment (API + Worker)
- Service (API)
- ConfigMap (non-secret config)
- Secret (JWT_SECRET, DATABASE_URL, etc.)
- HPA (autoscaling)
- Ingress (HTTPS termination)

### Monitoring

- Prometheus metrics at `/metrics`
- Health check at `/health` and `/api/admin/health`
- Structured logs to stdout (JSON format)

Use Grafana to visualize Prometheus metrics. Example queries:

```promql
# Events per second
rate(anpr_events_processed_total[5m])

# Queue backlog
anpr_queue_size

# Job success rate
rate(anpr_jobs_processed_total[5m]) / (rate(anpr_jobs_processed_total[5m]) + rate(anpr_jobs_failed_total[5m]))
```

## Known Limitations & TODOs

1. **Export Worker Not Implemented**: `/feedback/export` creates a record but no worker actually generates the ZIP. Need to implement `export_worker.py`.

2. **No Plate Deduplication**: If same plate appears in consecutive frames, multiple events are created. Need deduplication logic.

3. **No Live Stream Support**: Only uploaded videos are processed. Adding RTSP stream support requires integrating with cv2.VideoCapture or GStreamer.

4. **Stub Detector**: Must replace `yolo_easyocr_adapter.py` with real implementation.

5. **No Rate Limiting**: API has no rate limiting. Add with `slowapi` or nginx.

6. **Limited Error Handling**: Some edge cases (e.g., storage failures) may not be handled gracefully.

## Troubleshooting

### Workers not processing jobs

- Check Redis connectivity: `redis-cli -h localhost ping`
- Check queue has jobs: `redis-cli llen video_processing`
- Check worker logs: `docker-compose logs -f worker`

### API returns 500 errors

- Check database connectivity
- Check environment variables are set
- Check logs for stack traces

### Upload fails

- Check storage service is running (MinIO or Supabase)
- Check credentials in .env
- Check bucket exists

### Low detection accuracy

- Verify detector model is trained on similar data
- Tune `DETECTION_CONFIDENCE_THRESHOLD`
- Check frame quality (resolution, lighting)

## Next Steps

See `DEVELOPMENT_CHECKLIST.md` for prioritized list of enhancements.

**Immediate priorities**:
1. Integrate real YOLO + EasyOCR detector
2. Implement export worker
3. Add comprehensive integration tests
4. Tune performance (caching, indexes)

## Contact

For questions:
- Tech Lead: [email]
- Documentation: /docs endpoint
- Code issues: GitHub Issues

---

**Good luck! The foundation is solid. Focus on the detector integration and you'll have a working system quickly.**
