# Railway Deployment Guide

Railway is much simpler than AWS - no security groups, no SSH keys, just deploy and go!

## 🚀 Quick Deploy Steps

### 1. Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up/login with GitHub
3. Click "New Project"

### 2. Connect Repository
1. Click "Deploy from GitHub repo"
2. Select your repository: `ASR_SALES_CALLS_AGENT`
3. Railway will auto-detect it's Python

### 3. Add Services

You'll need **3 services**:

#### A. **Main API Service** (FastAPI)
- Uses the root directory
- Railway will auto-detect Python
- Port will be set via `$PORT` env var

#### B. **PostgreSQL Database**
1. Click "New" → "Database" → "Add PostgreSQL"
2. Railway creates DB automatically
3. Copy the `DATABASE_URL` connection string

#### C. **Redis** (for Celery)
1. Click "New" → "Database" → "Add Redis"
2. Railway creates Redis automatically
3. Copy the `REDIS_URL` connection string

### 4. Configure Environment Variables

Go to your API service → Variables tab, add:

```bash
# Database (from PostgreSQL service)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (from Redis service)
REDIS_URL=${{Redis.REDIS_URL}}

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
```

**Railway automatically sets:**
- `$PORT` - Port to listen on (don't hardcode)
- `$DATABASE_URL` - From PostgreSQL service
- `$REDIS_URL` - From Redis service

### 5. Run Migrations

In Railway dashboard:
1. Go to API service → Settings → "Generate Domain"
2. Get your Railway URL (e.g., `your-app.railway.app`)
3. Go to "Shell" tab or use "Run Command"
4. Run:
```bash
alembic upgrade head
```

### 6. Deploy

Railway auto-deploys on every git push! Or manually:
1. Click "Deploy" button
2. Watch the logs
3. Once deployed, your API is live at `your-app.railway.app`

## 📝 Railway-Specific Features

### Automatic HTTPS
Railway provides free SSL certificates automatically!

### Auto-Scaling
Railway can auto-scale based on traffic (upgrade plan for better scaling)

### Logs
- Real-time logs in Railway dashboard
- No SSH needed - everything in browser

### Database Backups
Railway PostgreSQL includes automated backups (check plan)

## 🔧 Configuration Files

### `railway.json`
Main Railway configuration - already created ✅

### `Procfile`
Defines services (web + worker) - already created ✅

### `nixpacks.toml`
Build configuration - already created ✅

## 🎯 Multiple Services Setup

Railway supports multiple services in one project:

1. **API Service** (FastAPI)
   - Root directory
   - Port: `$PORT`
   - Command: `uvicorn agent_service.api:app --host 0.0.0.0 --port $PORT`

2. **Celery Worker** (separate service)
   - Same root directory
   - Command: `celery -A agent_service.services.processing_queue.celery_app worker --loglevel=info`
   - Shares same env vars as API

## 💰 Pricing

Railway has a generous free tier:
- $5 free credit/month
- Perfect for development/small projects
- Upgrade for production scaling

## 🐛 Troubleshooting

### Port Issues
- Railway sets `$PORT` automatically
- Don't hardcode port 8000, use `$PORT`

### Database Connection
- Use `${{Postgres.DATABASE_URL}}` in env vars
- Railway handles connection pooling

### Build Failures
- Check logs in Railway dashboard
- Common issues: missing dependencies, Python version

### Celery Worker Not Running
- Create separate service with Procfile `worker` command
- Ensure Redis URL is set correctly

## 🚀 After Deployment

1. **Test API**:
   ```bash
   curl https://your-app.railway.app/healthz
   ```

2. **Update Frontend**:
   - In Netlify, set `VITE_API_BASE_URL=https://your-app.railway.app`

3. **Monitor**:
   - Check Railway dashboard for logs
   - Set up alerts if needed

## ✅ Benefits Over AWS EC2

- ✅ No security groups to configure
- ✅ No SSH keys needed
- ✅ Automatic HTTPS
- ✅ Built-in PostgreSQL & Redis
- ✅ Auto-deploy on git push
- ✅ Simple pricing
- ✅ Better developer experience

