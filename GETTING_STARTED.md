# Getting Started with ANPR City API

**Quick start guide to get the ANPR City API running in under 10 minutes.**

## Prerequisites

- Docker & Docker Compose (for quickest setup)
- OR Python 3.11+ (for local development)
- 8GB+ RAM recommended
- 20GB+ disk space

## Option 1: Quick Start with Docker (Self-Hosted)

**Fastest way to get started - everything in Docker**

```bash
# 1. Clone and enter directory
cd anpr-city-api

# 2. Run bootstrap script
chmod +x scripts/bootstrap.sh
./scripts/bootstrap.sh

# This will:
#   - Create .env with secure JWT_SECRET
#   - Start PostgreSQL, Redis, MinIO
#   - Run database migrations

# 3. Start API and Worker
docker-compose up -d api worker

# 4. Verify it's running
curl http://localhost:8000/health
# Should return: {"status":"ok"}

# 5. Open API documentation
open http://localhost:8000/docs
```

**Default Credentials:**
- Email: `admin@example.com`
- Password: `changeme123`

**Services Running:**
- API: http://localhost:8000
- MinIO Console: http://localhost:9001
- PgAdmin: http://localhost:5050

## Option 2: Supabase Mode

**Use Supabase for managed database & storage**

```bash
# 1. Create Supabase account & project
# Go to https://supabase.com

# 2. Follow setup guide
# See SUPABASE_SETUP.md for detailed steps

# 3. Update .env with Supabase credentials
cp .env.example .env
# Edit MODE=supabase and add SUPABASE_* values

# 4. Start services
docker-compose -f docker-compose.supabase.yml up -d
```

See [SUPABASE_SETUP.md](SUPABASE_SETUP.md) for complete guide.

## Option 3: Local Development (No Docker)

**For Python developers who prefer local setup**

```bash
# 1. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start services (Postgres & Redis)
# Option A: Use Docker for services only
docker-compose up -d postgres redis minio

# Option B: Install locally
# brew install postgresql redis  # macOS
# sudo apt install postgresql redis  # Ubuntu

# 4. Create .env
cp .env.example .env
# Generate JWT_SECRET: openssl rand -base64 32
# Update DATABASE_URL, REDIS_URL

# 5. Run migrations
alembic upgrade head
# OR run SQL directly:
psql $DATABASE_URL -f migrations/001_initial_schema.sql

# 6. Start API (terminal 1)
python -m uvicorn src.main:app --reload

# 7. Start Worker (terminal 2)
python -m src.worker
```

## Verify Installation

Run the test script:

```bash
chmod +x scripts/test-api.sh
./scripts/test-api.sh
```

This will test:
- Health check
- Authentication
- User management
- Camera creation
- Events API
- BOLO management
- Metrics

## First Steps

### 1. Login and Get Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme123"}'
```

Save the `access_token` from response.

### 2. Create a Camera

```bash
curl -X POST http://localhost:8000/api/cameras \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main Street Camera",
    "description": "North-facing camera at Main St",
    "lat": 40.7128,
    "lon": -74.0060,
    "heading": 90.0,
    "active": true
  }'
```

### 3. Upload a Test Video

```bash
curl -X POST http://localhost:8000/api/uploads \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_video.mp4" \
  -F "camera_id=CAMERA_ID_FROM_STEP_2"
```

### 4. Check Processing Status

```bash
curl http://localhost:8000/api/jobs/JOB_ID_FROM_STEP_3 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. View Detected Events

```bash
curl http://localhost:8000/api/events?limit=10 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Interactive API Documentation

Open http://localhost:8000/docs in your browser for:
- Interactive API explorer
- Try out endpoints
- See request/response schemas
- Copy curl commands

## Next Steps

### Integrate Real Detector

The detector is currently a stub. To integrate YOLO + EasyOCR:

1. Edit `src/detectors/yolo_easyocr_adapter.py`
2. Replace the `detect_plates()` function
3. Install additional dependencies:
   ```bash
   pip install ultralytics easyocr
   ```
4. Download models:
   ```bash
   # YOLO model for plate detection
   wget https://github.com/your-model.pt

   # EasyOCR will download on first use
   ```
5. Test with sample video:
   ```bash
   python -c "
   from src.detectors.yolo_easyocr_adapter import detect_plates
   import cv2
   frame = cv2.imread('test_plate.jpg')
   results = detect_plates(frame)
   print(results)
   "
   ```

See comments in the file for example implementation.

### Configure BOLO Alerts

Create a BOLO alert for a plate pattern:

```bash
curl -X POST http://localhost:8000/api/bolos \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plate_pattern": "ABC.*",
    "description": "Stolen vehicle",
    "active": true,
    "notification_webhook": "https://your-webhook.com/alert"
  }'
