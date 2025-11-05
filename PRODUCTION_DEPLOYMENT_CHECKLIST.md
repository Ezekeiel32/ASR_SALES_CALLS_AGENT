# Production Deployment Checklist

Complete guide for deploying IvriMeet to production with RunPod Serverless backend.

## Pre-Deployment Requirements

### 1. Accounts & Services Setup
- [ ] RunPod account created (https://www.runpod.io)
- [ ] Netlify account created (https://www.netlify.com)
- [ ] PostgreSQL database provisioned (Neon, Supabase, or AWS RDS)
- [ ] AWS S3 bucket created for audio storage
- [ ] Ivrit API key obtained
- [ ] DeepSeek API key obtained (for LLM/summarization)
- [ ] Backend hosting service chosen (Railway, Render, or your own server)

### 2. Repository Setup
- [ ] Code pushed to GitHub/GitLab
- [ ] `.env.example` files reviewed
- [ ] Sensitive credentials NOT committed to git

## Backend Deployment (Part 1 - RunPod Serverless)

### Step 1: RunPod Endpoint Creation ✅ (IN PROGRESS)
- [x] GitHub repository connected to RunPod
- [ ] Docker image built successfully
- [ ] Endpoint status shows "Ready"
- [ ] Endpoint ID copied (format: `ep-xxxxx`)
- [ ] RunPod API key copied from account settings

### Step 2: RunPod Environment Variables
After build completes, add these in RunPod endpoint settings:

```bash
# Critical Variables
DATABASE_URL=postgresql://user:password@host:5432/ivrimeet_db
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
S3_BUCKET=your-bucket-name
S3_REGION=us-east-1
IVRIT_API_KEY=your_ivrit_api_key
LLM_API_KEY=your_deepseek_api_key
JWT_SECRET_KEY=your_secret_key_min_32_characters_long
```

- [ ] All environment variables added
- [ ] Endpoint tested with test job
- [ ] Endpoint URL noted (format: `https://api-xxxxx.runpod.io`)

## Backend Deployment (Part 2 - API Server)

Choose ONE of these options:

### Option A: Railway
1. [ ] Connect GitHub repository to Railway
2. [ ] Set build command: `pip install -r requirements.txt`
3. [ ] Set start command: `uvicorn agent_service.api:app --host 0.0.0.0 --port $PORT`
4. [ ] Add environment variables (see below)
5. [ ] Deploy and note the URL

### Option B: Render
1. [ ] Connect GitHub repository to Render
2. [ ] Create new Web Service
3. [ ] Set build command: `pip install -r requirements.txt`
4. [ ] Set start command: `uvicorn agent_service.api:app --host 0.0.0.0 --port $PORT`
5. [ ] Add environment variables (see below)
6. [ ] Deploy and note the URL

### Option C: Your Own Server
1. [ ] SSH into server
2. [ ] Clone repository
3. [ ] Install dependencies: `pip install -r requirements.txt`
4. [ ] Set up systemd service or PM2
5. [ ] Configure nginx reverse proxy
6. [ ] Set environment variables
7. [ ] Start service
8. [ ] Note the public URL

### Backend API Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/ivrimeet_db

# RunPod Configuration
USE_RUNPOD=true
RUNPOD_ENDPOINT_ID=ep-xxxxx
RUNPOD_API_KEY=your_runpod_api_key
RUNPOD_SERVERLESS_URL=https://api-xxxxx.runpod.io

# AWS S3
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
S3_BUCKET=your-bucket-name
S3_REGION=us-east-1

# External APIs
IVRIT_API_KEY=your_ivrit_api_key
IVRIT_API_URL=https://api.ivrit.ai
LLM_API_KEY=your_deepseek_api_key
LLM_MODEL=deepseek-ai/deepseek-v3.1-terminus

# Security
JWT_SECRET_KEY=your_secret_key_min_32_characters_long

# CORS (add your frontend domain)
CORS_ORIGINS=http://localhost:3000,https://your-app.netlify.app

# Optional
ENVIRONMENT=production
LOG_LEVEL=INFO
```

- [ ] All environment variables configured
- [ ] Backend API accessible at public URL
- [ ] Health check endpoint working: `GET /healthz`

## Frontend Deployment (Netlify)

### Step 1: Connect Repository
1. [ ] Go to Netlify Dashboard
2. [ ] Click "Add new site" → "Import an existing project"
3. [ ] Connect GitHub/GitLab
4. [ ] Select `ASR_SALES_CALLS_AGENT` repository

### Step 2: Build Configuration
Verify these settings:

```toml
[build]
  base = "IvriMeet"
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "18"
```

- [ ] Base directory: `IvriMeet`
- [ ] Build command: `npm run build`
- [ ] Publish directory: `dist`
- [ ] Node version: 18

### Step 3: Environment Variables
Add in Netlify: Site settings → Build & deploy → Environment variables

```bash
# Backend API URL (REQUIRED)
VITE_API_BASE_URL=https://your-backend-api-url.com

# Optional: Gemini API (for live transcription)
GEMINI_API_KEY=your_gemini_api_key
```

- [ ] `VITE_API_BASE_URL` set to backend API URL
- [ ] Optional: `GEMINI_API_KEY` added if using live transcription

### Step 4: Deploy
1. [ ] Click "Deploy site"
2. [ ] Wait for build to complete (3-5 minutes)
3. [ ] Site deployed at `https://your-app.netlify.app`
4. [ ] Custom domain configured (optional)

## Post-Deployment Verification

### Backend API Tests
- [ ] Health check: `curl https://your-backend-url.com/healthz`
- [ ] Authentication working
- [ ] Database connection successful
- [ ] S3 storage accessible
- [ ] RunPod endpoint reachable

### RunPod Endpoint Tests
```bash
# Test with provided utility
cd ASR_SALES_CALLS_AGENT
export RUNPOD_ENDPOINT_ID=ep-xxxxx
export RUNPOD_API_KEY=your_key

python scripts/runpod_utils.py test-endpoint
```

- [ ] Endpoint responds to health checks
- [ ] Test job completes successfully
- [ ] Processing time acceptable

### Frontend Tests
- [ ] Open `https://your-app.netlify.app`
- [ ] Login functionality works
- [ ] Can upload meeting audio file
- [ ] Upload progress shows correctly
- [ ] Meeting processes successfully
- [ ] Transcript displays
- [ ] Summary generates
- [ ] Speaker identification works
- [ ] All pages load without errors
- [ ] Check browser console for errors
- [ ] Test on mobile device

### Integration Tests
- [ ] Upload test meeting through frontend
- [ ] Verify backend receives request
- [ ] Verify RunPod processes the job
- [ ] Verify results stored in database
- [ ] Verify audio stored in S3
- [ ] Verify frontend displays results correctly

## Backend CORS Configuration

Ensure your backend allows requests from Netlify:

```python
# In agent_service/api.py or environment variables
CORS_ORIGINS=https://your-app.netlify.app,http://localhost:3000
```

- [ ] Netlify domain added to CORS origins
- [ ] CORS headers configured correctly
- [ ] Preflight requests handled

## Database Setup

### Run Migrations
```bash
# SSH into backend server or use Railway/Render CLI
alembic upgrade head
```

- [ ] All migrations applied
- [ ] Tables created successfully
- [ ] Default organization created

### Seed Data (Optional)
```bash
python -c "from agent_service.database.seed_data import seed_database; seed_database()"
```

- [ ] Seed data loaded (if needed)
- [ ] Test users created
- [ ] Sample data added

## Monitoring & Maintenance

### Set Up Monitoring
- [ ] RunPod endpoint metrics monitored
- [ ] Backend API uptime monitoring (UptimeRobot, Pingdom)
- [ ] Error tracking configured (Sentry, optional)
- [ ] Log aggregation set up (optional)

### Cost Monitoring
- [ ] RunPod billing alerts configured
- [ ] AWS S3 billing alerts set
- [ ] Database cost tracked
- [ ] Total monthly cost estimated: $___________

## Security Checklist

- [ ] All environment variables stored securely
- [ ] JWT secret key is strong (32+ characters)
- [ ] Database uses SSL connection
- [ ] S3 bucket has proper permissions
- [ ] API rate limiting configured
- [ ] CORS properly restricted
- [ ] No sensitive data in git repository
- [ ] .env files in .gitignore

## Performance Optimization

- [ ] Database indexed properly
- [ ] S3 CDN configured (CloudFront, optional)
- [ ] Frontend assets optimized
- [ ] Gzip compression enabled
- [ ] RunPod cold start time acceptable (<60s)

## Documentation

- [ ] API documentation accessible
- [ ] User guide created
- [ ] Admin documentation written
- [ ] Deployment process documented
- [ ] Troubleshooting guide available

## Rollback Plan

If deployment fails:

1. **Frontend**: Revert to previous Netlify deployment
   - Go to Netlify → Deploys → Click previous successful deploy → "Publish deploy"

2. **Backend API**: Roll back to previous version
   - Railway/Render: Use their rollback feature
   - Manual: `git checkout <previous-commit>` and redeploy

3. **RunPod Endpoint**: Cannot rollback easily
   - Keep previous Docker image tag
   - Create new endpoint with old image if needed

- [ ] Rollback procedure tested
- [ ] Previous versions tagged in git
- [ ] Backup database available

## Support Contacts

- **RunPod Support**: https://www.runpod.io/support
- **Netlify Support**: https://www.netlify.com/support
- **Railway Support**: https://railway.app/help
- **Your Team**: __________________

## Deployment Timeline

Estimated time for complete deployment:

| Task | Estimated Time |
|------|---------------|
| RunPod endpoint build | 30-45 minutes |
| Backend API deployment | 10-15 minutes |
| Frontend deployment | 5-10 minutes |
| Testing & verification | 15-20 minutes |
| **Total** | **60-90 minutes** |

## Cost Estimate (Monthly)

| Service | Cost |
|---------|------|
| RunPod Serverless (CPU) | $50-100 |
| PostgreSQL Database | $20-50 |
| AWS S3 Storage | $10-50 |
| Backend API Hosting | $7-20 |
| External APIs (Ivrit, DeepSeek) | $50-200 |
| **Total Estimated** | **$137-420/month** |

## Success Criteria

Deployment is successful when:

- ✅ All services are running and accessible
- ✅ Frontend can communicate with backend
- ✅ Backend can communicate with RunPod endpoint
- ✅ Database connections working
- ✅ S3 storage accessible
- ✅ End-to-end meeting processing works
- ✅ No critical errors in logs
- ✅ Performance metrics acceptable
- ✅ All tests passing

---

## Quick Reference URLs

After deployment, document your URLs here:

- **Frontend (Netlify)**: _______________________________
- **Backend API**: _______________________________
- **RunPod Endpoint**: _______________________________
- **Database**: _______________________________
- **S3 Bucket**: _______________________________

---

**Deployment Date**: _______________
**Deployed By**: _______________
**Version**: _______________