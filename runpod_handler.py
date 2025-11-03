"""
RunPod Serverless handler for meeting processing.
This replaces the Celery worker - RunPod calls this function directly.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

import runpod  # pip install runpod

from agent_service.database.connection import get_db_session
from agent_service.services.orchestrator import ProcessingOrchestrator
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
            error_msg = "Missing required fields: meeting_id, organization_id"
            logger.error(error_msg)
            return {
                "error": error_msg
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
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})

