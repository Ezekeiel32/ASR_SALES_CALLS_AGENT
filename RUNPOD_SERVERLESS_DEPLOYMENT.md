# RunPod Serverless Deployment Guide - Consolidated Backend

This guide explains how to deploy the consolidated IvriMeet backend as a RunPod Serverless HTTP endpoint.

## Overview

The backend has been consolidated into a single FastAPI application (`runpod_handler.py`) that runs as an HTTP server on RunPod Serverless. This eliminates the need for separate API servers and worker processes.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Netlify Frontend                          │
│               (https://ivreetmeet.netlify.app)              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ HTTP/HTTPS
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              RunPod Serverless Endpoint                      │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         FastAPI Application                         │    │
│  │         (runpod_handler.py)                        │    │
│  │                                                     │    │
│  │  • Authentication Endpoints                        │    │
│  │  • Meeting Upload & Processing                     │    │
│  │  • Transcription & Diarization                     │    │
│  │  • Speaker Recognition                             │    │
│  │  • Summarization                                   │    │
│  │  • Database Operations                             │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              Neon PostgreSQL Database                        │
│           (with pgvector extension)                          │
└──────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **RunPod Account**: Sign up at [runpod.io](https://www.runpod.io/)
2. **Docker**: Installed locally for building images
3. **Environment Variables**: Prepared for deployment
4. **Neon Database**: PostgreSQL database with pgvector extension

## Step 1: Prepare Environment Variables

Create a `.env` file with all required configuration:

```bash
# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname?sslmode=require

# API Keys
IVRIT_API_KEY=your_ivrit_api_key
NVIDIA_API_KEY=your_nvidia_api_key
PYANNOTE_AUTH_TOKEN=your_huggingface_token

# AWS S3 (for audio storage)
S3_BUCKET=your-bucket-name
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# JWT Authentication
JWT_SECRET_KEY=your_random_secret_key_at_least_32_chars

# CORS Origins (frontend URL)
CORS_ORIGINS=https://ivreetmeet.netlify.app

# Optional: Gmail OAuth (for email analysis features)
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
```

## Step 2: Build and Push Docker Image

### Build the Docker Image

```bash
cd ASR_SALES_CALLS_AGENT

# Build for RunPod Serverless (HTTP mode)
docker build -f Dockerfile.runpod_serverless -t ivrimeet-backend:latest .
```

### Tag and Push to Docker Registry

You need to push the image to a public registry (Docker Hub, GitHub Container Registry, etc.):

#### Option A: Docker Hub

```bash
# Login to Docker Hub
docker login

# Tag the image
docker tag ivrimeet-backend:latest yourusername/ivrimeet-backend:latest

# Push to Docker Hub
docker push yourusername/ivrimeet-backend:latest
```

#### Option B: GitHub Container Registry

```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Tag the image
docker tag ivrimeet-backend:latest ghcr.io/yourusername/ivrimeet-backend:latest

# Push to registry
docker push ghcr.io/yourusername/ivrimeet-backend:latest
```

## Step 3: Create RunPod Serverless Endpoint

### Via RunPod Web Console

1. Go to [RunPod Console](https://www.runpod.io/console/serverless)
2. Click **"New Endpoint"**
3. Configure the endpoint:

   **Basic Settings:**
   - **Name**: `ivrimeet-backend`
   - **Container Image**: `yourusername/ivrimeet-backend:latest`
   - **Container Start Command**: Leave empty (uses Dockerfile CMD)

   **GPU Settings:**
   - **GPU Type**: Select based on your needs (e.g., `NVIDIA A40`, `RTX 4090`)
   - **Worker Count**: 
     - Min Workers: `1` (keeps 1 instance always running)
     - Max Workers: `5` (scales up to 5 instances)
   - **Idle Timeout**: `300` seconds (5 minutes)

   **Environment Variables:**
   Add all variables from your `.env` file:
   ```
   DATABASE_URL=postgresql://...
   IVRIT_API_KEY=...
   NVIDIA_API_KEY=...
   PYANNOTE_AUTH_TOKEN=...
   S3_BUCKET=...
   S3_REGION=...
   AWS_ACCESS_KEY_ID=...
   AWS_SECRET_ACCESS_KEY=...
   JWT_SECRET_KEY=...
   CORS_ORIGINS=https://ivreetmeet.netlify.app
   ```

   **Advanced Settings:**
   - **Max Concurrency**: `10` (requests per worker)
   - **Request Timeout**: `900` seconds (15 minutes for long audio files)
   - **Port**: `8000` (must match Dockerfile EXPOSE)

4. Click **"Deploy"**

### Via RunPod API (Alternative)

```bash
curl -X POST https://api.runpod.ai/v2/endpoints \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ivrimeet-backend",
    "image": "yourusername/ivrimeet-backend:latest",
    "gpuTypeId": "AMPERE_16",
    "workerCount": {
      "min": 1,
      "max": 5
    },
    "idleTimeout": 300,
    "env": {
      "DATABASE_URL": "postgresql://...",
      "IVRIT_API_KEY": "...",
      "NVIDIA_API_KEY": "...",
      "PYANNOTE_AUTH_TOKEN": "...",
      "S3_BUCKET": "...",
      "S3_REGION": "...",
      "AWS_ACCESS_KEY_ID": "...",
      "AWS_SECRET_ACCESS_KEY": "...",
      "JWT_SECRET_KEY": "...",
      "CORS_ORIGINS": "https://ivreetmeet.netlify.app"
    },
    "maxConcurrency": 10,
    "requestTimeout": 900,
    "port": 8000
  }'
```

## Step 4: Get Your Endpoint URL

After deployment, RunPod will provide an endpoint URL:

```
https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync
```

However, for HTTP server mode, you'll use the direct endpoint URL:

```
https://{ENDPOINT_ID}-8000.proxy.runpod.net
```

You can find this in the RunPod console under your endpoint details.

## Step 5: Update Frontend Configuration

Update your Netlify frontend environment variables:

1. Go to Netlify Dashboard → Your Site → Site Settings → Environment Variables
2. Update `VITE_API_URL` or `REACT_APP_API_URL`:
   ```
   VITE_API_URL=https://{ENDPOINT_ID}-8000.proxy.runpod.net
   ```

3. Redeploy your Netlify site to apply changes

## Step 6: Run Database Migrations

Before the backend can serve requests, initialize the database:

```bash
# SSH into a RunPod instance or run locally with DATABASE_URL
export DATABASE_URL="postgresql://user:password@host.neon.tech/dbname?sslmode=require"

# Run migrations
cd ASR_SALES_CALLS_AGENT
alembic upgrade head
```

Or you can run migrations through a one-time job on RunPod:

```bash
# Create a temporary container
docker run --rm \
  -e DATABASE_URL="postgresql://..." \
  yourusername/ivrimeet-backend:latest \
  alembic upgrade head
```

## Step 7: Test the Deployment

### Health Check

```bash
curl https://{ENDPOINT_ID}-8000.proxy.runpod.net/healthz
```

Expected response:
```json
{
  "status": "ok",
  "service": "runpod-serverless"
}
```

### Register a Test User

```bash
curl -X POST https://{ENDPOINT_ID}-8000.proxy.runpod.net/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123",
    "name": "Test User",
    "organization_name": "Test Org"
  }'
```

### Upload a Meeting

```bash
# Login first to get token
TOKEN=$(curl -X POST https://{ENDPOINT_ID}-8000.proxy.runpod.net/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"securepassword123"}' \
  | jq -r '.access_token')

# Upload audio file
curl -X POST https://{ENDPOINT_ID}-8000.proxy.runpod.net/meetings/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/audio.mp3" \
  -F "title=Test Meeting"
```

## Monitoring and Logs

### View Logs in RunPod Console

1. Go to RunPod Console → Serverless → Your Endpoint
2. Click on **"Logs"** tab
3. Monitor real-time logs and errors

### Custom Logging

The application uses Python's logging module. Logs are sent to stdout/stderr and captured by RunPod.

## Scaling Configuration

### Auto-scaling

RunPod automatically scales workers based on:
- **Request Volume**: More requests = more workers
- **Worker Load**: Each worker handles up to `maxConcurrency` concurrent requests
- **Idle Timeout**: Workers shut down after `idleTimeout` seconds of inactivity

### Recommended Settings by Usage

**Low Traffic (< 100 requests/day):**
```
Min Workers: 0
Max Workers: 2
Idle Timeout: 300s
Max Concurrency: 5
```

**Medium Traffic (100-1000 requests/day):**
```
Min Workers: 1
Max Workers: 5
Idle Timeout: 600s
Max Concurrency: 10
```

**High Traffic (> 1000 requests/day):**
```
Min Workers: 2
Max Workers: 10
Idle Timeout: 900s
Max Concurrency: 15
```

## Cost Optimization

### Tips to Reduce Costs

1. **Use Spot Instances**: Enable spot instances for up to 50% savings
2. **Optimize Idle Timeout**: Balance between cold starts and cost
3. **Set Appropriate Min Workers**: 
   - `0` = lowest cost but cold starts
   - `1+` = faster response but constant cost
4. **Right-size GPU**: Choose the smallest GPU that meets your needs
5. **Monitor Utilization**: Check logs for actual usage patterns

### Estimated Costs (RunPod A40 GPU)

- **On-Demand**: ~$0.79/hour per worker
- **Spot**: ~$0.40/hour per worker
- **Idle Time**: Still charged (use timeout to minimize)

Example monthly cost with 1 min worker running 24/7:
- On-Demand: $0.79 × 24 × 30 = $569/month
- Spot: $0.40 × 24 × 30 = $288/month

## Troubleshooting

### Container Fails to Start

**Check logs for:**
- Missing environment variables
- Database connection errors
- Missing dependencies

**Solution:**
1. Verify all environment variables are set
2. Test DATABASE_URL locally
3. Ensure Docker image built successfully

### Database Connection Errors

**Error:** `could not connect to server`

**Solution:**
1. Check DATABASE_URL format
2. Verify Neon database is accessible
3. Ensure pgvector extension is enabled:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

### CORS Errors

**Error:** `Access-Control-Allow-Origin`

**Solution:**
1. Verify `CORS_ORIGINS` includes your frontend URL
2. Check frontend is using correct API URL
3. Ensure protocol matches (https/http)

### Timeout on Large Files

**Error:** Request timeout after 900s

**Solution:**
1. Increase `Request Timeout` in RunPod settings
2. Optimize audio processing pipeline
3. Use S3 pre-signed URLs for very large files

### Cold Start Latency

**Issue:** First request takes 30+ seconds

**Solution:**
- Set `Min Workers` to 1 or more
- Accept cold start cost for low-traffic applications
- Use health check pings to keep instances warm

## Updating the Deployment

### Update Process

1. **Build new image:**
   ```bash
   docker build -f Dockerfile.runpod_serverless -t ivrimeet-backend:v2 .
   docker tag ivrimeet-backend:v2 yourusername/ivrimeet-backend:v2
   docker push yourusername/ivrimeet-backend:v2
   ```

2. **Update endpoint:**
   - Go to RunPod Console
   - Edit endpoint settings
   - Change container image to new version
   - Click **"Update"**

3. **Zero-downtime deployment:**
   - RunPod gradually shifts traffic to new version
   - Old workers complete current requests
   - New workers start handling new requests

### Rolling Back

If issues occur:
1. Edit endpoint settings
2. Change image back to previous version
3. Click **"Update"**

## Security Best Practices

1. **Environment Variables**: Never commit `.env` files
2. **JWT Secret**: Use strong random keys (32+ characters)
3. **Database**: Use SSL/TLS connections (included in Neon)
4. **API Keys**: Rotate regularly
5. **CORS**: Only allow trusted frontend domains
6. **Rate Limiting**: Consider adding rate limiting middleware

## Support and Resources

- **RunPod Documentation**: https://docs.runpod.io/
- **RunPod Discord**: https://discord.gg/runpod
- **GitHub Issues**: Report bugs and feature requests
- **Backend API Documentation**: `https://{ENDPOINT_ID}-8000.proxy.runpod.net/docs` (FastAPI auto-docs)

## Next Steps

1. ✅ Deploy to RunPod Serverless
2. ✅ Update Netlify frontend configuration
3. ✅ Test all endpoints
4. 📊 Monitor logs and performance
5. 🎯 Optimize based on usage patterns
6. 🔒 Enable additional security features

---

**Deployment Status**: Ready for production use with consolidated backend architecture.