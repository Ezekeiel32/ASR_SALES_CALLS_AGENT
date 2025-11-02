#!/usr/bin/env python3
"""Test all imports to ensure no circular dependencies or missing modules."""
from __future__ import annotations

import sys

def test_imports():
	"""Test critical imports."""
	errors = []
	
	try:
		from agent_service.config import get_settings
		print("✓ config")
	except Exception as e:
		errors.append(f"config: {e}")
	
	try:
		from agent_service.database import get_db
		from agent_service.database.models import Meeting, Speaker, Organization
		print("✓ database")
	except Exception as e:
		errors.append(f"database: {e}")
	
	try:
		from agent_service.clients.ivrit_client import IvritClient
		print("✓ ivrit_client")
	except Exception as e:
		errors.append(f"ivrit_client: {e}")
	
	try:
		from agent_service.services.orchestrator import ProcessingOrchestrator
		print("✓ orchestrator")
	except Exception as e:
		errors.append(f"orchestrator: {e}")
	
	try:
		from agent_service.services.processing_queue import enqueue_meeting_processing
		print("✓ processing_queue")
	except Exception as e:
		errors.append(f"processing_queue: {e}")
	
	try:
		from agent_service.services.voiceprint_service import VoiceprintService
		print("✓ voiceprint_service")
	except Exception as e:
		errors.append(f"voiceprint_service: {e}")
	
	try:
		from agent_service.services.speaker_service import SpeakerService
		print("✓ speaker_service")
	except Exception as e:
		errors.append(f"speaker_service: {e}")
	
	try:
		from agent_service.summarizers.nvidia import NvidiaDeepSeekSummarizer
		print("✓ nvidia summarizer")
	except Exception as e:
		errors.append(f"nvidia summarizer: {e}")
	
	try:
		from agent_service.api import app
		print("✓ api")
	except Exception as e:
		errors.append(f"api: {e}")
	
	if errors:
		print("\n❌ Errors found:")
		for error in errors:
			print(f"  - {error}")
		return 1
	
	print("\n✅ All imports successful!")
	return 0


if __name__ == "__main__":
	sys.exit(test_imports())

