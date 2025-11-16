# Switching from Replit (Selfhost) Mode to Production (Supabase) Mode

This document explains how to transition from the current **Replit/Selfhost** development mode to a production-ready **Supabase/External** mode when you're ready to deploy.

## Current Mode: Replit/Selfhost (Development)

The application is currently configured to run entirely within the Replit environment using:

### Current Configuration
- **MODE**: `selfhost`
- **DATABASE_URL**: Replit's managed PostgreSQL (auto-configured)
- **REDIS_URL**: `redis://localhost:6379/0` (local Redis server)
- **Storage**: MinIO (local object storage)
- **CORS**: `*` (allows all origins for development)

### Services Running
1. **Backend API** - Port 8000
2. **Frontend** - Port 5000
3. **Redis Server** - Port 6379 (local)
4. **PostgreSQL** - Replit managed database

---

## Production Mode: Supabase/External (Ready)

When you're ready to deploy to production or use external managed services, follow this transition guide.

### Step 1: Set Up External Services

#### 1.1 Create Supabase Project
1. Go to https://supabase.com
2. Create a new project
3. Note your project credentials:
   - Project URL
   - Anon/Public Key
   - Service Role Key
   - Database URL

#### 1.2 Set Up Supabase Storage
Run this SQL in the Supabase SQL Editor to create storage buckets:

```sql
INSERT INTO storage.buckets (id, name, public) 
VALUES ('anpr-uploads', 'anpr-uploads', false);

INSERT INTO storage.buckets (id, name, public) 
VALUES ('anpr-crops', 'anpr-crops', false);
```

#### 1.3 Run Database Migrations
Copy the contents of `migrations/001_initial_schema.sql` and run it in the Supabase SQL Editor.

#### 1.4 Create External Redis (Upstash or similar)
1. Go to https://upstash.com (or your preferred Redis provider)
2. Create a new Redis database
3. Get the connection URL (format: `redis://user:password@host:port`)

### Step 2: Update Environment Variables

Update these Replit Secrets to switch to production mode:

| Variable | Current (Selfhost) | Production (Supabase) |
|----------|-------------------|----------------------|
| **MODE** | `selfhost` | `supabase` |
| **DATABASE_URL** | (Replit auto-configured) | `postgresql+asyncpg://user:pass@db.project.supabase.co:5432/postgres` |
| **SUPABASE_URL** | (not set) | `https://your-project.supabase.co` |
| **SUPABASE_KEY** | (not set) | Your Supabase anon key |
| **SUPABASE_SERVICE_KEY** | (not set) | Your Supabase service role key |
| **REDIS_URL** | `redis://localhost:6379/0` | `redis://user:pass@your-redis-provider.com:port` |
| **CORS_ORIGINS** | `*` | Your production domain(s), e.g., `https://yourdomain.com` |

### Step 3: Frontend Configuration

Update the frontend API base URL for production:

**During Development (Current)**:
- Frontend calls backend via relative path `/api`
- Works because both run in same Replit environment

**For Production**:
Create a `.env` file in the `frontend/` directory:

```bash
# For production deployment
VITE_API_BASE_URL=https://your-backend-domain.com/api
```

Or set this as a Replit Secret if deploying the frontend on Replit.

### Step 4: Remove Local Services (Optional)

When using external services, you can remove these local workflows:
- **redis-server** workflow (using external Redis instead)

Keep only:
- **backend** workflow
- **frontend** workflow

### Step 5: Update CORS for Production

In Replit Secrets, update:
```
CORS_ORIGINS=https://your-frontend-domain.com,https://yourdomain.com
```

### Step 6: Test the Transition

1. Update all environment variables
2. Restart workflows:
   - Backend workflow
   - Frontend workflow
3. Test login with admin credentials
4. Verify database connectivity
5. Test file upload (storage)
6. Monitor logs for any errors

---

## Checklist: Replit → Production Transition

- [ ] Create Supabase project and note credentials
- [ ] Set up Supabase storage buckets
- [ ] Run database migrations in Supabase
- [ ] Create external Redis instance
- [ ] Update `MODE` to `supabase`
- [ ] Update `DATABASE_URL` to Supabase connection string
- [ ] Add `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`
- [ ] Update `REDIS_URL` to external Redis
- [ ] Update `CORS_ORIGINS` to production domains
- [ ] Configure `VITE_API_BASE_URL` in frontend
- [ ] Test all functionality in new environment
- [ ] Remove local Redis workflow if using external Redis

---

## Rollback to Replit Mode

If you need to switch back to Replit/Selfhost mode:

1. Set `MODE=selfhost`
2. Remove or clear Supabase credentials
3. Set `REDIS_URL=redis://localhost:6379/0`
4. Set `CORS_ORIGINS=*`
5. Restart workflows

---

## Additional Production Considerations

### Security
- Generate a new `JWT_SECRET` for production (stronger, 64+ characters)
- Use strong `ADMIN_PASSWORD`
- Enable HTTPS/SSL for all services
- Restrict CORS to specific domains only

### Monitoring
- Enable Prometheus metrics (already configured)
- Set up logging aggregation
- Monitor Redis queue length
- Track database performance

### Scaling
- Configure worker concurrency (`WORKER_CONCURRENCY`)
- Adjust database connection pool size if needed
- Consider multiple worker instances for high load

---

## Support

For issues during transition:
- Check Supabase dashboard for database connectivity
- Verify Redis connection with `redis-cli ping`
- Review backend logs for detailed error messages
- Ensure all environment variables are set correctly
