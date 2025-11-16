# ANPR City API

Production-ready FastAPI backend for Automatic Number Plate Recognition (ANPR) with human-in-the-loop corrections, BOLO alerts, and licensing/metering capabilities.

## Features

- **Video Upload & Processing**: Async video ingestion with frame extraction and detection
- **License Plate Detection**: Pluggable detector adapter (YOLO + EasyOCR ready)
- **Human-in-the-Loop**: Review and correction workflow for detected plates
- **BOLO Alerts**: Pattern matching with webhook/email notifications
- **Camera Management**: Geospatial camera registry with RTSP support
- **Licensing & Metering**: On-premise license activation and usage reporting
- **Data Export**: Labeled dataset export for model retraining
- **Authentication**: JWT-based auth with role-based access control (admin/clerk)
- **Monitoring**: Prometheus metrics and structured logging
- **Dual Mode**: Supabase or self-hosted (Postgres + MinIO)

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Client    │────────▶│   FastAPI    │────────▶│  Postgres   │
│  (Frontend) │         │   API Server │         │  Database   │
└─────────────┘         └──────────────┘         └─────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │    Redis     │
                        │    Queue     │
                        └──────────────┘
                              │
                              ▼
                        ┌──────────────┐         ┌─────────────┐
                        │   Worker(s)  │────────▶│   Storage   │
                        │  (Detector)  │         │ (S3/MinIO)  │
                        └──────────────┘         └─────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for local dev)
- PostgreSQL 15+ (if not using Docker)
- Redis 7+ (if not using Docker)

### Option 1: Self-Hosted Mode (Docker Compose)

```bash
# Clone repository
git clone <repo-url>
cd anpr-city-api

# Copy environment file
cp .env.example .env

# Edit .env and set:
#   MODE=selfhost
#   JWT_SECRET=<generate-secure-random-string>

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head

# API available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Option 2: Supabase Mode

1. **Create Supabase Project**:
   - Go to https://supabase.com
   - Create a new project
   - Note your project URL and keys

2. **Configure Storage**:
   ```sql
   -- In Supabase SQL Editor, create buckets:
   INSERT INTO storage.buckets (id, name, public) VALUES ('anpr-uploads', 'anpr-uploads', false);
   INSERT INTO storage.buckets (id, name, public) VALUES ('anpr-crops', 'anpr-crops', false);
   ```

3. **Run Database Migration**:
   ```bash
   # Copy SQL from migrations/001_initial_schema.sql
   # Paste and run in Supabase SQL Editor
   ```

4. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env:
   MODE=supabase
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   SUPABASE_SERVICE_KEY=your-service-role-key
   DATABASE_URL=postgresql+asyncpg://postgres:[password]@db.your-project.supabase.co:5432/postgres
   JWT_SECRET=<generate-secure-random-string>
   ```

5. **Start Services**:
   ```bash
   docker-compose -f docker-compose.supabase.yml up -d
   ```

### Option 3: Local Development (No Docker)

```bash
# Install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up database
createdb anpr_city
alembic upgrade head

# Start Redis (or use cloud Redis)
redis-server

# Run API server
python -m uvicorn src.main:app --reload

# Run worker (in separate terminal)
python -m src.worker
```

## Configuration

All configuration via environment variables (see `.env.example`):

| Variable | Description | Required |
|----------|-------------|----------|
| `MODE` | `supabase` or `selfhost` | Yes |
| `DATABASE_URL` | Async PostgreSQL connection string | Yes |
| `JWT_SECRET` | Secret key for JWT (min 32 chars) | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `SUPABASE_URL` | Supabase project URL | If MODE=supabase |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | If MODE=supabase |
| `MINIO_ENDPOINT` | MinIO endpoint | If MODE=selfhost |

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login and receive JWT

### Users (Admin only)
- `POST /api/users` - Create user
- `GET /api/users` - List users

### Cameras
- `POST /api/cameras` - Create camera (admin)
- `GET /api/cameras` - List cameras
- `GET /api/cameras/{id}` - Get camera
- `PATCH /api/cameras/{id}` - Update camera (admin)

### Uploads & Jobs
- `POST /api/uploads` - Upload video for processing
- `GET /api/jobs/{job_id}` - Get job status

### Events
- `GET /api/events` - Search events (by plate, camera, time)
- `GET /api/events/{id}` - Get event details
- `POST /api/events/{id}/confirm` - Confirm detection
- `POST /api/events/{id}/correction` - Submit correction

### Feedback & Export
- `GET /api/feedback/pending` - List unreviewed events
- `POST /api/feedback/export` - Request labeled data export