```

When a matching plate is detected, the webhook will be called.

### Set Up Monitoring

1. **Prometheus + Grafana**:
   ```bash
   # Metrics available at /metrics
   curl http://localhost:8000/metrics

   # Import Grafana dashboard (create one or find community dashboard)
   ```

2. **Log Aggregation**:
   - Logs are JSON structured
   - Pipe to ELK stack, Loki, or CloudWatch Logs
   - Example with filebeat/fluentd

3. **Alerting**:
   - Set up alerts in Prometheus/Grafana
   - PagerDuty integration
   - Slack notifications

## Troubleshooting

### API won't start

```bash
# Check logs
docker-compose logs api

# Common issues:
# - DATABASE_URL incorrect
# - JWT_SECRET not set
# - Ports already in use (8000)
```

### Worker not processing jobs

```bash
# Check worker logs
docker-compose logs worker

# Check Redis connection
docker-compose exec worker redis-cli -h redis ping

# Check queue length
docker-compose exec api python -c "
from src.services.queue import queue_service
import asyncio
asyncio.run(queue_service.connect())
print(asyncio.run(queue_service.get_queue_length('video_processing')))
"
```

### Database connection errors

```bash
# Check Postgres is running
docker-compose ps postgres

# Test connection
docker-compose exec api psql $DATABASE_URL -c "SELECT 1;"

# Check credentials in .env
```

### Upload fails

```bash
# Check storage is running
docker-compose ps minio  # self-hosted
# OR check Supabase dashboard for storage

# Check buckets exist
# MinIO: http://localhost:9001
# Supabase: Storage tab in dashboard

# Check file size limits (default: 100MB)
```

## Development Workflow

### Making Changes

```bash
# 1. Create feature branch
git checkout -b feature/new-endpoint

# 2. Make changes to code

# 3. Run tests
make test

# 4. Format code
make format

# 5. Lint
make lint

# 6. Commit
git add .
git commit -m "Add new endpoint"

# 7. Push and create PR
git push origin feature/new-endpoint
```

### Adding a Database Migration

```bash
# 1. Modify models in src/models/

# 2. Create migration
make migrate-create
# OR: alembic revision --autogenerate -m "description"

# 3. Review generated migration in alembic/versions/

# 4. Apply migration
make migrate
# OR: alembic upgrade head

# 5. Test rollback
alembic downgrade -1
alembic upgrade head
```

### Running Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Specific test file
pytest tests/test_auth.py -v

# Specific test
pytest tests/test_auth.py::test_login_success -v
```

## Common Commands

```bash
# Start all services
make dev

# Stop all services
docker-compose down

# View logs
docker-compose logs -f api
docker-compose logs -f worker

# Restart a service
docker-compose restart api

# Run migrations
make migrate

# Clean up
make clean

# Rebuild containers
docker-compose build --no-cache

# Shell into container
docker-compose exec api bash
docker-compose exec worker bash
```

## Useful Resources

- **API Docs**: http://localhost:8000/docs
- **Metrics**: http://localhost:8000/metrics
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **PgAdmin**: http://localhost:5050

## Documentation Index

- [README.md](README.md) - Overview and architecture
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Project status and features
- [DEVELOPER_HANDOFF.md](DEVELOPER_HANDOFF.md) - Technical deep dive
- [API_QUICK_REFERENCE.md](API_QUICK_REFERENCE.md) - API examples
- [SUPABASE_SETUP.md](SUPABASE_SETUP.md) - Supabase configuration
- [OPERATIONAL_CONSIDERATIONS.md](OPERATIONAL_CONSIDERATIONS.md) - Production ops
- [DEVELOPMENT_CHECKLIST.md](DEVELOPMENT_CHECKLIST.md) - Roadmap and TODOs

## Getting Help

1. Check documentation above
2. Search existing GitHub issues
3. Check logs: `docker-compose logs`
4. Ask in team chat
5. Create GitHub issue with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Logs and error messages
   - Environment (OS, Docker version, etc.)

## What's Next?

After setup:

1. ✅ Integrate real detector (Priority 1)
2. ✅ Upload test videos
3. ✅ Test review workflow
4. ✅ Configure BOLO alerts
5. ✅ Set up monitoring
6. ✅ Deploy to staging
7. ✅ Load testing
8. ✅ Production deployment

See [DEVELOPMENT_CHECKLIST.md](DEVELOPMENT_CHECKLIST.md) for complete roadmap.

---

**You're ready to start developing! 🚀**

Questions? See [DEVELOPER_HANDOFF.md](DEVELOPER_HANDOFF.md) or contact the team.
