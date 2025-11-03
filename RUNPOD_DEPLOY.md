# RunPod Deployment Guide - Cheaper & Better Than Koyeb! 🚀

## 🎯 Why RunPod?

**Koyeb Issues:**
- ❌ Expensive ($0.50/hr = $375/month)
- ❌ Annoying sleep/start behavior
- ❌ Limited auto-scaling flexibility
- ❌ Complex service management

**RunPod Advantages:**
- ✅ Cheaper: RTX 4000 at $0.29/hr (42% savings!)
- ✅ Better reliability
- ✅ True pay-per-use (scale to 0 = $0)
- ✅ Simple pod management
- ✅ Better GPU availability
- ✅ Great documentation

## 💰 Cost Comparison

**RunPod Pricing (RTX 4000):**
- GPU: RTX 4000 Ada (similar to Koyeb)
- VRAM: 30GB
- CPU: 8 vCPU
- RAM: 30GB
- **Cost: $0.29/hour**

**Monthly Cost Examples:**
- 10 hours/month processing: **$2.90/month** 🎉
- 50 hours/month processing: **$14.50/month** 🎉
- 100 hours/month processing: **$29/month** 🎉

**vs Koyeb:**
- Koyeb: $0.50/hr = $50/month for 100 hours
- **RunPod saves: $21/month (42% cheaper!)** 💰

## 🏗️ Recommended Architecture

### Option 1: Hybrid (Best Balance) ⭐ RECOMMENDED

**API Service: Render (Free)**
- Handles HTTP requests (login, upload, list meetings)
- Always-on, fast responses
- **Cost: $0/month** ✅

**Worker Service: RunPod GPU**
- Processes meetings with GPU
- Auto-scales to 0 when idle
- **Cost: $0.29/hr only when processing** ✅

**Total: ~$15-30/month** (vs $375/month with Koyeb!)

### Option 2: Full RunPod (If You Want Everything There)

**API Service: RunPod CPU Pod**
- Standard CPU instance
- Always-on for API
- Cost: ~$0.05-0.10/hr = ~$40-75/month

**Worker Service: RunPod GPU Pod**
- GPU for ML processing
- Auto-scaling
- Cost: $0.29/hr when processing

**Total: ~$55-100/month**

## 🚀 Deployment Steps

### Step 1: Set Up RunPod Account

1. Go to https://www.runpod.io/
2. Sign up (free account)
3. Add payment method (only charged when pods run)
4. Get $10 free credit to start! 🎉

### Step 2: Create API Service (Render - Free)

Since API doesn't need GPU, use Render for free:

1. Go to https://render.com
2. Connect GitHub repo
3. **New Web Service**:
   - Name: `ivrimeet-api`
   - Environment: `Docker`
   - Region: Choose closest to you
   - Branch: `main`
   - Root Directory: `/` (or leave empty)
   - Dockerfile Path: `Dockerfile`
   - Docker Command: (leave empty, uses Dockerfile CMD)
4. **Environment Variables**:
   ```bash
   DATABASE_URL=your_supabase_postgres_url
   REDIS_URL=your_upstash_redis_url
   CORS_ORIGINS=https://ivreetmeet.netlify.app
   IVRIT_API_KEY=your_key
   NVIDIA_API_KEY=your_key
   PYANNOTE_AUTH_TOKEN=your_hf_token
   JWT_SECRET_KEY=your_jwt_secret
   PORT=8000
   PYTHONUNBUFFERED=1
   ```
5. **Scaling**: Always-on (free tier)
6. Click **Create Web Service**

**Your API URL**: `https://ivrimeet-api.onrender.com` (or custom domain)

### Step 3: Create Worker Service (RunPod GPU)

#### 3.1 Create GPU Pod Template

