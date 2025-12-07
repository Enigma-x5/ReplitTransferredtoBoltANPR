# ANPR City - Replit Project Documentation

## Overview
This project is a production-ready **Automatic Number Plate Recognition (ANPR)** system with a React frontend and FastAPI backend. It features human-in-the-loop corrections, BOLO (Be On the Lookout) alerts, camera management, and video processing capabilities.

## Current Setup (Selfhost Mode)

### Architecture
```
Frontend (React + Vite) → Backend API (FastAPI) → PostgreSQL Database
        Port 5000              Port 8000              Replit Managed
                                    ↓
                               Redis Queue → Worker Process
                               Port 6379     (Background)
                                    ↓
                            MinIO Storage (S3-compatible)
```

### Running Services
1. **Frontend** - React application on port 5000 (user-facing)
2. **Backend** - FastAPI server on port 8000
3. **Redis** - Local queue server on port 6379
4. **PostgreSQL** - Replit managed database
5. **Worker** - Background job processor (planned)

### Admin Access
- **Email**: admin@admin.com
- **Username**: admin
- **Password**: Admin@123

### Environment Configuration
- **Mode**: `selfhost` (using local/Replit resources)
- **Database**: Supabase PostgreSQL (shared with Bolt for synchronized development)
- **Redis**: Local Redis server
- **Storage**: MinIO for file uploads
- **CORS**: Allows all origins (development mode)
- **Frontend API**: Configured via Vite proxy in `vite.config.ts` - forwards `/api` requests to backend on port 8000

## Project Structure

```
/
├── frontend/              # React + TypeScript + Vite frontend
│   ├── src/
│   │   ├── api/          # API client
│   │   ├── auth/         # Authentication context
│   │   ├── components/   # UI components (shadcn/ui)
│   │   ├── pages/        # Application pages
│   │   └── main.tsx      # Entry point
│   ├── package.json
│   └── vite.config.ts
│
├── src/                  # Python backend
│   ├── api/             # API route handlers
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── detectors/       # ANPR detection adapters
│   ├── main.py          # FastAPI app
│   ├── worker.py        # Background job processor
│   ├── config.py        # Configuration
│   └── database.py      # Database setup
│
├── migrations/          # SQL migrations
├── docs/               # Documentation
│   └── READY_SWITCH.md # Production transition guide
│
├── requirements.txt    # Python dependencies
└── README.md          # Project documentation
```

## Key Features

### Implemented
- ✅ User authentication (JWT-based)
- ✅ Camera management
- ✅ Video upload and processing queue
- ✅ License plate event tracking
- ✅ BOLO alert system
- ✅ Human-in-the-loop corrections
- ✅ Data export for model training
- ✅ Audit logging
- ✅ Licensing/metering system

### Pending Integration
- ⏳ YOLO + EasyOCR detector (stub ready)
- ⏳ Worker process (code ready, needs workflow)
- ⏳ MinIO server setup
- ⏳ Webhook/email notifications

## Development Workflow

### Making Changes

**Backend Changes**:
1. Edit files in `src/`
2. Backend auto-reloads (uvicorn --reload)
3. Check console logs for errors

**Frontend Changes**:
1. Edit files in `frontend/src/`
2. Vite HMR updates instantly
3. View changes in the webview

**Database Changes**:
1. Modify models in `src/models/`
2. Create new migration SQL file
3. Run: `psql $DATABASE_URL -f migrations/new_migration.sql`

### Testing the Application

**Access the Frontend**:
- Click the "Webview" tab in Replit
- Or use the preview pane on the right

**Test the API**:
- Backend API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

**Login**:
1. Navigate to `/login` in the frontend
2. Use admin credentials (see above)
3. Access dashboard and features

## Workflows

### Frontend (Port 5000)
- **Command**: `cd frontend && npm run dev`
- **Status**: Running
- **Purpose**: Serves the React application
- **Output**: Webview (user-facing)

### Backend (Port 8000)
- **Command**: `python -m uvicorn src.main:app --host 0.0.0.0 --port 8000`
- **Status**: Running
- **Purpose**: FastAPI server with all endpoints
- **Output**: Console logs

### Redis Server (Port 6379)
- **Command**: `redis-server --bind 127.0.0.1 --port 6379`
- **Status**: Running
- **Purpose**: Job queue for video processing
- **Output**: Console logs

## Database Schema

Key tables:
- `users` - Authentication and authorization
- `cameras` - Camera registry with geospatial data
- `uploads` - Video upload tracking
- `events` - License plate detections
- `corrections` - Human corrections
- `bolos` - BOLO alert patterns
- `bolo_matches` - Matched alerts
- `licenses` - License key management
- `audit_logs` - Activity tracking

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login

### Users
- `POST /api/users` - Create user (admin only)
- `GET /api/users` - List users

### Cameras
- `GET /api/cameras` - List cameras
- `POST /api/cameras` - Create camera (admin)
- `GET /api/cameras/{id}` - Get camera details
- `PATCH /api/cameras/{id}` - Update camera

### Uploads & Jobs
- `POST /api/uploads` - Upload video for processing
- `GET /api/jobs/{job_id}` - Get job status

### Events
- `GET /api/events` - Search events
- `GET /api/events/{id}` - Event details
- `POST /api/events/{id}/confirm` - Confirm detection
- `POST /api/events/{id}/correction` - Submit correction

