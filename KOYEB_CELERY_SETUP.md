# Setting Up Celery Worker on Koyeb

## 🎯 Problem
Your `koyeb.yaml` was missing the Celery worker service, so uploaded meetings were queued but never processed.

## ✅ Solution
The `koyeb.yaml` has been updated to include a worker service. However, **Koyeb requires you to create the worker service manually** in the dashboard.

## 📋 Steps to Set Up Celery Worker

### Option 1: Using koyeb.yaml (Automatic)
If you redeploy from GitHub, Koyeb should detect both services:
- `api` - FastAPI web server
- `worker` - Celery worker

### Option 2: Manual Setup in Koyeb Dashboard

1. **Go to Koyeb Dashboard** → Your App → "Services"

2. **Create New Service:**
   - Click "Create Service"
   - Select same GitHub repository
   - Same branch (main)

3. **Configuration:**
   - **Name**: `worker` (or `ivrimeet-worker`)
   - **Type**: `Worker` (not Web)
   - **Dockerfile**: Use existing `Dockerfile`

4. **Start Command:**
   ```
   celery -A agent_service.services.processing_queue.celery_app worker --loglevel=info --concurrency=2
   ```

5. **Environment Variables:**
   - Copy ALL environment variables from your API service:
     - `DATABASE_URL`
     - `REDIS_URL` ⚠️ **CRITICAL - Must be same Redis!**
     - `IVRIT_API_KEY`
     - `NVIDIA_API_KEY`
     - `PYANNOTE_AUTH_TOKEN`
     - `S3_BUCKET` (if using S3)
     - `AWS_ACCESS_KEY_ID`
     - `AWS_SECRET_ACCESS_KEY`
     - All other API keys

6. **Scaling:**
   - Min: 1 (worker must always be running to process tasks)
   - Max: 2 (can scale up for heavy processing)

7. **No Port Needed:**
   - Worker doesn't need HTTP port
   - No health check needed

## 🔍 Verify Worker is Running

1. **Check Logs:**
   - Go to worker service → "Logs"
   - You should see:
     ```
     celery@... ready.
     ```

2. **Test Processing:**
   - Upload a meeting file
   - Check worker logs for:
     ```
     [INFO] Enqueued meeting ... for processing
     [INFO] Processing meeting ...
     ```

3. **Check Redis Connection:**
   - If you see "Connection refused" errors:
     - Verify `REDIS_URL` is correct
     - Make sure Redis is accessible from worker
     - Check Redis credentials match

## 🐛 Troubleshooting

### Worker Not Processing Tasks

**Check:**
1. Is worker service running? (should show "Running" in dashboard)
2. Are both services using same `REDIS_URL`?
3. Check worker logs for errors

**Common Issues:**

**"No module named 'celery'"**
- Dockerfile might not be installing dependencies
- Check build logs

**"Connection refused" to Redis**
- Verify `REDIS_URL` format: `redis://host:port` or `redis://user:pass@host:port`
- For Upstash Redis: `redis://default:token@host:port`
- Make sure Redis is accessible from Koyeb

**"Database connection error"**
- Worker needs `DATABASE_URL` same as API
- Verify PostgreSQL is accessible

**Tasks queued but not processed**
- Worker service might not be running
- Check scaling settings (min should be ≥ 1)
- Verify Redis connection in worker logs

### Worker Keeps Crashing

**Check logs for:**
- Memory issues (if models too large)
- Missing environment variables
- Database connection failures

**Solutions:**
- Increase worker memory limit
- Add missing env vars
- Verify database connection string

## 📊 Resource Requirements

**Worker Memory:**
- Base: ~200MB
- PyAnnote models: +1-2GB
- SpeechBrain: +500MB
- **Total**: ~2-3GB minimum

**Recommendation:**
- Use at least 4GB RAM for worker
- GPU instance has 44GB (plenty!)

## ✅ Checklist

- [ ] Worker service created in Koyeb
- [ ] Same `REDIS_URL` as API service
- [ ] All environment variables copied
- [ ] Worker shows "Running" status
- [ ] Logs show "celery@... ready"
- [ ] Test upload processes successfully

## 🚀 After Setup

Once worker is running:
1. Upload a test meeting
2. Check API logs: Should see "Enqueued meeting..."
3. Check worker logs: Should see "Processing meeting..."
4. Wait for processing to complete
5. Check meeting status in dashboard

Your meetings will now be processed automatically! 🎉

