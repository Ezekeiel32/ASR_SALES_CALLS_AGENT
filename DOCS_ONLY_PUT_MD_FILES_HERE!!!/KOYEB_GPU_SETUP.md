# Koyeb GPU Deployment - RTX-4000 Setup

## ✅ Current Configuration

You're deploying with:
- **Instance**: RTX-4000-SFF-ADA (6 vCPU, 44GB RAM, GPU)
- **Region**: Europe
- **Builder**: Switch to **Docker** (not Buildpack)
- **Cost**: Free during Pro trial, then $0.50/hr ($375/mo)

## 🚀 Deployment Steps

### 1. Switch Builder to Docker
In the Koyeb dashboard, change from "Buildpack" to **"Docker"** so it uses your `Dockerfile`.

### 2. Create PostgreSQL & Redis First!

**Create these BEFORE adding environment variables:**

1. **PostgreSQL**: Databases → Create Database → PostgreSQL → Copy connection string
2. **Redis**: Databases → Create Database → Redis → Copy connection string

### 3. Environment Variables (After Creating Databases)

Go to "Environment variables" section and add:

```bash
# Database (from Koyeb PostgreSQL you just created)
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis (from Koyeb Redis you just created)
REDIS_URL=redis://host:port

# CORS (for Netlify frontend)
CORS_ORIGINS=https://ivreetmeet.netlify.app

# API Keys
IVRIT_API_KEY=your_ivrit_key
NVIDIA_API_KEY=your_nvidia_key
RUNPOD_API_KEY=your_runpod_key
IVRIT_RUNPOD_ENDPOINT_ID=your_endpoint_id

# PyAnnote (required for GPU diarization)
PYANNOTE_AUTH_TOKEN=your_huggingface_token

# S3 (optional but recommended - for model storage)
S3_BUCKET=your-bucket-name
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# GPU Settings (PyTorch will auto-detect CUDA)
CUDA_VISIBLE_DEVICES=0

# Port (Koyeb sets this, but we have fallback)
PORT=8000
```

### 3. Create PostgreSQL & Redis in Koyeb (Do This First!)

**Before deploying your app:**

1. **Create PostgreSQL in Koyeb:**
   - Go to "Databases" → "Create Database"
   - Select **PostgreSQL**
   - Choose plan (start with free/cheapest)
   - Wait for it to provision
   - Go to database settings → Copy the **Connection String** or **DATABASE_URL**
   - It looks like: `postgresql://user:password@host:port/dbname`

2. **Create Redis in Koyeb:**
   - Go to "Databases" → "Create Database"  
   - Select **Redis**
   - Choose plan
   - Copy the **REDIS_URL** connection string

3. **Add to Environment Variables:**
   - In your app deployment, add:
     - `DATABASE_URL=<the_postgres_url_you_copied>`
     - `REDIS_URL=<the_redis_url_you_copied>`

### 4. Health Check Configuration

Your health check is already set to port 8000 ✅

But for better monitoring, change it to:
- **Type**: HTTP
- **Path**: `/healthz`
- **Port**: 8000

### 5. Deploy!

Click "Deploy" - Koyeb will:
1. Build Docker image with CUDA support
2. Deploy to GPU instance
3. Run migrations automatically (if configured)
4. Start the FastAPI server

## 🔥 GPU Performance Expectations

With RTX-4000 GPU:

**PyAnnote Diarization:**
- 30min audio: ~5-10 seconds (vs 30-60s on CPU)
- 1hr audio: ~10-20 seconds (vs 1-2min on CPU)

**SpeechBrain Voiceprints:**
- Already fast on CPU (~1-2s per snippet)
- GPU: ~0.5-1s per snippet (minor improvement)

**Overall Pipeline:**
- Full meeting processing: 2-5x faster than CPU

## 📊 Resource Usage

**Memory:**
- PyTorch + models: ~2-4GB
- FastAPI + Celery: ~500MB
- System: ~2GB
- **Total**: ~6-8GB (plenty of headroom with 44GB!)

**GPU:**
- PyAnnote will use GPU for inference
- SpeechBrain may use CPU (already fast enough)

## ⚠️ Important Notes

### After Free Trial Ends:
- **Cost**: $0.50/hour = $375/month if running 24/7
- **Recommendation**: Use autoscaling (0-1 instances)
  - Scales to 0 when idle = $0
  - Only pays when processing meetings
  - Check your usage in Koyeb dashboard

### Model Downloads:
- First time: Models download from HuggingFace (~1GB total)
- Subsequent: Faster if using S3 for model storage
- GPU drivers: Already included in Koyeb GPU instances

### Monitoring:
- Check Koyeb logs to see GPU usage
- Watch for CUDA errors (shouldn't happen, but monitor)
- Track processing times to see GPU speedup

## 🐛 Troubleshooting

### Models Not Using GPU:
- Check logs for "CUDA available: True"
- Verify `torch.cuda.is_available()` returns True
- PyAnnote auto-detects GPU via `device="cuda"`

### Out of Memory:
- Unlikely with 44GB RAM
- But if happens: Reduce batch size in PyAnnote config

### Build Fails:
- Make sure builder is "Docker" not "Buildpack"
- Check Dockerfile is in repo root ✅

## ✅ Post-Deployment Checklist

1. ✅ Test health endpoint: `curl https://your-app.koyeb.app/healthz`
2. ✅ Check logs for "CUDA available: True"
3. ✅ Run a test meeting upload
4. ✅ Verify GPU is being used (check processing times)
5. ✅ Set up autoscaling to 0-1 instances

## 💡 Cost Optimization After Trial

Once trial ends, consider:
- **Autoscaling 0-1**: Only pay when processing
- **Or downgrade**: Switch to CPU instance if GPU not needed
- **Or hybrid**: Use GPU for PyAnnote, CPU for everything else

---

**You're all set!** Click deploy and enjoy the GPU power during your free week! 🚀

