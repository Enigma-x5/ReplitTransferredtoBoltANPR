# Supabase Setup Guide

This guide walks you through setting up ANPR City API with Supabase.

## Prerequisites

- Supabase account (https://supabase.com)
- Access to Supabase project dashboard

## Step 1: Create Supabase Project

1. Go to https://supabase.com/dashboard
2. Click "New Project"
3. Fill in:
   - Name: `anpr-city`
   - Database Password: Generate strong password and save it
   - Region: Choose closest to your users
4. Wait for project to provision (~2 minutes)

## Step 2: Get Connection Details

1. In your project dashboard, go to **Settings** → **Database**
2. Note the following:
   - **Host**: `db.xxxxxxxxxxxxx.supabase.co`
   - **Database name**: `postgres`
   - **Port**: `5432`
   - **User**: `postgres`
   - **Password**: Your password from Step 1

3. Construct your `DATABASE_URL`:
   ```
   postgresql+asyncpg://postgres:[YOUR_PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
   ```

4. Go to **Settings** → **API**
5. Note:
   - **Project URL**: `https://xxxxxxxxxxxxx.supabase.co`
   - **anon public key**: `eyJhbG...` (long string)
   - **service_role key**: `eyJhbG...` (different long string)

## Step 3: Create Storage Buckets

1. In Supabase dashboard, go to **Storage**
2. Click **Create Bucket**
3. Create first bucket:
   - Name: `anpr-uploads`
   - Public bucket: **NO** (keep private)
   - Click **Create**

4. Create second bucket:
   - Name: `anpr-crops`
   - Public bucket: **NO**
   - Click **Create**

## Step 4: Configure Storage Policies

For each bucket (`anpr-uploads` and `anpr-crops`):

1. Click on the bucket name
2. Go to **Policies** tab
3. Click **New Policy**
4. Click **Create policy from scratch**

### Policy 1: Service Role Full Access

```sql
-- Policy name: Service role full access
-- Allowed operation: All (SELECT, INSERT, UPDATE, DELETE)
-- Target roles: service_role

((role() = 'service_role'::text))
```

This allows the API (using service_role key) to manage files.

### Policy 2: Authenticated Read Access

```sql
-- Policy name: Authenticated users can read
-- Allowed operation: SELECT
-- Target roles: authenticated

((role() = 'authenticated'::text))
```

This allows authenticated users to view files via signed URLs.

## Step 5: Run Database Migration

1. In Supabase dashboard, go to **SQL Editor**
2. Click **New Query**
3. Copy the entire contents of `migrations/001_initial_schema.sql`
4. Paste into the query editor
5. Click **Run** (or press Cmd/Ctrl + Enter)
6. Verify: You should see "Success. No rows returned" (this is normal)
7. Go to **Table Editor** to verify tables were created:
   - users
   - cameras
   - uploads
   - events
   - corrections
   - bolos
   - bolo_matches
   - licenses
   - usage_reports
   - exports
   - audit_logs

## Step 6: Verify Bootstrap Admin User

1. In **Table Editor**, open the `users` table
2. You should see one user:
   - Email: `admin@example.com`
   - Username: `admin`
   - Role: `admin`

This is your bootstrap admin account.

**Default Password**: `changeme123`

**IMPORTANT**: Change this password after first login!

## Step 7: Configure Environment Variables

Create `.env` file in project root:

```bash
# Application Mode
MODE=supabase

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# JWT Configuration (generate a secure random string)
JWT_SECRET=your-super-secret-jwt-key-min-32-characters-long

# Database (from Step 2)
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres

# Supabase (from Step 2)
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbG...[your-anon-key]
SUPABASE_SERVICE_KEY=eyJhbG...[your-service-role-key]

# Redis (local or cloud)
REDIS_URL=redis://localhost:6379/0

# Storage
STORAGE_BUCKET=anpr-uploads
STORAGE_CROPS_BUCKET=anpr-crops

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS (adjust for your frontend)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Generate JWT_SECRET**:
```bash
openssl rand -base64 32
```

## Step 8: Start the Application

### Option A: Docker Compose (Recommended)

```bash
# Start API and Worker (Redis included)
docker-compose -f docker-compose.supabase.yml up -d

# View logs
docker-compose logs -f api
docker-compose logs -f worker
```

### Option B: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis (or use cloud Redis)
redis-server

# Terminal 1: Start API
python -m uvicorn src.main:app --reload

# Terminal 2: Start Worker
python -m src.worker
```

## Step 9: Verify Installation

1. **Check API Health**:
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"ok"}
   ```

2. **Login as Admin**:
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@example.com","password":"changeme123"}'

   # Should return JWT token
   ```

3. **Access API Docs**:
   Open http://localhost:8000/docs in browser

4. **Check Prometheus Metrics**:
   Open http://localhost:8000/metrics

## Step 10: Test Upload Workflow

1. Get JWT token (from Step 9, login response)

