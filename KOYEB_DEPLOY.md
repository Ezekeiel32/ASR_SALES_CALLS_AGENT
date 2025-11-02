# Koyeb Deployment Guide

Koyeb is a serverless platform that automatically handles Docker, scaling, and HTTPS. Much simpler than AWS!

## 🚀 Quick Deploy Steps

### 1. Create Koyeb Account
1. Go to [koyeb.com](https://www.koyeb.com)
2. Sign up/login with GitHub
3. Get $5.50 free credit/month!

### 2. Create PostgreSQL Database

In Koyeb Dashboard:
1. Go to "Databases" → "Create Database"
2. Select **PostgreSQL**
3. Choose plan (Free tier available)
4. Copy the connection string (looks like: `postgresql://user:pass@host:port/db`)

### 3. Create Redis Instance

In Koyeb Dashboard:
1. Go to "Databases" → "Create Database"
2. Select **Redis**
3. Choose plan
4. Copy the connection URL (looks like: `redis://host:port`)

### 4. Deploy Your App

**Option A: From GitHub (Recommended)**
1. Go to "Apps" → "Create App"
2. Select "GitHub" as source
3. Choose your repository: `ASR_SALES_CALLS_AGENT`
4. Koyeb will auto-detect Dockerfile

**Option B: From Dockerfile**
1. Make sure `Dockerfile` is in your repo root ✅
2. Koyeb will build and deploy automatically

### 5. Configure Environment Variables

In your Koyeb App → Settings → Environment Variables:

```bash
# Database (from PostgreSQL service)
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis (from Redis service)
REDIS_URL=redis://host:port

# CORS (for Netlify frontend)
CORS_ORIGINS=https://ivreetmeet.netlify.app

# API Keys
IVRIT_API_KEY=your_ivrit_key
NVIDIA_API_KEY=your_nvidia_key
RUNPOD_API_KEY=your_runpod_key
IVRIT_RUNPOD_ENDPOINT_ID=your_endpoint_id

# Optional - PyAnnote
PYANNOTE_AUTH_TOKEN=your_huggingface_token

# S3 (optional, for large files)
S3_BUCKET=your-bucket-name
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Port (Koyeb sets this automatically)
PORT=8000
```

### 6. Run Database Migrations

**Option A: Via Koyeb Shell**
1. Go to your app → "Runtime" → "Shell"
2. Run:
```bash
alembic upgrade head
```

**Option B: Via CLI**
```bash
koyeb apps exec <app-name> -- alembic upgrade head
```

### 7. Deploy Celery Worker (Optional)

Create a **second service** for Celery:

1. Go to "Apps" → "Create Service"
2. Use same GitHub repo
3. Set **Start Command**:
```bash
celery -A agent_service.services.processing_queue.celery_app worker --loglevel=info
```
4. Use same environment variables (especially `REDIS_URL`)

### 8. Get Your URL

Once deployed:
- Koyeb gives you: `https://your-app-<hash>.koyeb.app`
- Or set custom domain in Settings

## 📝 Configuration Files

### `Dockerfile`
Multi-stage build for optimized image size ✅

### `koyeb.yaml`
Optional - Koyeb config file ✅

### `.dockerignore`
Excludes unnecessary files from Docker build ✅

## 🎯 Koyeb Features

### Automatic HTTPS
Free SSL certificates for all domains!

### Auto-Scaling
Scales from 0 to N based on traffic (serverless)

### Global CDN
Deploys to multiple regions automatically

### Logs
Real-time logs in Koyeb dashboard
- No SSH needed
- Searchable logs
- Alert on errors

### Database Backups
Automatic backups (check your plan)

## 💰 Pricing

**Free Tier:**
- $5.50 credit/month
- Perfect for development
- Includes PostgreSQL and Redis

**Production:**
- Pay per use
- Scales automatically
- Very affordable

## 🐛 Troubleshooting

### Build Failures
- Check logs in Koyeb dashboard
- Common issues: Missing dependencies, wrong Python version
- Build logs show exact error

### Port Issues
- Use `${PORT:-8000}` in Dockerfile (already set) ✅
- Koyeb sets `PORT` automatically

### Database Connection
- Use `DATABASE_URL` from Koyeb PostgreSQL service
- Connection pooling handled automatically

### Celery Not Working
- Make sure Redis URL is correct
- Check Celery logs in worker service
- Verify Redis is accessible

### Memory Issues
- Koyeb free tier: 512MB RAM
- For ML models, may need to upgrade
- Or use S3 for model storage (already configured)

## 🚀 After Deployment

1. **Test API**:
   ```bash
   curl https://your-app.koyeb.app/healthz
   ```

2. **Update Frontend**:
   - In Netlify, set `VITE_API_BASE_URL=https://your-app.koyeb.app`

3. **Monitor**:
   - Check Koyeb dashboard for metrics
   - Set up alerts if needed

## 🔄 Auto-Deploy

Koyeb auto-deploys on every git push to your main branch!

Or trigger manual deploy:
- Dashboard → App → "Redeploy"

## ✅ Benefits Over AWS EC2

- ✅ No security groups
- ✅ No SSH keys
- ✅ Automatic HTTPS
- ✅ Built-in PostgreSQL & Redis
- ✅ Auto-deploy on git push
- ✅ Serverless (scales to zero)
- ✅ Global CDN
- ✅ Simple pricing
- ✅ Better developer experience

## 📊 Resource Limits

**Free Tier:**
- 512MB RAM per service
- 1 vCPU
- 10GB storage

**For ML Models:**
- Consider upgrading to 1GB+ RAM
- Or use S3 for models (already configured) ✅

## 🔧 Advanced: Multiple Services

You can have:
1. **API Service** - FastAPI web server
2. **Worker Service** - Celery worker (separate)
3. **PostgreSQL** - Database
4. **Redis** - Task queue

All connected via environment variables!

