from __future__ import annotations

import logging
import uuid
from typing import Any

from celery import Celery
from sqlalchemy.orm import Session

import asyncio

from agent_service.database.connection import get_db_session
from agent_service.services.orchestrator import ProcessingOrchestrator

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
	"hebrew_meetings",
	broker="redis://localhost:6379/0",
	backend="redis://localhost:6379/0",
)

celery_app.conf.update(
	task_serializer="json",
	accept_content=["json"],
	result_serializer="json",
	timezone="UTC",
	enable_utc=True,
)


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