1. Go to RunPod Dashboard → **Pods** → **Templates**
2. Click **Create Template**
3. **Basic Info**:
   - Name: `ivrimeet-worker`
   - Container Image: `python:3.12-slim` (we'll use custom Dockerfile)
4. **GPU**: 
   - Select: RTX 4000 Ada (or RTX 3090 for cheaper option)
   - VRAM: 30GB
5. **Container Config**:
   - **Docker Command**: (we'll override with custom image)
   - **Container Disk**: 20GB (for models)
6. **Network**:
   - Expose HTTP Port: (leave empty, worker doesn't need HTTP)
7. **Environment Variables**:
   ```bash
   DATABASE_URL=your_supabase_postgres_url
   REDIS_URL=your_upstash_redis_url
   IVRIT_API_KEY=your_key
   NVIDIA_API_KEY=your_key
   PYANNOTE_AUTH_TOKEN=your_hf_token
   S3_BUCKET=your_bucket
   S3_REGION=us-east-1
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   PYTHONUNBUFFERED=1
   PYTHONPATH=/app
   CELERY_BROKER_URL=your_redis_url
   CELERY_RESULT_BACKEND=your_redis_url
   ```
8. **Save Template**

#### 3.2 Build and Push Docker Image

RunPod can build from Dockerfile or use pre-built image. Two options:

**Option A: Build on RunPod (Easier)**

1. Go to **Pods** → **Create Pod**
2. Select your template
3. **Build from Dockerfile**:
   - Dockerfile: `Dockerfile.worker`
   - Build Context: (your GitHub repo URL or Docker Hub image)
4. Click **Deploy**

**Option B: Push to Docker Hub (More Control)**

```bash
# Build locally
cd /home/chezy/ASR/ASR_SALES_CALLS_AGENT
docker build -f Dockerfile.worker -t ivrimeet-worker:latest .

# Tag for Docker Hub
docker tag ivrimeet-worker:latest yourusername/ivrimeet-worker:latest

# Push to Docker Hub
docker push yourusername/ivrimeet-worker:latest
```

Then in RunPod:
- **Container Image**: `yourusername/ivrimeet-worker:latest`

#### 3.3 Create Pod with Auto-Scaling

1. **Pods** → **Create Pod**
2. **Template**: Select `ivrimeet-worker`
3. **Instance Type**: RTX 4000 Ada ($0.29/hr)
4. **Auto-Scaling**:
   - **Min Instances**: 0 ← Scale to 0 when idle!
   - **Max Instances**: 2
   - **Scale Up**: When Redis queue has tasks
   - **Scale Down**: After 5 minutes idle
5. **Network Volume**: (optional, for persistent model cache)
6. Click **Deploy Pod**

**Pod will:**
- Start when Celery task arrives in Redis queue
- Process meeting
- Scale down to 0 after 5-10 min idle
- **Cost: Only pay when processing!** 💰

### Step 4: Configure Celery to Trigger RunPod (Optional)

RunPod has webhooks/API to trigger pods. For auto-scaling based on queue:

**Option A: Simple (Manual Check)**
- Worker pod stays at min: 0
- When task arrives, manually start pod (or use cron)

**Option B: Advanced (Auto-Scale via API)**
- Use RunPod API to start/stop pods
- Check Redis queue length
- Start pod when queue > 0
- Stop pod when queue = 0 and idle > 5min

I can create a small service for this if needed!

### Step 5: Update Frontend

Update Netlify environment variable:

```bash
VITE_API_BASE_URL=https://ivrimeet-api.onrender.com
```

## 📋 RunPod Setup Checklist

- [ ] Create RunPod account ($10 free credit!)
- [ ] Create API service on Render (free)
- [ ] Create worker template in RunPod
- [ ] Build/push Docker image (Dockerfile.worker)
- [ ] Deploy GPU pod with auto-scaling (min: 0)
- [ ] Set all environment variables
- [ ] Test: Upload meeting → Check pod starts → Verify processing
- [ ] Update frontend API URL
- [ ] Monitor costs in RunPod dashboard

## 🔧 RunPod Pod Configuration

### Worker Pod Command

The pod needs to run Celery worker. In your RunPod template or pod settings:

**Start Command**:
```bash
celery -A agent_service.services.processing_queue.celery_app worker --loglevel=info --concurrency=2
```

Or use the CMD from `Dockerfile.worker` (already set!).

### Health Check (Optional)

RunPod can monitor pod health. For worker pods, you might want a simple HTTP endpoint:

Create `worker_health.py`:
```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "type": "worker"}
```

Then expose port 8001 in RunPod pod config.

## 💡 Pro Tips

### 1. Use RunPod Network Volumes

Store models in network volume (persistent across pod restarts):
- Faster startup (models already downloaded)
- Persistent cache
- Cost: ~$0.10/GB/month

### 2. Monitor Costs

RunPod dashboard shows:
- Current running pods
- Hourly cost
- Monthly estimate
- Set budget alerts!

### 3. Scale Settings

**Conservative** (Save Money):
- Min: 0, Max: 1
- Scale down: 5 min idle

**Aggressive** (Faster):
- Min: 0, Max: 3
- Scale down: 10 min idle

### 4. Multiple GPU Options

If RTX 4000 is busy, try:
- **RTX 3090**: $0.24/hr (cheaper!)
- **RTX A4000**: $0.29/hr (similar performance)
- **A5000**: $0.49/hr (if you need more VRAM)

## 🆚 RunPod vs Koyeb

| Feature | Koyeb | RunPod |
|---------|-------|--------|
| **GPU Cost** | $0.50/hr | $0.29/hr ✅ |
| **Auto-Scale** | Limited | Better ✅ |
| **Reliability** | Issues with sleep | More stable ✅ |
| **Setup** | Easier (PaaS) | Medium (IaaS) |
| **Free Trial** | 7 days Pro | $10 credit ✅ |
| **Documentation** | Good | Excellent ✅ |

## 🎯 Expected Results

**Cost Savings:**
- Current Koyeb: $375/month (24/7) or $150/month (scaled)
- RunPod: $15-30/month (50-100 hours processing)
- **Savings: 80-95%!** 🎉

**Performance:**
- Same GPU speed (5-10s diarization) ✅
- Better reliability ✅
- Faster pod startup ✅

## 🚨 Troubleshooting

### Pod Won't Start
- Check Docker image is accessible
- Verify environment variables
- Check RunPod logs

### Celery Not Connecting
- Verify `REDIS_URL` is correct
- Check Redis is accessible from RunPod
- Test Redis connection in pod shell

### Models Not Loading
- Check HuggingFace token
- Verify S3 credentials (if using S3)
- Check disk space in pod

## 📞 Need Help?

Want me to:
1. ✅ Create RunPod deployment scripts?
2. ✅ Set up auto-scaling service?
3. ✅ Migrate your current setup step-by-step?

Just ask! RunPod is definitely the better choice - cheaper, more reliable, and you have more control. 🚀

