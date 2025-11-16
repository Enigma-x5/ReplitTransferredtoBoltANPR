# ANPR City Frontend - Setup Guide

## Quick Start

This frontend is designed to work with your existing FastAPI backend that matches the `openapi.yaml` specification.

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure API Connection

Edit `.env` file and set your backend URL:

```bash
# For local development (backend at localhost:8000)
VITE_API_BASE_URL=http://localhost:8000/api

# For production
VITE_API_BASE_URL=https://api.yourdomain.example.com/api
```

### 3. Run Development Server

```bash
npm run dev
```

The app will start at `http://localhost:8080`

### 4. Login

Use credentials from your backend system. The frontend expects:
- Email/password authentication
- JWT token in response with `access_token` field
- User role (`admin` or `clerk`) in user profile

## Available Pages

### 🏠 Dashboard (`/dashboard`)
- System metrics overview
- Recent detection events
- Camera location map placeholder (OlaMaps integration pending)

### 📹 Cameras (`/cameras`)
- View all cameras
- **Admin only**: Create/edit cameras with location data

### 📤 Uploads (`/uploads`)
- Upload MP4 videos for processing
- Track job status (queued, processing, done, failed)

### 📋 Events (`/events`)
- Search detections by plate, camera, date range
- View confidence scores and review states

### ✅ Review Queue (`/review`)
- Human-in-the-loop verification
- Confirm correct detections
- Submit corrections for misreads

### 🚨 BOLOs (`/bolos`)
- View active Be On the Lookout alerts
- **Admin only**: Create new BOLOs with plate patterns

### ⚙️ System Status (`/system`)
- Health checks
- License usage information
- Database/storage status

## Role-Based Access

### Admin Role
- Full access to all features
- Can create/edit cameras
- Can create BOLOs
- Can manage users (if backend supports)

### Clerk Role
- View cameras (read-only)
- Upload videos
- Search and view events
- Review and correct detections
- View BOLOs (read-only)

## Architecture Notes

### API Client (`src/api/client.ts`)
- Centralized Axios instance
- Automatic JWT token injection
- 401 handling with auto-logout
- All endpoints match OpenAPI spec

### Authentication (`src/auth/`)
- JWT stored in localStorage (centralized in `tokenStorage.ts`)
- React Context for auth state
- Protected routes for authenticated pages
- Ready to migrate to HttpOnly cookies if needed

### Design System
- Professional navy/slate blue theme
- Amber accents for alerts
- All colors defined in `src/index.css` using HSL
- Shadcn/ui component library

## API Integration Checklist

Ensure your backend implements these endpoints as defined in `openapi.yaml`:

- ✅ `POST /auth/login` - Returns JWT token
- ✅ `GET /cameras` - List cameras
- ✅ `POST /cameras` - Create camera (admin)
- ✅ `PATCH /cameras/{id}` - Update camera (admin)
- ✅ `POST /uploads` - Upload video file
- ✅ `GET /jobs/{job_id}` - Check job status
- ✅ `GET /events` - Search events with filters
- ✅ `GET /events/{id}` - Get single event
- ✅ `POST /events/{id}/confirm` - Confirm detection
- ✅ `POST /events/{id}/correction` - Submit correction
- ✅ `GET /feedback/pending` - Get unreviewed events
- ✅ `GET /bolos` - List BOLOs
- ✅ `POST /bolos` - Create BOLO (admin)
- ✅ `GET /admin/health` - System health
- ✅ `GET /licenses/usage` - License usage

## CORS Configuration

If running frontend and backend on different ports during development, ensure your backend allows CORS from `http://localhost:8080`.

Example FastAPI CORS setup:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Production Build

```bash
# Build for production
npm run build

# Preview production build locally
npm run preview
```

Built files will be in `dist/` directory. Deploy these static files to any web server or CDN.

## Deployment Options

### Option 1: Static Hosting
Deploy `dist/` to:
- Netlify
- Vercel
- AWS S3 + CloudFront
- Azure Static Web Apps

### Option 2: Docker
```dockerfile
FROM nginx:alpine
COPY dist/ /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Option 3: Same Server as Backend
Configure your backend to serve static files from `dist/` directory.

## Environment Variables

Only one environment variable is needed:

- `VITE_API_BASE_URL` - Backend API base URL (default: `/api`)

Note: Vite requires `VITE_` prefix for environment variables to be exposed to the client.

## Troubleshooting

### "Network Error" or CORS issues
- Check that backend is running
- Verify CORS settings in backend
- Confirm `VITE_API_BASE_URL` is correct

### Login redirects immediately back to login
- Check JWT token format from backend
- Verify token is being stored (check browser DevTools → Application → Local Storage)
- Ensure token doesn't expire immediately

### 401 Unauthorized on authenticated requests
- Token may be expired
- Backend may not be accepting the token format
- Check `Authorization: Bearer <token>` header is being sent

### TypeScript errors
```bash
npm run build
```
Will show all type errors. Frontend is fully typed to match OpenAPI spec.

## Next Steps

1. **Map Integration**: Add OlaMaps implementation in `DashboardPage.tsx`
2. **Image Display**: Implement presigned URL fetching for event crop images
3. **Real-time Updates**: Add WebSocket or polling for live event updates
4. **Export Feature**: Implement labeled data export functionality
5. **Keyboard Shortcuts**: Add hotkeys for review queue actions

## Support

For backend-related issues, refer to your backend documentation.
For frontend issues, check:
- Browser console for errors
- Network tab for failed API calls
- React DevTools for component state
