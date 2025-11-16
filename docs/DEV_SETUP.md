# Developer Setup Guide

This guide provides clear, step-by-step instructions for setting up the ANPR City API development environment.

## Prerequisites

- **Docker & Docker Compose** (recommended for quickest setup)
- **Python 3.11+** (for local development without Docker)
- **Node.js 18+** (for frontend development)
- **8GB+ RAM** recommended
- **20GB+ disk space**

## Quick Start Options

Choose the setup that best fits your development environment:

1. **Docker Development** (Recommended) - Full stack in containers
2. **Local Development** (No Docker) - Run services locally
3. **Replit Development** - Cloud-based development

---

## Option 1: Docker Development (Recommended)

### Step 1: Clone and Setup Environment

```bash
# Navigate to project directory
cd anpr-city-api

# Run bootstrap script
chmod +x scripts/bootstrap.sh
./scripts/bootstrap.sh
```

The bootstrap script will:
- Create `.env` from `.env.template` if it doesn't exist
- Generate a secure `JWT_SECRET`
- Start Postgres, Redis, and MinIO
- Run database migrations
- Create admin user

### Step 2: Start API and Worker

```bash
# Start API server and worker
docker-compose up -d api worker

# View logs
docker-compose logs -f api
```

### Step 3: Start Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at http://localhost:5000 with API proxy to http://localhost:8000

### Step 4: Verify Setup

```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme123"}'
```

### Services Overview

| Service | Port | URL | Credentials |
|---------|------|-----|-------------|
| API | 8000 | http://localhost:8000/docs | admin@example.com / changeme123 |
| Frontend | 5000 | http://localhost:5000 | Same as API |
| MinIO Console | 9001 | http://localhost:9001 | minioadmin / minioadmin |
| PgAdmin | 5050 | http://localhost:5050 | admin@example.com / admin |
| Postgres | 5432 | localhost:5432 | postgres / postgres |
| Redis | 6379 | localhost:6379 | (no password) |

---

## Option 2: Local Development (No Docker)

### Step 1: Install Dependencies

#### Install Python Dependencies

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

#### Install System Services

**macOS (Homebrew):**
```bash
brew install postgresql@15 redis
brew services start postgresql@15
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql-15 redis-server
sudo systemctl start postgresql
sudo systemctl start redis-server
```

### Step 2: Configure Environment

```bash
# Create .env from template
cp .env.template .env

# Generate JWT_SECRET
JWT_SECRET=$(openssl rand -base64 32)

# Update .env file
# Set DATABASE_URL to your local Postgres
# Set REDIS_URL to your local Redis
```

Example `.env` for local development:
```bash
MODE=selfhost
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/anpr_city
JWT_SECRET=<your-generated-secret>
REDIS_URL=redis://localhost:6379/0
DETECTOR_BACKEND=mock
```

### Step 3: Setup Database

```bash
# Create database
createdb anpr_city

# Run migrations
psql postgresql://postgres:postgres@localhost:5432/anpr_city -f migrations/001_initial_schema.sql

# Create admin user
python create_admin.py
```

### Step 4: Start Services

**Terminal 1 - API Server:**
```bash
source venv/bin/activate
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Worker:**
```bash
source venv/bin/activate
python -m src.worker
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Option 3: Replit Development

Replit is pre-configured with the necessary environment. The `.replit` file handles the setup.

### How Replit Works

1. **Environment Variables**: Set in Replit Secrets
2. **Backend**: Runs on port 8000 (configured in `.replit`)
3. **Frontend**: Vite dev server on port 5000 with proxy
4. **Database**: Use Docker Postgres or connect to external DB

### Replit Setup Steps

1. Open project in Replit
2. Add secrets in Replit Secrets panel:
   - `DATABASE_URL`
   - `JWT_SECRET`
   - `REDIS_URL`
   - Other required env vars from `.env.template`
3. Click "Run" - Replit will start both backend and frontend
4. Access via Replit's webview URL

See `replit.md` and `REPLIT_MODIFICATIONS.md` for detailed Replit configuration.

