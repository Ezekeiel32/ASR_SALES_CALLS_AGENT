# RunPod Serverless Deployment Guide

This guide covers deploying the ASR Sales Calls Agent to RunPod Serverless infrastructure.

## Architecture Overview

RunPod Serverless replaces Celery/Redis for asynchronous task processing:
- **API Server**: FastAPI application running on a traditional host (Netlify, Render, Railway, etc.)
- **Processing Service**: RunPod Serverless endpoint for handling `runpod_handler.py`
- **Database**: PostgreSQL with pgvector for speaker embeddings
- **Storage**: AWS S3 for audio files and models

## Prerequisites

1. RunPod Account with API key and Credits
2. AWS Account (S3 bucket for audio/models)
3. PostgreSQL database (RDS or self-hosted)
4. Backend API host (Render, Railway, Koyeb, or similar)
5. Environment variables configured

## Step 1: Prepare RunPod Docker Image

The project includes two Dockerfiles:
- `Dockerfile` - Multi-stage production build
- `Dockerfile.runpod_serverless` - RunPod-optimized build

### Build Docker Image for RunPod

```bash
cd ASR_SALES_CALLS_AGENT

# Build for RunPod
docker build -f Dockerfile.runpod_serverless -t ivrimeet-runpod:latest .

# Tag for RunPod registry
docker tag ivrimeet-runpod:latest <your-runpod-username>/ivrimeet-runpod:latest

# Push to Docker registry (Docker Hub, GitHub Container Registry, etc.)
docker push <your-runpod-username>/ivrimeet-runpod:latest
```

## Step 2: Set Up RunPod Serverless Endpoint

### Via RunPod Web Console

1. Go to https://www.runpod.io/console/serverless
2. Click "Create Template" or use existing template
3. Configure:
   - **Docker Image**: `<your-registry>/ivrimeet-runpod:latest`
   - **Container Disk**: 50GB (for models)
   - **Volume Disk**: 100GB (for processing)
   - **GPU**: None required (CPU-only for faster cold starts)
   - **Environment Variables**: See section below

### Environment Variables for RunPod Endpoint

Configure these in the RunPod Endpoint settings:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@host:5432/ivrimeet_db

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET=your-bucket-name
S3_REGION=us-east-1

# Ivrit ASR Configuration
IVRIT_API_KEY=your_ivrit_key
IVRIT_API_URL=https://api.ivrit.ai

# LLM Configuration
LLM_API_KEY=your_deepseek_key
LLM_MODEL=deepseek-ai/deepseek-v3.1-terminus

# Platform Detection
USE_RUNPOD=true

# Backend URL (for Gmail OAuth redirects)
BACKEND_URL=https://your-api.example.com
RUNPOD_SERVERLESS_URL=https://your-runpod-endpoint.runpod.io
```

## Step 3: Get RunPod Credentials

After creating the endpoint, retrieve:
- **Endpoint ID**: From RunPod console (e.g., `ep-xxxxx`)
- **API Key**: From RunPod API keys

Configure your backend API with:
```bash
RUNPOD_ENDPOINT_ID=ep-xxxxx
RUNPOD_API_KEY=your_api_key
```

## Step 4: Deploy Backend API

Deploy the FastAPI backend to your preferred host (Netlify, Render, Railway, etc.):

```bash
# Example: Using Render.com
# 1. Connect GitHub repository
# 2. Create new Web Service
# 3. Configure:
#    - Build command: pip install -r requirements.txt
#    - Start command: uvicorn agent_service.api:app --host 0.0.0.0 --port $PORT
#    - Environment variables: See section below
```

### Backend Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/ivrimeet_db

# RunPod Configuration
USE_RUNPOD=true
RUNPOD_ENDPOINT_ID=ep-xxxxx
RUNPOD_API_KEY=your_api_key

# AWS S3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET=your-bucket-name
S3_REGION=us-east-1

# Ivrit ASR
IVRIT_API_KEY=your_ivrit_key
IVRIT_API_URL=https://api.ivrit.ai

# LLM
LLM_API_KEY=your_deepseek_key
LLM_MODEL=deepseek-ai/deepseek-v3.1-terminus

# JWT/Security
JWT_SECRET_KEY=your_secure_random_key_min_32_chars

# CORS
CORS_ORIGINS=https://ivreetmeet.netlify.app,https://your-frontend.com

# Gmail OAuth
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_secret
GMAIL_REDIRECT_URI=https://your-api.example.com/auth/gmail/callback
GMAIL_CREDENTIALS_PATH=credentials.json

# Optional
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## Step 5: Test RunPod Deployment

### Test Locally

```bash
# Set environment variables
export RUNPOD_ENDPOINT_ID=ep-xxxxx
export RUNPOD_API_KEY=your_api_key
export DATABASE_URL=postgresql://localhost/test_db
export USE_RUNPOD=true

# Run backend locally
cd ASR_SALES_CALLS_AGENT
uvicorn agent_service.api:app --reload

# Test upload endpoint
curl -X POST http://localhost:8000/meetings/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_audio.mp3" \
  -F "title=Test Meeting"
