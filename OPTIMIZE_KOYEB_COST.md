# Optimize Koyeb Costs - Split API & Worker

## 💰 Current Situation

**Current Setup:**
- API + Worker both on GPU instance
- Cost: $375/month (24/7) or ~$150/month (with scaling)
- ❌ Paying for GPU even when just handling HTTP requests

## ✅ Solution: Split Services

### Architecture Change

**Before:**
```
GPU Instance (RTX-4000)
├── API Service (FastAPI)     ← Doesn't need GPU!
└── Worker Service (Celery)   ← Needs GPU for ML
Cost: $375/month (24/7)
```

**After:**
```
Standard CPU Instance
└── API Service (FastAPI)      ← Handles HTTP requests
    Cost: ~$15-30/month (24/7)

GPU Instance (RTX-4000) [Auto-scaling]
└── Worker Service (Celery)    ← Only runs when processing
    Cost: $0/hr idle, $0.50/hr active
    Estimated: $25-100/month
```

**Total Cost: $40-130/month** (85% savings!) 🎉

## 🚀 Implementation Steps

### Step 1: Create Separate Services in Koyeb

#### 1.1 API Service (Standard CPU)

1. Go to Koyeb Dashboard
2. **New Service** → Connect GitHub
3. **Service Type**: Web Service
4. **Instance Type**: Standard (NOT GPU)
   - Choose: `Standard-1X` or `Standard-2X`
   - Cost: ~$15-30/month
5. **Dockerfile**: Use your existing `Dockerfile`
6. **Environment Variables**: Copy all from current setup
7. **Scaling**: `min: 1, max: 1` (always-on)

**This handles:**
- `/healthz` health checks
- `/auth/login`, `/auth/register`
- `/meetings/list`, `/meetings/{id}`
- Upload endpoints (just enqueues to Celery)

**No GPU needed!** FastAPI responds in milliseconds.

#### 1.2 Worker Service (GPU with Auto-Scaling)

1. **New Service** → Same GitHub repo
2. **Service Type**: Worker Service
3. **Instance Type**: GPU → RTX-4000
4. **Dockerfile**: Use `Dockerfile.worker`
5. **Environment Variables**: Same as API service
6. **Scaling**: 
   - `min: 0` ← Scale to 0 when idle!
   - `max: 2` ← Scale up when queue has tasks

**This handles:**
- Celery worker tasks
- PyAnnote diarization (needs GPU)
- SpeechBrain voiceprints (needs GPU)
- Meeting processing

**Auto-scales:**
- Idle = 0 instances = $0/hour ✅
- Processing = 1-2 instances = $0.50/hour each

### Step 2: Update CELERY_BROKER_URL

Both services need to use the **same Redis URL**:

```bash
REDIS_URL=your_upstash_redis_url  # Same for both services!
```

This ensures the API can enqueue tasks and the Worker can process them.

### Step 3: Update Frontend API URL

In Netlify, update `VITE_API_BASE_URL` to point to your new **API service URL**:
- Old: `https://alleged-steffie-zpe-e3243604.koyeb.app`
- New: `https://your-new-api-service.koyeb.app`

### Step 4: Test the Setup

1. **Upload a meeting** from frontend
2. **Check API logs**: Should see "Enqueued meeting for processing"
3. **Check Worker logs**: Should see "Worker scaled up" → "Processing meeting"
4. **Verify**: Meeting processes successfully
5. **Wait 5 minutes**: Worker should scale down to 0

## 📊 Cost Estimation

### Scenario 1: Light Usage (10 hours/month processing)

- API (CPU): $20/month (always-on)
- Worker (GPU): 10 hours × $0.50 = $5/month
- **Total: $25/month** 💰

### Scenario 2: Medium Usage (50 hours/month processing)

- API (CPU): $20/month (always-on)
- Worker (GPU): 50 hours × $0.50 = $25/month
- **Total: $45/month** 💰

### Scenario 3: Heavy Usage (150 hours/month processing)

- API (CPU): $30/month (might need 2X instance)
- Worker (GPU): 150 hours × $0.50 = $75/month
- **Total: $105/month** 💰

**vs Current $375/month** = **70-85% savings!** 🎉

## 🎯 Performance

**API Response Times:**
- Health check: < 50ms ✅
- Login/Register: < 200ms ✅
- List meetings: < 500ms ✅
- Upload (enqueue): < 1s ✅

**Processing Times (same as current):**
- 30min audio: 5-10s diarization ✅
- 1hr audio: 10-20s diarization ✅
- Full pipeline: Same speed! ✅

## ⚠️ Important Notes

### Auto-Scaling Behavior

**Worker Scale Up:**
- When task arrives in Redis queue
- Koyeb detects queue has tasks
- Scales from 0 → 1 (takes ~30-60s to start)
- Starts processing immediately

**Worker Scale Down:**
- After queue is empty for 5-10 minutes
- Scales from 1 → 0
- Next task will trigger scale-up again

**Cold Start:**
- First request after idle: ~30-60s delay
- Subsequent requests: Instant
- Acceptable for async processing (user already uploaded)

### Keep Worker Warm (Optional)

If you want to avoid cold starts:

1. **Keepalive ping to worker** (every 4 min)
2. **Set `min: 1`** (always 1 instance running)
3. **Cost**: Adds $0.50/hr = $360/month when idle
4. **Recommendation**: Only if processing constantly

## ✅ Checklist

- [ ] Create API service (Standard CPU instance)
- [ ] Create Worker service (GPU instance, auto-scale)
- [ ] Both services use same `REDIS_URL`
- [ ] Update frontend `VITE_API_BASE_URL`
- [ ] Test upload → processing → completion
- [ ] Verify worker scales to 0 after idle
- [ ] Monitor costs in Koyeb dashboard

## 🚀 Alternative: Even Cheaper with RunPod

If you want to go even cheaper:

**RunPod GPU:**
- RTX 4000: $0.29/hour (vs Koyeb $0.50/hour)
- Same performance
- **50 hours/month = $14.50** (vs Koyeb $25)

**Setup:**
- API: Render free tier ($0)
- Worker: RunPod GPU ($0.29/hr)
- **Total: ~$15/month** for processing 🎉

But requires more setup (RunPod API integration).

---

**Recommendation**: Start with Koyeb split (easier, already set up), then consider RunPod if costs are still high.

