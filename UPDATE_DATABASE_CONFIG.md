# Fix Login Issue - Database Configuration Required

## Problem
Your backend is trying to connect to `localhost:5432` (local PostgreSQL) instead of Supabase, which is why login fails.

## Solution: Get Supabase Credentials

### Step 1: Get Database Password

1. Go to: https://supabase.com/dashboard
2. Select your project: `sgetvwnbkluohcbqapfr`
3. Navigate to: **Settings** → **Database**
4. Scroll to "Connection String" section
5. Click on "Connection pooling" tab (this is what we need for Replit)
6. You'll see a connection string like:
   ```
   postgresql://postgres.sgetvwnbkluohcbqapfr:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
7. Copy the **entire connection string** including the password

### Step 2: Get Service Role Key

1. In the same Supabase project dashboard
2. Navigate to: **Settings** → **API**
3. Scroll to "Project API keys" section
4. Find **service_role** key (NOT the anon key)
5. Click the eye icon to reveal it
6. Copy the entire key (starts with `eyJhbG...`)

### Step 3: Update .env File

Replace these two lines in `/tmp/cc-agent/60261000/project/.env`:

**Current (WRONG):**
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/anpr_city
SUPABASE_SERVICE_KEY=SUPABASE_SERVICE_ROLE_KEY
```

**New (CORRECT):**
```bash
DATABASE_URL=postgresql://postgres.sgetvwnbkluohcbqapfr:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
SUPABASE_SERVICE_KEY=[YOUR-SERVICE-ROLE-KEY]
```

**Important Notes:**
- Use `postgresql://` NOT `postgresql+asyncpg://` (the backend code converts it automatically)
- Use port `6543` (connection pooler) NOT `5432` (direct connection)
- Replace `[YOUR-PASSWORD]` with the actual password from Step 1
- Replace `[YOUR-SERVICE-ROLE-KEY]` with the actual key from Step 2

### Step 4: Restart Backend

After updating the `.env` file:
1. Stop the running backend (if any)
2. Start it again
3. The backend will now connect to Supabase

### Step 5: Test Login

Try logging in with:
- **Email**: `admin@admin.com`
- **Password**: `Admin@123`

It should work now!

---

## Quick Copy-Paste Template

Once you have your credentials, copy this entire block and paste it into your `.env` file (replacing the old DATABASE_URL and SUPABASE_SERVICE_KEY lines):

```bash
# === REPLACE THESE TWO LINES IN YOUR .env FILE ===
DATABASE_URL=postgresql://postgres.sgetvwnbkluohcbqapfr:YOUR_DB_PASSWORD_HERE@aws-0-us-east-1.pooler.supabase.com:6543/postgres
SUPABASE_SERVICE_KEY=YOUR_SERVICE_ROLE_KEY_HERE
```

---

## Alternative: Let Me Do It

If you provide me with:
1. The complete connection string from Supabase (including password)
2. The service_role key

I can update the `.env` file for you immediately.

Just paste them in your next message like this:
```
Connection string: postgresql://postgres.sgetvwnbkluohcbqapfr:abc123...
Service role key: eyJhbGci...
```
