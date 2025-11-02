# Fixing Koyeb Worker Instance Keeps Stopping

## 🚨 Problem: Instance Keeps Stopping

Your Celery worker service keeps crashing/stopping. Common causes and solutions below.

## 🔍 Common Causes

### 1. **Health Check Failure** (Most Likely)
**Problem:** The main `Dockerfile` has a HEALTHCHECK that expects port 8000, but workers don't expose HTTP ports.

**Solution:** ✅ Created `Dockerfile.worker` without health check
- Updated `koyeb.yaml` to use `Dockerfile.worker` for worker service

### 2. **Missing Environment Variables**
**Problem:** Worker crashes on startup if required env vars are missing.

**Check:**
- `REDIS_URL` - **CRITICAL** - Must be set
- `DATABASE_URL` - Required for processing
- All API keys (IVRIT_API_KEY, NVIDIA_API_KEY, etc.)

**Solution:** Copy ALL environment variables from API service to worker service

### 3. **Redis Connection Failure**
**Problem:** Worker can't connect to Redis, crashes immediately.

**Check Logs For:**
```
Connection refused
Cannot connect to redis
Redis connection error
```

**Solutions:**
- Verify `REDIS_URL` is correct in worker service
- Check Redis is accessible (same Redis as API service)
- For `rediss://` URLs, SSL is now auto-configured ✅

### 4. **Import Errors**
**Problem:** Python modules fail to import, worker crashes.

**Check Logs For:**
```
ModuleNotFoundError
ImportError
No module named 'X'
```

**Solution:**
- Verify all dependencies in `requirements.txt` are installed
- Check Dockerfile builds successfully
- Review build logs for missing packages

### 5. **Memory Limit Exceeded**
**Problem:** Worker runs out of memory loading models.

**Check Logs For:**
```
Out of memory
Killed
MemoryError
```

**Solutions:**
- Increase worker instance size in Koyeb
- Use S3 for model storage (already configured)
- Reduce `--concurrency` (currently 2, try 1)

### 6. **Auto-Scaling to Zero**
**Problem:** Koyeb scales worker to 0 when idle.

**Solution:**
- Set scaling minimum to **1** (should already be set in koyeb.yaml)
- Go to service → Scaling → Set min: 1, max: 2

## ✅ What I Fixed

1. **Created `Dockerfile.worker`:**
   - No health check (workers don't need HTTP endpoints)
   - No port exposure
   - Optimized for worker processes only

2. **Updated `koyeb.yaml`:**
   - Worker service now uses `Dockerfile.worker`
   - Removed unnecessary health check config

3. **Improved Error Handling:**
   - Added Redis URL validation
   - Better error messages on startup
   - Retry logic for Redis connections

4. **Worker Stability Settings:**
   - `worker_max_tasks_per_child: 50` - Prevents memory leaks
   - `task_acks_late: True` - Better task handling
   - Time limits to prevent hanging tasks

## 📋 Action Items

### Immediate Steps:

1. **Update Worker Service in Koyeb:**
   - Go to worker service → "Settings" → "Dockerfile"
   - Change from `Dockerfile` to `Dockerfile.worker`
   - Or redeploy from GitHub (will use updated koyeb.yaml)

2. **Verify Environment Variables:**
   - Worker service must have **all** env vars from API service
   - Especially: `REDIS_URL`, `DATABASE_URL`, API keys

3. **Check Scaling:**
   - Minimum instances: **1**
   - Maximum instances: 2 (optional)

4. **Remove Health Check (if manual setup):**
   - Worker service → Settings → Health Check
   - Remove or disable health check

### Verify It's Working:

1. **Check Logs:**
   ```
   celery@... ready.
   [INFO] Detected secure Redis connection (rediss://), configuring SSL...
   [INFO] Celery SSL configuration applied
   ```

2. **Test Upload:**
   - Upload a meeting
   - Check worker logs show: `Processing meeting...`

## 🐛 Debugging Steps

### 1. Check Recent Logs
In Koyeb Dashboard → Worker Service → Logs:
- Look for error messages
- Check what happens right before it stops
- Look for Python tracebacks

### 2. Check Service Events
Koyeb Dashboard → Worker Service → "Events":
- See why service stopped
- Check for resource limits
- Look for crash reports

### 3. Test Locally
```bash
# Test Celery startup
docker build -f Dockerfile.worker -t ivrimeet-worker .
docker run -e REDIS_URL="your_redis_url" -e DATABASE_URL="your_db_url" ivrimeet-worker
```

### 4. Enable Verbose Logging
Temporarily change worker command to:
```bash
celery -A agent_service.services.processing_queue.celery_app worker --loglevel=debug --concurrency=1
```

## 📊 Resource Recommendations

**Minimum for Worker:**
- **Memory**: 2GB (for base + Celery)
- **For ML Models**: 4GB+ (if loading PyAnnote/SpeechBrain locally)
- **With S3**: 2-3GB is fine (models loaded on-demand)

**Current Setup:**
- GPU instance: 44GB RAM ✅ (plenty)
- Free tier: 512MB ❌ (not enough, need to upgrade)

## 💡 Pro Tips

1. **Use S3 for Models:**
   - Models stored in S3, loaded on-demand
   - Reduces worker memory needs
   - Faster startup

2. **Monitor Logs:**
   - Set up alerts in Koyeb for worker crashes
   - Check logs regularly for warnings

3. **Gradual Scaling:**
   - Start with concurrency=1
   - Increase to 2 once stable
   - Monitor memory usage

## ✅ Checklist

- [ ] Updated to use `Dockerfile.worker` (or redeployed from GitHub)
- [ ] All environment variables set in worker service
- [ ] `REDIS_URL` matches API service exactly
- [ ] Scaling min=1 set
- [ ] Health check removed/disabled
- [ ] Logs show "celery@... ready" without errors
- [ ] Test upload processes successfully

---

**After fixing, the worker should stay running!** 🚀

If it still stops, check the logs for the exact error message and share it.