```

### Test RunPod Endpoint Directly

```bash
# Test handler via RunPod API
curl -X POST https://api.runpod.io/v2/{ENDPOINT_ID}/run \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
      "organization_id": "550e8400-e29b-41d4-a716-446655440001",
      "audio_s3_key": "meetings/550e8400-e29b-41d4-a716-446655440001/test_audio.mp3"
    }
  }'

# Check job status
curl -X GET https://api.runpod.io/v2/{ENDPOINT_ID}/status/{JOB_ID} \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}"
```

## Step 6: Monitor RunPod Endpoint

### Check Endpoint Status
- Go to RunPod Console > Endpoints
- Monitor: Pod status, requests, errors, pricing
- Review logs in pod details

### Common Issues

#### Cold Start Times
- First request may take 30-60 seconds
- Subsequent requests typically 5-10 seconds
- Consider keeping endpoint warm with periodic requests

#### GPU Memory Issues
- Use `Dockerfile` without GPU for CPU-only (recommended for cost)
- Or allocate GPU if needed for faster processing

#### Database Connection Timeouts
- Ensure DATABASE_URL is accessible from RunPod
- Configure security groups/firewall to allow RunPod IPs
- Use connection pooling in production

#### S3 Access Issues
- Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
- Check S3 bucket permissions
- Ensure bucket and endpoint are in compatible regions

## Step 7: Deploy Frontend

Deploy React/Vite frontend to Netlify:

```bash
cd IvriMeet

# Build
npm run build

# Deploy to Netlify
netlify deploy --prod --dir=dist
```

Configure frontend environment variables in Netlify:
```bash
VITE_API_URL=https://your-api.example.com
VITE_ENABLE_GMAIL=true
```

## Scaling & Cost Optimization

### RunPod Endpoints Configuration

For optimal cost/performance:

```
Development/Testing:
- CPU: 2-4 vCPU
- Memory: 8-16GB
- Disk: 30GB Container + 50GB Volume
- GPU: None (CPU-only)
- $0.01-0.05/hour idle

Production:
- CPU: 4-8 vCPU
- Memory: 16-32GB
- Disk: 50GB Container + 100GB Volume
- GPU: Optional (RTX 4090 if needed for heavy processing)
- $0.05-0.20/hour depends on GPU
```

### Cost Reduction Tips

1. **Use CPU endpoints**: No GPU needed for ASR/summarization
2. **Batch processing**: Queue meetings during off-peak hours
3. **Model caching**: Store models in S3, cache locally in volume
4. **Endpoint scaling**: Use "Min Instances" to control idle costs
5. **Request optimization**: Compress audio before S3 upload

## Troubleshooting

### Meetings Stay in "pending" Status

```bash
# Check RunPod job status
curl -X GET https://api.runpod.io/v2/{ENDPOINT_ID}/status/{JOB_ID} \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}"

# Check backend logs
tail -f backend_logs.txt | grep "{MEETING_ID}"

# Manual retry
curl -X POST {BACKEND_URL}/meetings/{MEETING_ID}/retry \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Handler Crashes

1. Check endpoint logs in RunPod console
2. Review error messages in database
3. Test with small audio file (5-10 seconds)
4. Verify all environment variables are set

### Database Connection Issues

```bash
# Test database connectivity from backend
psql $DATABASE_URL -c "SELECT version();"

# Migrate database schema
python -m alembic upgrade head

# Check migrations status
python -m alembic current
```

## Monitoring Checklist

- [ ] RunPod endpoint status: GREEN
- [ ] Database connectivity: OK
- [ ] S3 bucket access: OK
- [ ] Backend API health: /healthz returns 200
- [ ] Sample meeting upload: Completes successfully
- [ ] Meeting processing: Completes within 5 minutes
- [ ] Frontend loads: No CORS errors
- [ ] Gmail OAuth: Redirects correctly

## Production Deployment Checklist

- [ ] All environment variables set
- [ ] Database backups configured
- [ ] S3 bucket versioning enabled
- [ ] CloudFront/CDN for static assets
- [ ] SSL/TLS certificates valid
- [ ] CORS origins whitelist updated
- [ ] Rate limiting configured
- [ ] Error monitoring (Sentry) configured
- [ ] Database auto-scaling enabled
- [ ] RunPod endpoint monitoring enabled
- [ ] Backup/disaster recovery plan

## Next Steps

1. Deploy to RunPod
2. Test end-to-end workflow
3. Monitor performance and costs
4. Scale based on requirements
5. Set up CI/CD pipeline for automatic deployments

## Support & Resources

- [RunPod Documentation](https://docs.runpod.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)

## Cost Estimates (Monthly)

Typical production costs:

```
RunPod Endpoint (CPU):        $50-100   (4vCPU, 16GB RAM)
PostgreSQL Database:          $20-50    (managed RDS)
S3 Storage:                   $10-50    (depends on volume)
Bandwidth:                    $5-20     (data transfer)
LLM API (DeepSeek):          $20-100   (depends on request volume)
Ivrit ASR API:               $30-100   (depends on call duration)
────────────────────────────────────
Total Estimate:              $135-420/month

Cost Optimization Possible: $80-150/month with careful tuning
```

