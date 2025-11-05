# RunPod Serverless Quick Deployment Guide

**Fast track to deployment without local Docker build**

## Option 1: Deploy via RunPod Web Console (Recommended - No Local Build)

### Step 1: Create RunPod Account & Add Credits
1. Go to https://www.runpod.io
2. Sign up or log in
3. Add credits to your account ($10 minimum recommended)

### Step 2: Create Docker Image via RunPod Builder

RunPod can build the image directly. You have two options:

#### Option A: Use GitHub Repository
1. Push this repository to GitHub
2. In RunPod Console: Settings > Repositories
3. Connect your GitHub account
4. Select this repository

#### Option B: Docker Build Instructions for Deployment
If you prefer to build locally with more time:

```bash
cd ASR_SALES_CALLS_AGENT

# Build with increased timeout (20 minutes)
docker buildx build --progress=plain \
  -f Dockerfile.runpod_serverless \
  -t ivrimeet-runpod:latest \
  --load \
  .

# Tag and push to Docker Hub
docker tag ivrimeet-runpod:latest YOUR_DOCKERHUB_USERNAME/ivrimeet-runpod:latest
docker push YOUR_DOCKERHUB_USERNAME/ivrimeet-runpod:latest
```

### Step 3: Create RunPod Template

1. Go to https://www.runpod.io/console/serverless
2. Click **"New Template"**
3. Configure:
   - **Name**: `ivrimeet-handler`
   - **Docker Image**: `docker.io/YOUR_USERNAME/ivrimeet-runpod:latest`
   - **Container Disk**: 50 GB
   - **Volume Disk**: 100 GB
   - **GPU**: None (CPU mode recommended)
   - **Minimum Instances**: 0
   - **Max Instances**: 3

### Step 4: Set Environment Variables in Template

Add these in RunPod Template > Environment Variables:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/ivrimeet_db

# AWS S3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET=your-bucket-name
S3_REGION=us-east-1

# APIs
IVRIT_API_KEY=your_ivrit_key
IVRIT_API_URL=https://api.ivrit.ai
LLM_API_KEY=your_deepseek_key
LLM_MODEL=deepseek-ai/deepseek-v3.1-terminus

# Platform
USE_RUNPOD=true
BACKEND_URL=https://your-backend.example.com
```

### Step 5: Create Endpoint

1. Save the template
2. Click **"Create Endpoint"**
3. Select the template
4. Choose deployment region (e.g., US-EU)
5. Click **"Deploy"**
6. **Note the Endpoint ID** (format: `ep-xxxxx...`)

### Step 6: Get API Key

1. Go to RunPod Console > Settings > API Keys
2. Click **"Create"**
3. Copy the API Key
4. **Save securely**

### Step 7: Configure Backend API

Deploy your FastAPI backend with these environment variables:

```bash
# RunPod Configuration
USE_RUNPOD=true
RUNPOD_ENDPOINT_ID=ep-xxxxx...
RUNPOD_API_KEY=your_api_key

# All other variables from .env.example
```

**Deployment Hosts (pick one):**
- [Render.com](https://render.com) - Free tier available
- [Railway.app](https://railway.app) - Pay-as-you-go
- [Fly.io](https://fly.io) - Distributed deployment
- [AWS Lambda](https://aws.amazon.com/lambda/)
- [Google Cloud Run](https://cloud.google.com/run)

### Step 8: Test Deployment

```bash
# Set environment variables locally
export RUNPOD_ENDPOINT_ID=ep-xxxxx
export RUNPOD_API_KEY=your_api_key

# Test endpoint
python scripts/runpod_utils.py test-endpoint

# Submit test job
python scripts/runpod_utils.py submit-job \
  --meeting-id $(python -c "import uuid; print(uuid.uuid4())") \
  --organization-id $(python -c "import uuid; print(uuid.uuid4())") \
  --wait
```

### Step 9: Deploy Frontend

```bash
cd IvriMeet
npm install
npm run build

# Deploy to Netlify
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

