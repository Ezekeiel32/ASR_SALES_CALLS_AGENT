web: uvicorn agent_service.api:app --host 0.0.0.0 --port $PORT
worker: celery -A agent_service.services.processing_queue.celery_app worker --loglevel=info

