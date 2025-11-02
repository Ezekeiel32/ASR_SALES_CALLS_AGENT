from __future__ import annotations

import logging
import os
import uuid
from typing import Any
from urllib.parse import urlparse

from celery import Celery
from sqlalchemy.orm import Session

import asyncio
import ssl

from agent_service.config import get_settings
from agent_service.database.connection import get_db_session
from agent_service.services.orchestrator import ProcessingOrchestrator

logger = logging.getLogger(__name__)
settings = get_settings()

# Get Redis URL from environment (Railway/Koyeb provides REDIS_URL automatically)
redis_url = settings.redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Parse Redis URL to determine if SSL is needed
redis_parsed = urlparse(redis_url)
is_ssl = redis_parsed.scheme == "rediss" or redis_url.startswith("rediss://")

# For secure Redis (rediss://), we need to configure SSL properly
# Upstash and other Redis services use TLS but don't require client certificates
if is_ssl:
	logger.info("Detected secure Redis connection (rediss://), configuring SSL...")
	# Ensure URL has ssl_cert_reqs parameter (required by Celery)
	if "ssl_cert_reqs" not in redis_url:
		separator = "&" if "?" in redis_url else "?"
		redis_url = f"{redis_url}{separator}ssl_cert_reqs=CERT_NONE"

# Initialize Celery app
celery_app = Celery(
	"hebrew_meetings",
	broker=redis_url,
	backend=redis_url,
)

# Configure Celery with SSL settings for Redis if needed
celery_conf = {
	"task_serializer": "json",
	"accept_content": ["json"],
	"result_serializer": "json",
	"timezone": "UTC",
	"enable_utc": True,
}

# Add Redis SSL configuration if using rediss://
# This is required for Upstash Redis and other TLS-enabled Redis services
if is_ssl:
	celery_conf.update({
		"broker_use_ssl": {
			"ssl_cert_reqs": ssl.CERT_NONE,  # CERT_NONE for Redis services without client certs
			"ssl_ca_certs": None,
			"ssl_certfile": None,
			"ssl_keyfile": None,
		},
		"redis_backend_use_ssl": {
			"ssl_cert_reqs": ssl.CERT_NONE,
			"ssl_ca_certs": None,
			"ssl_certfile": None,
			"ssl_keyfile": None,
		},
	})
	logger.info("Celery SSL configuration applied for Redis broker and backend")

celery_app.conf.update(celery_conf)


@celery_app.task(bind=True, max_retries=3)
def process_meeting_task(
	self,
	meeting_id: str,
	organization_id: str,
	audio_s3_key: str | None = None,
) -> dict[str, Any]:
	"""
	Celery task for processing a meeting asynchronously.

	Args:
		meeting_id: Meeting UUID as string
		organization_id: Organization UUID as string
		audio_s3_key: S3 key for audio file

	Returns:
		Processing results dictionary
	"""
	try:
		meeting_uuid = uuid.UUID(meeting_id)
		org_uuid = uuid.UUID(organization_id)

		with get_db_session() as db:
			orchestrator = ProcessingOrchestrator(db)
			# Run async process_meeting in sync context (Celery task)
			result = asyncio.run(
				orchestrator.process_meeting(
					meeting_id=meeting_uuid,
					organization_id=org_uuid,
					audio_s3_key=audio_s3_key,
				)
			)

		logger.info(f"Successfully processed meeting {meeting_id}")
		return result

	except Exception as e:
		logger.error(f"Error processing meeting {meeting_id}: {e}", exc_info=True)
		# Retry with exponential backoff
		raise self.retry(exc=e, countdown=60 * (2**self.request.retries))


def enqueue_meeting_processing(
	meeting_id: uuid.UUID,
	organization_id: uuid.UUID,
	audio_s3_key: str | None = None,
) -> str:
	"""
	Enqueue a meeting for async processing.

	Args:
		meeting_id: Meeting UUID
		organization_id: Organization UUID
		audio_s3_key: S3 key for audio file

	Returns:
		Task ID for tracking processing status
	"""
	task = process_meeting_task.delay(
		str(meeting_id),
		str(organization_id),
		audio_s3_key=audio_s3_key,
	)
	logger.info(f"Enqueued meeting {meeting_id} for processing (task: {task.id})")
	return task.id


def get_processing_status(task_id: str) -> dict[str, Any]:
	"""
	Get the status of a processing task.

	Args:
		task_id: Celery task ID

	Returns:
		Dictionary with task status and result
	"""
	task = celery_app.AsyncResult(task_id)
	return {
		"task_id": task_id,
		"status": task.state,
		"result": task.result if task.ready() else None,
		"error": str(task.info) if task.failed() else None,
	}