### BOLOs
- `POST /api/bolos` - Create BOLO alert
- `GET /api/bolos` - List BOLOs

### Licensing
- `POST /api/licenses/activate` - Activate license key
- `POST /api/licenses/usage` - Report usage metrics

### Admin
- `GET /api/admin/health` - System health check

Full API documentation: http://localhost:8000/docs

## Detector Integration

Replace the stub in `src/detectors/yolo_easyocr_adapter.py`:

```python
from ultralytics import YOLO
import easyocr

model = YOLO('path/to/plate_detector.pt')
reader = easyocr.Reader(['en'])

def detect_plates(frame):
    results = model(frame)
    detections = []
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
            crop = frame[y1:y2, x1:x2]
            ocr = reader.readtext(crop)
            if ocr:
                detections.append({
                    'plate': ocr[0][1],
                    'confidence': ocr[0][2],
                    'bbox': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}
                })
    return detections
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

## Deployment

### Kubernetes (Production)

```bash
# Create secrets
kubectl create secret generic anpr-secrets \
  --from-literal=jwt-secret=$(openssl rand -base64 32) \
  --from-literal=database-url=postgresql+asyncpg://... \
  --from-literal=redis-url=redis://...

# Deploy
kubectl apply -f k8s/

# See k8s/ directory for manifests
```

### Security Best Practices

1. **Secrets Management**:
   - Use Kubernetes secrets or AWS Secrets Manager
   - Never commit `.env` files
   - Rotate JWT secrets periodically

2. **HTTPS**:
   ```bash
   # Local dev with mkcert
   mkcert -install
   mkcert localhost 127.0.0.1
   # Use certs with uvicorn --ssl-keyfile --ssl-certfile
   ```

3. **Database**:
   - Use strong passwords
   - Enable SSL connections
   - Regular backups

## Monitoring

### Prometheus Metrics

Available at `/metrics`:

- `anpr_events_processed_total` - Total events processed
- `anpr_events_failed_total` - Failed events
- `anpr_jobs_processed_total` - Completed jobs
- `anpr_queue_size` - Current queue size

### Logging

Structured JSON logs (configurable):

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "info",
  "event": "User logged in",
  "user_id": "uuid",
  "email": "user@example.com"
}
```

## Migration: Supabase → Self-Hosted

```bash
# 1. Dump Supabase database
pg_dump -h db.your-project.supabase.co -U postgres -d postgres > backup.sql

# 2. Restore to self-hosted Postgres
psql -h localhost -U postgres -d anpr_city < backup.sql

# 3. Migrate storage (use rclone or custom script)
# 4. Update .env to MODE=selfhost
# 5. Restart services
```

## Operational Estimates

### GPU Requirements

- **Light load** (1-5 cameras): 1x T4 GPU
- **Medium load** (5-20 cameras): 2x T4 or 1x A10G
- **Heavy load** (20+ cameras): 2+ A10G or V100

Processing speed: ~30 FPS per GPU for detection + OCR

### Storage Estimates

- **Raw video**: ~1GB/hour per camera (h264 compressed)
- **Crops**: ~100KB per detection
- **Retention**: Plan for 30-90 days retention
- Example: 10 cameras × 24h × 30 days = 7.2TB

### Costs (AWS Example)

- EC2 (API): t3.medium = $30/mo
- EC2 (Worker + GPU): g4dn.xlarge = $400/mo
- RDS Postgres: db.t3.medium = $60/mo
- ElastiCache Redis: cache.t3.micro = $15/mo
- S3 Storage: 10TB = $230/mo

**Total**: ~$735/month for 10-camera deployment

## Troubleshooting

### Issue: Worker not processing jobs

```bash
# Check Redis connectivity
docker-compose exec worker redis-cli -h redis ping

# Check queue length
docker-compose exec api python -c "
from src.services.queue import queue_service
import asyncio
asyncio.run(queue_service.connect())
print(asyncio.run(queue_service.get_queue_length('video_processing')))
"

# Check worker logs
docker-compose logs -f worker
```

### Issue: Cannot upload files

- Check storage bucket exists (Supabase) or MinIO is running
- Verify credentials in .env
- Check file size limits (default: 100MB, configurable in nginx/proxy)

### Issue: Low detection accuracy

- Verify detector model is trained for your region's plates
- Adjust `DETECTION_CONFIDENCE_THRESHOLD` in .env
- Review frame extraction FPS (`FRAME_EXTRACTION_FPS`)

## Contributing

See `DEVELOPMENT_CHECKLIST.md` for next steps and contribution guidelines.

## License

Proprietary - All rights reserved

## Support

- Documentation: /docs
- Issues: GitHub Issues
- Email: support@yourdomain.com