---

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MODE` | Deployment mode | `selfhost` or `supabase` |
| `DATABASE_URL` | Async Postgres connection | `postgresql+asyncpg://user:pass@host:5432/db` |
| `JWT_SECRET` | Secret for JWT tokens | Generate with `openssl rand -base64 32` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DETECTOR_BACKEND` | Detector mode | `mock` (or `yolo` for production) |
| `WORKER_CONCURRENCY` | Worker threads | `2` |
| `DETECTION_CONFIDENCE_THRESHOLD` | Min confidence | `0.7` |
| `FRAME_EXTRACTION_FPS` | Frames per second | `2` |
| `LOG_LEVEL` | Logging level | `INFO` |

---

## Detector Backends

### Mock Detector (Development)

For lightweight development without YOLO/EasyOCR:

```bash
DETECTOR_BACKEND=mock
```

The mock detector:
- Processes videos without heavy ML dependencies
- Generates fake plate detections for testing
- Suitable for Replit and resource-constrained environments
- Fast and lightweight

### YOLO Detector (Production)

For real plate detection:

```bash
DETECTOR_BACKEND=yolo
YOLO_MODEL=keremberke/yolov8n-license-plate
```

Requirements:
- GPU recommended (CUDA support)
- Additional dependencies: `ultralytics`, `easyocr`, `torch`
- More processing time and resources

---

## Running the Worker

### Docker:
```bash
docker-compose up -d worker
docker-compose logs -f worker
```

### Local:
```bash
source venv/bin/activate
python -m src.worker
```

### Worker Environment Variables

Configure worker behavior:
```bash
DETECTOR_BACKEND=mock          # or 'yolo'
WORKER_CONCURRENCY=2           # Number of concurrent jobs
FRAME_SKIP=10                  # Process every Nth frame
DETECTION_CONFIDENCE_THRESHOLD=0.7
```

---

## Common Development Tasks

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_auth.py -v
```

### Format Code

```bash
black src/ tests/
ruff check src/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### View Logs

**Docker:**
```bash
docker-compose logs -f api
docker-compose logs -f worker
```

**Local:**
Logs output to console (structured JSON format)

---

## Troubleshooting

### Issue: Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000
# OR
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>
```

### Issue: Database Connection Failed

```bash
# Check Postgres is running
docker-compose ps postgres
# OR
pg_isready -h localhost -p 5432

# Test connection
psql postgresql://postgres:postgres@localhost:5432/anpr_city -c "SELECT 1;"
```

### Issue: Worker Not Processing Jobs

```bash
# Check Redis connection
redis-cli ping

# Check queue length
docker-compose exec api python -c "
from src.services.queue import queue_service
import asyncio
asyncio.run(queue_service.connect())
print(asyncio.run(queue_service.get_queue_length('video_processing')))
"

# Restart worker
docker-compose restart worker
```

### Issue: Frontend Can't Connect to API

Check `frontend/vite.config.ts` proxy configuration:
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

### Issue: Missing Dependencies

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

---

## Development Workflow

### Making Changes to Backend

1. Edit code in `src/`
2. API auto-reloads (uvicorn `--reload` flag)
3. Run tests: `pytest`
4. Format: `black src/`

### Making Changes to Frontend

1. Edit code in `frontend/src/`
2. Vite hot-reloads automatically
3. Build: `cd frontend && npm run build`

### Adding New API Endpoints

1. Create/edit route file in `src/api/`
2. Add schemas in `src/schemas/`
3. Update models if needed in `src/models/`
4. Add tests in `tests/`
5. Update `docs/openapi.yaml` if needed

---

## Next Steps

After successful setup:

1. **Test the API**: Use http://localhost:8000/docs
2. **Upload a video**: POST to `/api/uploads`
3. **Check detection results**: GET `/api/events`
4. **Review the frontend**: http://localhost:5000
5. **Configure BOLO alerts**: POST to `/api/bolos`

See also:
- [README.md](../README.md) - Project overview
- [GETTING_STARTED.md](../GETTING_STARTED.md) - Quick start guide
- [API_QUICK_REFERENCE.md](API_QUICK_REFERENCE.md) - API examples
- [REPLIT_MODIFICATIONS.md](../REPLIT_MODIFICATIONS.md) - Replit-specific notes

---

## Support

- Check existing documentation in `/docs`
- Review logs: `docker-compose logs`
- GitHub issues for bugs
- Team chat for questions
