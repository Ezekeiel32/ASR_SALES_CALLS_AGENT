# RunPod Serverless Hybrid Setup 🚀

## 🎯 Architecture

**API Service: Render (Free)**
- Handles all HTTP requests
- Fast, always-on, free
- Enqueues tasks to RunPod Serverless

**Worker: RunPod Serverless Endpoint**
- Processes meetings with GPU
- Auto-scales to 0 when idle
- Pay-per-second billing
- **Even cheaper than regular pods!**

## 💰 Cost Comparison

**RunPod Serverless Pricing:**
- RTX 4000: **$0.000166/sec** ($0.60/hr equivalent)
- But you only pay for **execution time**, not idle time!
- **30min meeting processing**: ~30 seconds GPU time = **$0.005** (half a cent!)
- **100 meetings/month**: ~$0.50 total! 🎉

**vs Regular Pods:**
- Pod: $0.29/hr minimum (even if idle)
- Serverless: Only pay when processing
- **90%+ savings for low/medium usage!**

## 🏗️ How It Works

1. **User uploads meeting** → API receives request
2. **API saves to S3** → Enqueues to RunPod Serverless
3. **RunPod scales up** → GPU processes meeting
4. **Result returns** → API updates database
5. **RunPod scales down** → Back to $0

## 🚀 Setup Steps

### Step 1: Set Up API on Render (Free)

1. Go to https://render.com
2. **New** → **Web Service**
3. Connect GitHub repo
4. Settings:
   - **Name**: `ivrimeet-api`
   - **Environment**: `Docker`
   - **Root Directory**: `/`
   - **Dockerfile**: `Dockerfile`
5. **Environment Variables**:
   ```bash
   DATABASE_URL=your_supabase_postgres_url
   REDIS_URL=your_upstash_redis_url
   CORS_ORIGINS=https://ivreetmeet.netlify.app
   IVRIT_API_KEY=your_key
   NVIDIA_API_KEY=your_key
   PYANNOTE_AUTH_TOKEN=your_hf_token
   JWT_SECRET_KEY=your_jwt_secret
   RUNPOD_API_KEY=your_runpod_key  # Get from RunPod dashboard
   RUNPOD_ENDPOINT_ID=your_endpoint_id  # After creating endpoint
   PORT=8000
   PYTHONUNBUFFERED=1
   ```
6. **Deploy** → Wait for build

**Your API URL**: `https://ivrimeet-api.onrender.com`

### Step 2: Create RunPod Serverless Handler

Create a handler function that RunPod will call:

```python
# runpod_handler.py
"""
RunPod Serverless handler for meeting processing.
This replaces the Celery worker - RunPod calls this function directly.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any

import runpod  # pip install runpod

from agent_service.database.connection import get_db_session
from agent_service.services.orchestrator import ProcessingOrchestrator
import asyncio

logger = logging.getLogger(__name__)

def handler(event: dict[str, Any]) -> dict[str, Any]:
    """
    RunPod serverless handler for processing meetings.
    
    Expected input:
    {
        "input": {
            "meeting_id": "uuid-string",
            "organization_id": "uuid-string",
            "audio_s3_key": "s3://bucket/key.mp3"  # optional
        }
    }
    
    Returns:
    {
        "status": "success" | "error",
        "result": {...}  # Processing results
    }
    """
    try:
        input_data = event.get("input", {})
        
        meeting_id_str = input_data.get("meeting_id")
        organization_id_str = input_data.get("organization_id")
        audio_s3_key = input_data.get("audio_s3_key")
        
        if not meeting_id_str or not organization_id_str:
            return {
                "error": "Missing required fields: meeting_id, organization_id"
            }
        
        meeting_id = uuid.UUID(meeting_id_str)
        organization_id = uuid.UUID(organization_id_str)
        
        logger.info(f"Processing meeting {meeting_id} via RunPod Serverless")
        
        # Process meeting
        with get_db_session() as db:
            orchestrator = ProcessingOrchestrator(db)
            result = asyncio.run(
                orchestrator.process_meeting(
                    meeting_id=meeting_id,
                    organization_id=organization_id,
                    audio_s3_key=audio_s3_key,
                )
            )
        
        logger.info(f"Successfully processed meeting {meeting_id}")
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error processing meeting: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }

# Register handler with RunPod
runpod.serverless.start({"handler": handler})
```