### BOLOs
- `GET /api/bolos` - List BOLOs
- `POST /api/bolos` - Create BOLO alert

Full API documentation: `http://localhost:8000/docs`

## User Preferences

### Coding Standards
- Follow existing patterns in the codebase
- Backend: FastAPI with async/await
- Frontend: React with TypeScript
- Use structured logging (structlog)
- Database: SQLAlchemy with async

### Development Approach
- Use Replit-managed services when possible
- Keep workflows minimal (currently 3)
- Test incrementally
- Document major changes

## Next Steps

### To Complete Project
1. **Set up MinIO server** for file storage (workflow or Docker)
2. **Configure worker process** as a separate workflow
3. **Integrate ANPR detector** (YOLO + EasyOCR)
4. **Test video upload and processing** end-to-end
5. **Set up production mode** (see `docs/READY_SWITCH.md`)

### To Deploy to Production
See `docs/READY_SWITCH.md` for detailed instructions on:
- Switching to Supabase for database and storage
- Using external Redis (Upstash)
- Configuring production domains
- Security hardening
- Performance tuning

## Troubleshooting

### Backend not starting
- Check `DATABASE_URL` is set
- Verify all dependencies installed: `pip list`
- Review backend workflow logs

### Frontend not loading
- Check frontend workflow is running
- Verify port 5000 is accessible
- Check browser console for errors

### Database connection issues
- Verify `DATABASE_URL` in Replit Secrets
- Check PostgreSQL is running: `psql $DATABASE_URL -c "SELECT 1"`
- Review migration status

### Redis connection errors
- Ensure Redis workflow is running
- Test connection: `redis-cli ping`
- Check `REDIS_URL` matches actual Redis server

## Resources

- **Original Backend**: Generated by Bolt.new
- **Frontend**: Generated by Lovable
- **Documentation**: See `README.md`, `GETTING_STARTED.md`, `DEVELOPER_HANDOFF.md`
- **API Reference**: `API_QUICK_REFERENCE.md`
- **Transition Guide**: `docs/READY_SWITCH.md`

## Recent Changes

**December 7, 2025 (Latest)**
- ✅ **FIXED: Events page crash** - Changed camera filter dropdown to use "all" as value instead of empty string (Radix UI requirement), with proper conversion for API requests
- ✅ **FIXED: review_state enum mismatch** - Added `values_callable` to SQLEnum configuration so SQLAlchemy sends lowercase values ("unreviewed") matching the Postgres enum instead of uppercase ("UNREVIEWED")
- ✅ **Ola Maps Integration** - Added interactive map to the dashboard displaying camera locations:
  - Backend endpoint `/api/maps/config` provides API key securely to authenticated users only
  - OlaMap React component dynamically loads Ola Maps Web SDK from CDN
  - Camera locations displayed as colored markers (green = active, red = inactive)
  - Markers have popups showing camera name and status
  - Map auto-fits bounds when multiple cameras are present
  - Improved error handling with timeout fallback for map loading

**December 6, 2025**
- ✅ **FIXED: Network Error on login** - Changed frontend `.env` to use `VITE_API_BASE_URL=/api` instead of `http://localhost:8000`. The old value caused the browser to try to connect to the user's local machine instead of going through the Vite proxy to reach the Replit backend.
- ✅ **Updated demo credentials** - Login page now shows correct credentials: `admin@admin.com / Admin@123`

**December 3, 2025**
- ✅ **FIXED: Frontend login issue** - AuthContext now decodes JWT token to get role from backend instead of hardcoding based on email. This allows any admin user to login (not just admin@example.com)
- ✅ **FIXED: Token validation** - Frontend now validates JWT expiration on mount and clears auth state if token is expired/invalid
- ✅ **FIXED: Error display** - Login page now shows actual backend error messages instead of generic fallback
- ✅ **FIXED: Database schema** - Ran migrations to create all 11 tables in Supabase
- ✅ **FIXED: Admin credentials** - Created admin user with email `admin@admin.com`, password `Admin@123`
- ✅ **FIXED: Backend config** - Added `extra="ignore"` to allow frontend env vars without breaking backend
- ✅ **Database sync** - Now using shared Supabase database with Bolt for synchronized development
- ✅ All workflows running and stable

**November 16, 2025**
- ✅ **FIXED: Frontend-Backend API connectivity** - Configured Vite proxy to forward `/api` requests from frontend (port 5000) to backend (port 8000), enabling proper API communication in both development and production environments
- ✅ All workflows running and stable

**November 15, 2025**
- ✅ **FIXED: Endless refresh loop** - Configured Vite HMR to use Replit's WebSocket proxy (wss protocol, port 443, REPLIT_DEV_DOMAIN host)
- ✅ Fixed bcrypt compatibility by downgrading to version 4.1.2
- ✅ All workflows stable and running correctly
- ✅ Frontend now loads without constant reconnections

**November 15, 2025 (Initial Setup)**
- Initial Replit setup completed
- Configured for selfhost mode
- Set up Replit PostgreSQL database
- Installed all Python and Node.js dependencies
- Created admin user
- Configured three workflows (frontend, backend, redis)
- Fixed database connection to use asyncpg
- Fixed missing imports (httpx, python-multipart, status)
- Created transition guide for production deployment

## Contact & Support

For issues or questions:
1. Review error logs in workflow consoles
2. Check `docs/READY_SWITCH.md` for production guidance
3. Consult original documentation in project root
4. Review API docs at `/docs` endpoint