## Option 2: Build on Your Machine (Alternative)

If you want to build the Docker image locally:

### Increase Docker Memory
```bash
# Ubuntu/Linux
# Edit /etc/docker/daemon.json
{
  "memory": 4000,
  "swap": 4000
}

# Restart Docker
sudo systemctl restart docker

# Or use buildx with memory limit
docker buildx build \
  --memory 4000m \
  --progress=plain \
  -f Dockerfile.runpod_serverless \
  -t ivrimeet-runpod:latest \
  .
```

### Alternative: Build in Stages
```bash
# Build only dependencies layer
docker build --target dependencies \
  -f Dockerfile.runpod_serverless \
  -t ivrimeet-deps:latest \
  .

# Then build full image
docker build \
  -f Dockerfile.runpod_serverless \
  -t ivrimeet-runpod:latest \
  .
```

## Option 3: Use Pre-Built Container

Contact support or use existing base images with dependencies already installed:

```dockerfile
# Use PyTorch official image with system dependencies
FROM pytorch/pytorch:2.1.0-cuda12.1-runtime-ubuntu22.04
```

## Monitoring Your Deployment

### Check Endpoint Status
- RunPod Console > Endpoints
- Green status = Ready
- Red status = Issue (check logs)

### View Logs
1. Click endpoint name
2. View "Activity" tab
3. Check pod logs for errors

### Common Startup Messages (Normal)
```
Loading models...
Initializing database connection...
Handler ready for requests
```

### Common Errors & Fixes

| Error | Solution |
|-------|----------|
| `No module named 'torch'` | Ensure Dockerfile.runpod_serverless is being used |
| `Connection timeout - database` | Verify DATABASE_URL is accessible, whitelist RunPod IPs |
| `Access Denied - S3 bucket` | Check AWS credentials and S3 bucket permissions |
| `Cold start timeout` | First request can take 30-60 seconds - normal |

## Pricing Reference

```bash
CPU Endpoints (Recommended):
- 2vCPU, 8GB RAM:   ~$0.01-0.02/hour (idle)
- 4vCPU, 16GB RAM:  ~$0.05-0.10/hour (running)
- Pay per second, no minimum

GPU Endpoints (Optional):
- RTX 4090:         ~$0.60-1.00/hour
- L40:              ~$0.40-0.60/hour
```

## Testing the Full Flow

### 1. Upload Audio via API
```bash
curl -X POST https://your-backend.example.com/meetings/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@test_audio.mp3" \
  -F "title=Test Meeting"
```

### 2. Check Processing Status
```bash
curl -X GET https://your-backend.example.com/meetings/MEETING_UUID \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. View Results
```bash
curl -X GET https://your-backend.example.com/meetings/MEETING_UUID/transcript \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Deployment Checklist

- [ ] Account created on RunPod
- [ ] Credits added ($10+)
- [ ] Docker image ready
- [ ] RunPod template created
- [ ] Endpoint deployed and running
- [ ] API key generated
- [ ] Backend API deployed
- [ ] Environment variables set
- [ ] Frontend deployed to Netlify
- [ ] Test upload successful
- [ ] Meeting processed successfully
- [ ] Results visible in UI

## Next Steps

1. **Immediate**: Sign up for RunPod
2. **Within 5 minutes**: Create template and endpoint
3. **Within 30 minutes**: Deploy backend API
4. **Within 1 hour**: Deploy frontend
5. **Test**: Upload a meeting and verify

## Support

- RunPod Docs: https://docs.runpod.io/
- Full Guide: See `RUNPOD_DEPLOYMENT_GUIDE.md`
- Issues: Check `RUNPOD_SETUP_SUMMARY.md` troubleshooting

## Success Criteria

✅ You'll know it's working when:
- RunPod endpoint shows green status
- Backend API returns 200 on `/healthz`
- Frontend loads without CORS errors
- Sample meeting uploads successfully
- Processing completes within 5 minutes
- Results display in UI

That's it! You're now running on RunPod Serverless 🚀