### Step 3: Create RunPod Serverless Endpoint

#### 3.1 Build and Push Docker Image

**Option A: Use Docker Hub**

```bash
# Create Dockerfile for RunPod handler
# Dockerfile.runpod_serverless
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cu121 && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir runpod

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run handler
CMD ["python", "runpod_handler.py"]
```

```bash
# Build and push
cd /home/chezy/ASR/ASR_SALES_CALLS_AGENT
docker build -f Dockerfile.runpod_serverless -t yourusername/ivrimeet-runpod:latest .
docker push yourusername/ivrimeet-runpod:latest
```

**Option B: Build on RunPod**

RunPod can build from GitHub repo directly!

#### 3.2 Create Serverless Endpoint

1. Go to RunPod Dashboard → **Serverless** → **Endpoints**
2. Click **Create Endpoint**
3. **Configuration**:
   - **Name**: `ivrimeet-worker`
   - **Container Image**: `yourusername/ivrimeet-runpod:latest`
   - Or: **Build from GitHub** → Select your repo
4. **GPU Type**: RTX 4000 Ada (or RTX 3090 for cheaper)
5. **Handler Path**: `/app/runpod_handler.py` (or `python runpod_handler.py`)
6. **Environment Variables**:
   ```bash
   DATABASE_URL=your_supabase_postgres_url
   IVRIT_API_KEY=your_key
   NVIDIA_API_KEY=your_key
   PYANNOTE_AUTH_TOKEN=your_hf_token
   S3_BUCKET=your_bucket
   S3_REGION=us-east-1
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   PYTHONUNBUFFERED=1
   PYTHONPATH=/app
   ```
7. **Scaling**:
   - **Min Workers**: 0 (scale to 0 when idle)
   - **Max Workers**: 3 (scale up for concurrent requests)
   - **Idle Timeout**: 60 seconds (scale down after 1 min idle)
8. **Click Create Endpoint**

**Copy the Endpoint ID** - you'll need this for the API!

### Step 4: Update API to Use RunPod Serverless

Modify the API to call RunPod instead of Celery:

```python
# agent_service/services/runpod_client.py
"""
Client for calling RunPod Serverless endpoints.
Replaces Celery for task queuing.
"""

from __future__ import annotations

import logging
import os
from typing import Any
import uuid
import httpx

logger = logging.getLogger(__name__)

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")
RUNPOD_API_URL = "https://api.runpod.io/v2"


def enqueue_meeting_processing(
    meeting_id: uuid.UUID,
    organization_id: uuid.UUID,
    audio_s3_key: str | None = None,
) -> str:
    """
    Enqueue a meeting for processing via RunPod Serverless.
    
    Args:
        meeting_id: Meeting UUID
        organization_id: Organization UUID
        audio_s3_key: Optional S3 key for audio file
    
    Returns:
        Job ID from RunPod
    """
    if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
        raise ValueError("RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID must be set")
    
    # Prepare job input
    job_input = {
        "meeting_id": str(meeting_id),
        "organization_id": str(organization_id),
    }
    
    if audio_s3_key:
        job_input["audio_s3_key"] = audio_s3_key
    
    # Call RunPod API
    url = f"{RUNPOD_API_URL}/{RUNPOD_ENDPOINT_ID}/run"
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json",
    }
    
    try:
        response = httpx.post(url, json={"input": job_input}, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        job_id = result.get("id")
        if not job_id:
            raise ValueError(f"RunPod API did not return job ID: {result}")
        
        logger.info(f"Enqueued meeting {meeting_id} to RunPod serverless: {job_id}")
        return job_id
        
    except Exception as e:
        logger.error(f"Failed to enqueue meeting to RunPod: {e}")
        raise


def get_processing_status(job_id: str) -> dict[str, Any]:
    """
    Get the status of a RunPod job.
    
    Returns:
        {
            "status": "IN_QUEUE" | "IN_PROGRESS" | "COMPLETED" | "FAILED",
            "result": {...}  # Only if completed
        }
    """
    if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
        raise ValueError("RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID must be set")
    
    url = f"{RUNPOD_API_URL}/{RUNPOD_ENDPOINT_ID}/status/{job_id}"
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
    }
    
    try:
        response = httpx.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to get RunPod job status: {e}")
        raise
```