2. Create a camera:
   ```bash
   curl -X POST http://localhost:8000/api/cameras \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test Camera",
       "lat": 40.7128,
       "lon": -74.0060,
       "active": true
     }'
   ```

3. Upload a test video:
   ```bash
   curl -X POST http://localhost:8000/api/uploads \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -F "file=@test_video.mp4" \
     -F "camera_id=CAMERA_ID_FROM_STEP_2"

   # Returns: {"job_id":"xxx-xxx-xxx","status":"queued",...}
   ```

4. Check job status:
   ```bash
   curl http://localhost:8000/api/jobs/JOB_ID_FROM_STEP_3 \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

5. Verify in Supabase:
   - Go to **Storage** → **anpr-uploads** → Should see uploaded video
   - Go to **Table Editor** → **uploads** → Should see upload record
   - After processing: **events** table should have detection records
   - **anpr-crops** bucket should have crop images

## Troubleshooting

### Issue: "Connection refused" to database

- Verify `DATABASE_URL` has correct password
- Check if your IP is allowed (Supabase allows all by default)
- Try connecting with `psql` to verify credentials

### Issue: "Bucket not found" error

- Verify bucket names match exactly: `anpr-uploads` and `anpr-crops`
- Check buckets exist in Supabase Storage dashboard
- Verify storage policies are configured

### Issue: "Invalid JWT" errors

- Verify `SUPABASE_SERVICE_KEY` is correct (not anon key)
- Check JWT_SECRET is set in .env
- Verify token hasn't expired (default: 7 days)

### Issue: Worker not processing jobs

- Check Redis is running: `redis-cli ping`
- Verify `REDIS_URL` in .env
- Check worker logs: `docker-compose logs -f worker`
- Verify worker container is running: `docker-compose ps`

### Issue: Low detection accuracy

This is expected! The detector is a stub. Replace `src/detectors/yolo_easyocr_adapter.py` with your real YOLO + EasyOCR implementation.

## Monitoring Supabase Usage

1. Go to **Settings** → **Billing**
2. Check:
   - Database size
   - Storage size
   - Bandwidth usage
   - API requests

Free tier includes:
- 500MB database
- 1GB storage
- 2GB bandwidth/month

For production, consider Pro plan ($25/mo) with:
- 8GB database
- 100GB storage
- 250GB bandwidth

## Backup Strategy

### Database Backup

```bash
# Manual backup
pg_dump -h db.xxxxxxxxxxxxx.supabase.co \
  -U postgres \
  -d postgres \
  -f backup_$(date +%Y%m%d).sql

# Restore
psql -h db.xxxxxxxxxxxxx.supabase.co \
  -U postgres \
  -d postgres \
  -f backup_20240101.sql
```

### Storage Backup

Use `rclone` or AWS CLI to sync Supabase storage to S3/local:

```bash
# Install rclone
# Configure Supabase as S3-compatible storage
rclone sync supabase:anpr-uploads ./backups/uploads
rclone sync supabase:anpr-crops ./backups/crops
```

## Migration to Self-Hosted

If you later want to migrate from Supabase to self-hosted:

1. Dump database (see Backup Strategy above)
2. Export storage buckets with rclone
3. Update `.env`:
   ```
   MODE=selfhost
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/anpr_city
   MINIO_ENDPOINT=localhost:9000
   # Remove SUPABASE_* vars
   ```
4. Start self-hosted stack: `docker-compose up -d`
5. Restore database: `psql -f backup.sql`
6. Upload files to MinIO

## Security Hardening

### 1. Change Default Admin Password

```bash
# Login and get token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme123"}' \
  | jq -r '.access_token')

# Update password (TODO: implement password change endpoint)
# For now, update directly in Supabase Table Editor or via SQL:
# UPDATE users SET hashed_password = crypt('new_password', gen_salt('bf'))
# WHERE email = 'admin@example.com';
```

### 2. Rotate JWT Secret

- Generate new secret: `openssl rand -base64 32`
- Update `.env`
- Restart services
- All users must re-login

### 3. Enable RLS on Supabase Tables (Optional)

If you want database-level security (in addition to API-level):

```sql
-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE cameras ENABLE ROW LEVEL SECURITY;
-- etc for all tables

-- Create policies (example)
CREATE POLICY "Service role full access" ON users
  FOR ALL USING (auth.role() = 'service_role');
```

**Note**: Current implementation uses application-level security (JWT in API). RLS is optional additional layer.

## Next Steps

1. **Integrate Real Detector**: Replace stub in `src/detectors/yolo_easyocr_adapter.py`
2. **Set Up Monitoring**: Configure Prometheus + Grafana
3. **Create Users**: Use `/api/users` to create clerk accounts
4. **Configure BOLOs**: Set up alert patterns via `/api/bolos`
5. **Test Workflow**: Upload videos, review detections, submit corrections

## Support

- Supabase Docs: https://supabase.com/docs
- Supabase Discord: https://discord.supabase.com
- Project Issues: GitHub Issues

---

**Setup complete! Your ANPR City API is now running on Supabase.**
