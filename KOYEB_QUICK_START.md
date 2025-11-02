# Koyeb Quick Start - Step by Step

## Deployment Order (Important!)

**Create databases FIRST, then deploy app!**

### Step 1: Create PostgreSQL in Koyeb
1. Go to Koyeb Dashboard
2. Click "Databases" → "Create Database"
3. Select **PostgreSQL**
4. Choose plan (Starter is fine)
5. Click "Create"
6. Wait ~1-2 minutes for provisioning
7. Click on your new database
8. **Copy the Connection String** (the full `postgresql://...` URL)
9. Save it somewhere - this is your `DATABASE_URL`

### Step 2: Create Redis in Koyeb
1. Still in "Databases"
2. Click "Create Database"
3. Select **Redis**
4. Choose plan
5. Click "Create"
6. Wait for provisioning
7. Click on your new Redis
8. **Copy the Connection URL** (the `redis://...` URL)
9. Save it - this is your `REDIS_URL`

### Step 3: Deploy Your App
1. Go to "Apps" → "Create App"
2. Connect GitHub repository: `Ezekiel32/ASR_SALES_CALLS_AGENT`
3. Make sure builder is set to **"Docker"** (not Buildpack)
4. Select GPU instance: **RTX-4000-SFF-ADA**
5. Set port: **8000**

### Step 4: Add Environment Variables
Before clicking "Deploy", go to "Environment Variables" and add:

```bash
# Paste the connection strings you copied above
DATABASE_URL=<paste_postgres_connection_string_here>
REDIS_URL=<paste_redis_connection_string_here>

# Your API keys
IVRIT_API_KEY=your_key_here
NVIDIA_API_KEY=your_key_here
PYANNOTE_AUTH_TOKEN=your_hf_token_here

# CORS
CORS_ORIGINS=https://ivreetmeet.netlify.app

# Optional but recommended
S3_BUCKET=your-bucket
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

### Step 5: Deploy!
Click "Deploy" and wait for build to complete.

### Step 6: Run Migrations
After deployment:
1. Go to your app → "Runtime" → "Shell"
2. Run: `alembic upgrade head`
3. This creates all database tables

### Step 7: Test
Your app will be at: `https://your-app-name.koyeb.app`

Test health endpoint:
```bash
curl https://your-app-name.koyeb.app/healthz
```

## Summary

**Order matters:**
1. ✅ Create PostgreSQL → Get `DATABASE_URL`
2. ✅ Create Redis → Get `REDIS_URL`  
3. ✅ Deploy app with environment variables
4. ✅ Run migrations
5. ✅ Test!

**Total time:** ~10 minutes