### Step 5: Update API Endpoints

Modify `agent_service/api.py` to use RunPod instead of Celery:

```python
# In agent_service/api.py

# Replace Celery import:
# from agent_service.services.processing_queue import enqueue_meeting_processing

# With RunPod client:
from agent_service.services.runpod_client import enqueue_meeting_processing, get_processing_status

# The rest of the code stays the same!
# enqueue_meeting_processing() has the same signature
```

### Step 6: Add RunPod Handler File

Create `runpod_handler.py` in the repo root:

```python
# See Step 2 above for full handler code
```

### Step 7: Add RunPod to Requirements

```bash
# Add to requirements.txt
runpod>=1.0.0
```

### Step 8: Update Frontend

No changes needed! The API still works the same way.

## 📋 Complete Checklist

- [ ] Create Render API service (free)
- [ ] Get RunPod API key (Dashboard → Settings → API Keys)
- [ ] Create `runpod_handler.py`
- [ ] Create `agent_service/services/runpod_client.py`
- [ ] Create `Dockerfile.runpod_serverless`
- [ ] Build and push Docker image (or use GitHub build)
- [ ] Create RunPod Serverless endpoint
- [ ] Add `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` to Render env vars
- [ ] Update API to use RunPod client (replace Celery)
- [ ] Test: Upload meeting → Verify RunPod processes it
- [ ] Update frontend API URL to Render URL

## 💡 Advantages of Serverless

✅ **True Pay-Per-Use**
- Only pay when processing
- No idle costs
- 90%+ savings for low usage

✅ **Auto-Scaling**
- Scales to 0 automatically
- Scales up instantly when needed
- No manual configuration

✅ **Simpler Architecture**
- No Redis queue needed (optional)
- Direct API calls
- Easier debugging

✅ **Faster Cold Starts**
- RunPod optimizes container startup
- Models pre-loaded in warm containers

## 🆚 Serverless vs Pods

| Feature | Serverless | Pods |
|---------|-----------|------|
| **Billing** | Per-second | Per-hour |
| **Idle Cost** | $0 | $0.29/hr |
| **Scaling** | Automatic | Manual/Auto |
| **Setup** | Simpler | More complex |
| **Best For** | Variable workload | Constant workload |

## 💰 Cost Example

**Processing 50 meetings/month:**
- Each meeting: ~30 seconds GPU time
- Total: 50 × 30s = 25 minutes = 1500 seconds
- Cost: 1500 × $0.000166 = **$0.25/month** 🎉

**vs Pod ($0.29/hr):**
- Need pod running: ~50 hours (to be available)
- Cost: 50 × $0.29 = **$14.50/month**

**Serverless saves: $14.25/month (98% savings!)** 💰

## 🚨 Important Notes

### Error Handling

RunPod Serverless returns errors in the response:
```python
{
    "status": "error",
    "error": "Error message here"
}
```

Update your API to handle these and update meeting status accordingly.

### Timeouts

RunPod Serverless has default timeout of 5 minutes. For longer meetings, increase timeout in endpoint settings.

### Monitoring

Check RunPod Dashboard → Serverless → Endpoints → Your Endpoint:
- Request count
- Average execution time
- Cost per request
- Error rate

## 🎉 Result

You now have:
- ✅ **Free API** (Render)
- ✅ **Cheap GPU processing** (RunPod Serverless)
- ✅ **Auto-scaling to 0**
- ✅ **Simple architecture**
- ✅ **~$0.25-1/month** for processing! 🚀

This is the cheapest and simplest setup possible!

