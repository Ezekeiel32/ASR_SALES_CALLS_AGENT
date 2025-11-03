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
    
    Raises:
        ValueError: If RunPod credentials are not set
        httpx.HTTPError: If API call fails
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
        
    except httpx.HTTPStatusError as e:
        logger.error(f"RunPod API error {e.response.status_code}: {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Failed to enqueue meeting to RunPod: {e}")
        raise


def get_processing_status(job_id: str) -> dict[str, Any]:
    """
    Get the status of a RunPod job.
    
    Args:
        job_id: RunPod job ID
    
    Returns:
        {
            "status": "IN_QUEUE" | "IN_PROGRESS" | "COMPLETED" | "FAILED",
            "result": {...}  # Only if completed
        }
    
    Raises:
        ValueError: If RunPod credentials are not set
        httpx.HTTPError: If API call fails
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
    except httpx.HTTPStatusError as e:
        logger.error(f"RunPod API error {e.response.status_code}: {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Failed to get RunPod job status: {e}")
        raise

