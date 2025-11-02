from __future__ import annotations

from agent_service.services.audio_processor import AudioProcessor
from agent_service.services.diarization_merger import DiarizationMerger
# Lazy import for DiarizationService to avoid torchaudio compatibility issues
def _get_diarization_service():
	"""Lazy import to avoid startup errors if pyannote.audio has compatibility issues."""
	try:
		from agent_service.services.diarization_service import DiarizationService
		return DiarizationService
	except (AttributeError, ImportError, Exception) as e:
		import warnings
		warnings.warn(f"DiarizationService not available: {e}. Speaker diarization will be limited.")
		return None

DiarizationService = _get_diarization_service()
from agent_service.services.hebrew_nlp import HebrewNLP
from agent_service.services.name_extractor import NameExtractor
from agent_service.services.name_suggestion_service import NameSuggestionService
from agent_service.services.orchestrator import ProcessingOrchestrator
from agent_service.services.processing_queue import (
	celery_app,
	enqueue_meeting_processing,
	get_processing_status,
)
from agent_service.services.snippet_extractor import SnippetExtractor
from agent_service.services.speaker_service import SpeakerService
from agent_service.services.voiceprint_service import VoiceprintService

__all__ = [
	"AudioProcessor",
	"DiarizationMerger",
	"DiarizationService",
	"HebrewNLP",
	"NameExtractor",
	"NameSuggestionService",
	"ProcessingOrchestrator",
	"SnippetExtractor",
	"SpeakerService",
	"VoiceprintService",
	"celery_app",
	"enqueue_meeting_processing",
	"get_processing_status",
]

